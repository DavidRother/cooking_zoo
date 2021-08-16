# Other core modules
from gym_cooking.cooking_world.cooking_world import CookingWorld
from gym_cooking.cooking_world.world_objects import *
from gym_cooking.environment.game.game_image import GameImage
from gym_cooking.cooking_book.recipe_drawer import RECIPES, NUM_GOALS

import copy
import numpy as np
from pathlib import Path
import os.path
from itertools import combinations, product
from collections import namedtuple, defaultdict
from pettingzoo import AECEnv
from pettingzoo.utils import agent_selector
from pettingzoo.utils import wrappers
from pettingzoo.utils.conversions import parallel_wrapper_fn

import gym


CollisionRepr = namedtuple("CollisionRepr", "time agent_names agent_locations")
COLORS = ['blue', 'magenta', 'yellow', 'green']

SymbolToClass = {
    ' ': Floor,
    '-': Counter,
    '/': CutBoard,
    '*': DeliverSquare,
    't': Tomato,
    'l': Lettuce,
    'o': Onion,
    'p': Plate,
}

GAME_OBJECTS_STATEFUL = [('Counter', []), ('Floor', []), ('DeliverSquare', []), ('CutBoard', []),
                         ('Plate', []), ('Lettuce', [ChopFoodStates.FRESH, ChopFoodStates.CHOPPED]),
                         ('Tomato', [ChopFoodStates.FRESH, ChopFoodStates.CHOPPED]),
                         ('Onion', [ChopFoodStates.FRESH, ChopFoodStates.CHOPPED]), ('Agent', [])]

action_translation_dict = {0: (0, 0), 1: (1, 0), 2: (0, 1), 3: (-1, 0), 4: (0, -1)}
reverse_action_translation_dict = {(0, 0): 0, (1, 0): 1, (0, 1): 2, (-1, 0): 3, (0, -1): 4}


def env(level, num_agents, seed, record, max_num_timesteps, recipes):
    """
    The env function wraps the environment in 3 wrappers by default. These
    wrappers contain logic that is common to many pettingzoo environments.
    We recomend you use at least the OrderEnforcingWrapper on your own environment
    to provide sane error messages. You can find full documentation for these methods
    elsewhere in the developer documentation.
    """
    env_init = CookingEnvironment(level, num_agents, seed, record, max_num_timesteps, recipes)
    env_init = wrappers.CaptureStdoutWrapper(env_init)
    env_init = wrappers.AssertOutOfBoundsWrapper(env_init)
    env_init = wrappers.OrderEnforcingWrapper(env_init)
    return env_init


parallel_env = parallel_wrapper_fn(env)


class CookingEnvironment(AECEnv):
    """Environment object for Overcooked."""

    metadata = {'render.modes': ['human'], 'name': "cooking_zoo"}

    def __init__(self, level, num_agents, seed, record, max_num_timesteps, recipes):
        super().__init__()

        self.possible_agents = ["player_" + str(r) for r in range(num_agents)]
        self.agents = self.possible_agents[:]

        self.level = level
        self.seed = seed
        self.record = record
        self.max_num_timesteps = max_num_timesteps
        self.t = 0
        self.filename = ""
        self.set_filename()
        self.world = CookingWorld([], 0, 0)
        self.recipes = recipes
        self.game = None
        self.recipe_graphs = [RECIPES[recipe]() for recipe in recipes]

        self.termination_info = ""
        self.load_level(level=self.level, num_agents=num_agents)
        self.graph_representation_length = sum([max(len(tup[1]), 2) if tup[1] else 1 for tup in GAME_OBJECTS_STATEFUL])

        obs_space = {'symbolic_observation': gym.spaces.Box(low=0, high=10,
                                                            shape=(self.graph_representation_length, self.world.width,
                                                                   self.world.height), dtype=np.int32),
                     'agent_location': gym.spaces.Box(low=0, high=max(self.world.width, self.world.height),
                                                      shape=(2,)),
                     'goal_vector': gym.spaces.MultiBinary(NUM_GOALS)}
        self.observation_spaces = {agent: gym.spaces.Dict(obs_space) for agent in self.possible_agents}
        self.action_spaces = {agent: gym.spaces.Discrete(5) for agent in self.possible_agents}
        self.has_reset = True

        self.recipe_mapping = dict(zip(self.possible_agents, self.recipe_graphs))
        self.agent_name_mapping = dict(zip(self.possible_agents, list(range(len(self.possible_agents)))))
        self.world_agent_mapping = dict(zip(self.possible_agents, self.world.agents))
        self.world_agent_to_env_agent_mapping = dict(zip(self.world.agents, self.possible_agents))
        self.agent_selection = None
        self._agent_selector = agent_selector(self.agents)
        self.done = False
        self.rewards = dict(zip(self.agents, [0 for _ in self.agents]))
        self._cumulative_rewards = dict(zip(self.agents, [0 for _ in self.agents]))
        self.dones = dict(zip(self.agents, [False for _ in self.agents]))
        self.infos = dict(zip(self.agents, [{} for _ in self.agents]))
        self.accumulated_actions = []
        self.current_tensor_observation = np.zeros((self.world.width, self.world.height,
                                                    self.graph_representation_length))

    def set_filename(self):
        self.filename = f"{self.level}_agents{self.num_agents}_seed{self.seed}"

    def state(self):
        pass

    def load_level(self, level, num_agents):
        x = 0
        y = 0
        my_path = os.path.realpath(__file__)
        dir_name = os.path.dirname(my_path)
        path = Path(dir_name)
        parent = path.parent / f"utils/levels/{level}.txt"
        agents = []
        # print(parent)
        with parent.open("r") as file:
            # Mark the phases of reading.
            phase = 1
            for line in file:
                line = line.strip('\n')
                if line == '':
                    phase += 1

                # Phase 1: Read in kitchen map.
                elif phase == 1:
                    for x, rep in enumerate(line):
                        # Object, i.e. Tomato, Lettuce, Onion, or Plate.
                        if rep in 'tlop':
                            counter = Counter(location=(x, y))
                            dynamic_object = SymbolToClass[rep](location=(x, y))
                            self.world.add_object(counter)
                            self.world.add_object(dynamic_object)
                        # GridSquare, i.e. Floor, Counter, Cutboard, Delivery.
                        elif rep in SymbolToClass:
                            static_object = SymbolToClass[rep](location=(x, y))
                            self.world.add_object(static_object)
                        else:
                            # Empty. Set a Floor tile.
                            floor = Floor(location=(x, y))
                            self.world.add_object(floor)
                    y += 1
                # Phase 2: Read in recipe list.
                elif phase == 2:
                    # self.recipes.append(RecipeStore[line]())
                    pass

                # Phase 3: Read in agent locations (up to num_agents).
                elif phase == 3:
                    if len(agents) < num_agents:
                        loc = line.split(' ')
                        agent = Agent((int(loc[0]), int(loc[1])), COLORS[len(agents)],
                                      'agent-' + str(len(agents) + 1))
                        agents.append(agent)

        self.world.agents = agents
        self.world.width = x + 1
        self.world.height = y

    def reset(self):
        self.world = CookingWorld([], 0, 0)
        self.t = 0

        # For tracking data during an episode.
        self.termination_info = ""

        # Load world & distances.
        self.load_level(level=self.level, num_agents=self.num_agents)

        if self.record:
            self.game = GameImage(
                filename=self.filename,
                world=self.world,
                record=self.record)
            self.game.on_init()
            self.game.save_image_obs(self.t)
        else:
            self.game = None

        self._agent_selector.reinit(self.agents)
        self.agent_selection = self._agent_selector.next()

        # Get an image observation
        # image_obs = self.game.get_image_obs()
        self.recipe_mapping = dict(zip(self.possible_agents, self.recipe_graphs))
        self.agent_name_mapping = dict(zip(self.possible_agents, list(range(len(self.possible_agents)))))
        self.world_agent_mapping = dict(zip(self.possible_agents, self.world.agents))
        self.world_agent_to_env_agent_mapping = dict(zip(self.world.agents, self.possible_agents))

        self.current_tensor_observation = self.get_tensor_representation()
        self.rewards = dict(zip(self.agents, [0 for _ in self.agents]))
        self._cumulative_rewards = dict(zip(self.agents, [0 for _ in self.agents]))
        self.dones = dict(zip(self.agents, [False for _ in self.agents]))
        self.infos = dict(zip(self.agents, [{} for _ in self.agents]))
        self.accumulated_actions = []

    def close(self):
        return

    def step(self, action):
        agent = self.agent_selection
        self.accumulated_actions.append(action)
        for idx, agent in enumerate(self.agents):
            self.rewards[agent] = 0
        if self._agent_selector.is_last():
            self.accumulated_step(self.accumulated_actions)
            self.accumulated_actions = []
        self.agent_selection = self._agent_selector.next()
        self._cumulative_rewards[agent] = 0

    def accumulated_step(self, actions):
        # Track internal environment info.
        self.t += 1

        translated_actions = [action_translation_dict[act] for act in actions]
        self.world.perform_agent_actions(self.world.agents, translated_actions)

        # Visualize.
        if self.record:
            self.game.on_render()

        if self.record:
            self.game.save_image_obs(self.t)

        # Get an image observation
        # image_obs = self.game.get_image_obs()
        self.current_tensor_observation = self.get_tensor_representation()

        info = {"t": self.t, "termination_info": self.termination_info}

        done, rewards, goals = self.compute_rewards()
        for idx, agent in enumerate(self.agents):
            self.dones[agent] = done
            self.rewards[agent] = rewards[idx]
            self.infos[agent] = info

    def observe(self, agent):
        observation = {'symbolic_observation': self.current_tensor_observation,
                       'agent_location': np.asarray(self.world_agent_mapping[agent].location, np.int32),
                       'goal_vector': self.recipe_mapping[agent].goals_completed(NUM_GOALS)}
        return observation

    def compute_rewards(self):
        done = False
        rewards = [0] * len(self.recipes)
        open_goals = [[0]] * len(self.recipes)
        # Done if the episode maxes out
        if self.t >= self.max_num_timesteps and self.max_num_timesteps:
            self.termination_info = f"Terminating because passed {self.max_num_timesteps} timesteps"
            done = True

        for idx, recipe in enumerate(self.recipe_graphs):
            goals_before = recipe.goals_completed(NUM_GOALS)
            recipe.update_recipe_state(self.world)
            open_goals[idx] = recipe.goals_completed(NUM_GOALS)
            bonus = recipe.completed() * 10
            rewards[idx] = sum(goals_before) - sum(open_goals[idx]) + bonus

        if all((recipe.completed() for recipe in self.recipe_graphs)):
            self.termination_info = "Terminating because all deliveries were completed"
            done = True
        return done, rewards, open_goals

    def get_tensor_representation(self):
        tensor = np.zeros((self.world.width, self.world.height, self.graph_representation_length))
        objects = defaultdict(list)
        objects["Agent"] = self.world.agents
        objects.update(self.world.world_objects)

        idx = 0
        for name, states in GAME_OBJECTS_STATEFUL:
            if states:
                for state in states:
                    for obj in objects[name]:
                        if obj.state == state:
                            x, y = obj.location
                            tensor[x, y, idx] += 1
                    idx += 1
            else:
                for obj in objects[name]:
                    x, y = obj.location
                    tensor[x, y, idx] += 1
                idx += 1
        return tensor

    def get_agent_names(self):
        return [agent.name for agent in self.world.agents]

    def render(self, mode='human'):
        pass
