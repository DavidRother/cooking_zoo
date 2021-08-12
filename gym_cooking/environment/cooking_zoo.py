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


def env(level, num_agents, seed, playable, record, max_num_timesteps, recipes):
    """
    The env function wraps the environment in 3 wrappers by default. These
    wrappers contain logic that is common to many pettingzoo environments.
    We recomend you use at least the OrderEnforcingWrapper on your own environment
    to provide sane error messages. You can find full documentation for these methods
    elsewhere in the developer documentation.
    """
    env_init = CookingEnvironment(level, num_agents, seed, playable, record, max_num_timesteps, recipes)
    env_init = wrappers.CaptureStdoutWrapper(env_init)
    env_init = wrappers.AssertOutOfBoundsWrapper(env_init)
    env_init = wrappers.OrderEnforcingWrapper(env_init)
    return env_init


class CookingEnvironment(AECEnv):
    """Environment object for Overcooked."""

    def __init__(self, level, num_agents, seed, playable, record, max_num_timesteps, recipes):
        super().__init__()
        self.level = level
        self.n_agents = num_agents
        self.seed = seed
        self.playable = playable
        self.record = record
        self.max_num_timesteps = max_num_timesteps
        self.t = 0
        self.filename = ""
        self.set_filename()
        self.world = CookingWorld([], 0, 0)
        self.recipes = recipes
        self.sim_agents = []
        self.agent_actions = {}
        self.game = None
        self.distances = {}
        self.recipe_graphs = [RECIPES[recipe]() for recipe in recipes]

        # For visualizing episode.
        self.rep = []

        # For tracking data during an episode.
        self.collisions = []
        self.termination_info = ""
        self.successful = False
        self.verbose = False
        self.load_level(level=self.level, num_agents=self.n_agents)
        self.graph_representation_length = sum([max(len(tup[1]), 2) if tup[1] else 1 for tup in GAME_OBJECTS_STATEFUL])

        self.possible_agents = ["player_" + str(r) for r in range(num_agents)]
        self.agent_name_mapping = dict(zip(self.possible_agents, list(range(len(self.possible_agents)))))
        obs_space = {'symbolic_observation': gym.spaces.Box(low=0, high=10,
                                                            shape=(self.graph_representation_length, self.world.width,
                                                                   self.world.height), dtype=np.int),
                     'agent_location': gym.spaces.Box(low=0, high=max(self.world.width, self.world.height),
                                                      shape=(2,)),
                     'goal_vector': gym.spaces.MultiBinary(NUM_GOALS)}
        self.observation_space = {agent: gym.spaces.Dict(obs_space) for agent in self.possible_agents}
        self.action_space = {agent: gym.spaces.Discrete(5) for agent in self.possible_agents}

    def set_filename(self):
        self.filename = f"{self.level}_agents{self.n_agents}_seed{self.seed}"

    def state(self):
        pass

    def observe(self, agent):
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
                        # sim_agent = SimAgent(
                        #         name='agent-'+str(len(self.sim_agents)+1),
                        #         id_color=COLORS[len(self.sim_agents)],
                        #         location=(int(loc[0]), int(loc[1])))
                        # self.sim_agents.append(sim_agent)

        self.sim_agents = agents
        self.world.agents = agents
        self.world.width = x + 1
        self.world.height = y

    def reset(self):
        self.world = CookingWorld([], 0, 0)
        self.agent_actions = {}
        self.t = 0

        # For tracking data during an episode.
        self.collisions = []
        self.termination_info = ""
        self.successful = False

        # Load world & distances.
        self.load_level(
            level=self.level,
            num_agents=self.n_agents)

        if self.record:
            self.game = GameImage(
                filename=self.filename,
                world=self.world,
                sim_agents=self.sim_agents,
                record=self.record)
            self.game.on_init()
        else:
            self.game = None
        if self.record:
            self.game.save_image_obs(self.t)

        # Get an image observation
        # image_obs = self.game.get_image_obs()
        tensor_obs = self.get_tensor_representation()

        # new_obs = copy.copy(self)
        done, rewards, goals = self.compute_rewards()
        info = {"t": self.t, "agent_locations": [agent.location for agent in self.sim_agents],
                "tensor_obs": tensor_obs,
                "done": done, "termination_info": self.termination_info, "rewards": rewards, "goals": goals}

        return info

    def close(self):
        return

    def step(self, action_dict):
        # Track internal environment info.
        self.t += 1
        if self.verbose:
            print("===============================")
            print("[environment.step] @ TIMESTEP {}".format(self.t))
            print("===============================")

        actions = [action_dict[agent.name] for agent in self.sim_agents]

        self.world.perform_agent_actions(self.sim_agents, actions)

        # Visualize.
        if self.record:
            self.game.on_render()

        if self.record:
            self.game.save_image_obs(self.t)

        # Get an image observation
        # image_obs = self.game.get_image_obs()
        tensor_obs = self.get_tensor_representation()

        done, rewards, goals = self.compute_rewards()
        obs = self.create_observation()
        info = {"t": self.t, "agent_locations": [agent.location for agent in self.sim_agents],
                "tensor_obs": tensor_obs,
                "done": done, "termination_info": self.termination_info, "rewards": rewards, "goals": goals}
        return tensor_obs, sum(rewards), done, info

    def create_observation(self, agent_num, open_goals, tensor_obs):
        agent_location = np.asarray(self.sim_agents[agent_num].location, np.int)
        observation = {'symbolic_observation': tensor_obs,
                       'agent_location': agent_location,
                       'goal_vector': open_goals[agent_num]}
        return observation

    def compute_rewards(self):
        done = False
        rewards = [0] * len(self.recipes)
        open_goals = [[0]] * len(self.recipes)
        # Done if the episode maxes out
        if self.t >= self.max_num_timesteps and self.max_num_timesteps:
            self.termination_info = f"Terminating because passed {self.max_num_timesteps} timesteps"
            self.successful = False
            done = True

        for idx, recipe in enumerate(self.recipe_graphs):
            goals_before = recipe.goals_completed(NUM_GOALS)
            recipe.update_recipe_state(self.world)
            open_goals[idx] = recipe.goals_completed(NUM_GOALS)
            bonus = recipe.completed() * 10
            rewards[idx] = sum(goals_before) - sum(open_goals[idx]) + bonus

        if all((recipe.completed() for recipe in self.recipe_graphs)):
            self.termination_info = "Terminating because all deliveries were completed"
            self.successful = True
            done = True
        return done, rewards, open_goals

    def get_tensor_representation(self):
        tensor = np.zeros((self.world.width, self.world.height, self.graph_representation_length))
        objects = defaultdict(list)
        objects["Agent"] = self.sim_agents
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
        return [agent.name for agent in self.sim_agents]

    def render(self, mode='human'):
        pass
