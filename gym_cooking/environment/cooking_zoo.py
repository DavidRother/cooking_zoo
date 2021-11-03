# Other core modules
from gym_cooking.cooking_world.cooking_world import CookingWorld
from gym_cooking.cooking_world.world_objects import *
from gym_cooking.cooking_book.recipe_drawer import RECIPES, NUM_GOALS

import numpy as np
from collections import namedtuple, defaultdict
from pettingzoo import AECEnv
from pettingzoo.utils import agent_selector
from pettingzoo.utils import wrappers
from pettingzoo.utils.conversions import parallel_wrapper_fn

import gym


CollisionRepr = namedtuple("CollisionRepr", "time agent_names agent_locations")
COLORS = ['blue', 'magenta', 'yellow', 'green']


def env(level, num_agents, record, max_steps, recipes):
    """
    The env function wraps the environment in 3 wrappers by default. These
    wrappers contain logic that is common to many pettingzoo environments.
    We recommend you use at least the OrderEnforcingWrapper on your own environment
    to provide sane error messages. You can find full documentation for these methods
    elsewhere in the developer documentation.
    """
    env_init = CookingEnvironment(level, num_agents, record, max_steps, recipes)
    env_init = wrappers.CaptureStdoutWrapper(env_init)
    env_init = wrappers.AssertOutOfBoundsWrapper(env_init)
    env_init = wrappers.OrderEnforcingWrapper(env_init)
    return env_init


parallel_env = parallel_wrapper_fn(env)


class CookingEnvironment(AECEnv):
    """Environment object for Overcooked."""

    metadata = {'render.modes': ['human'], 'name': "cooking_zoo"}

    def __init__(self, level, num_agents, record, max_steps, recipes, allowed_objects=None):
        super().__init__()

        self.allowed_objects = allowed_objects or []
        self.possible_agents = ["player_" + str(r) for r in range(num_agents)]
        self.agents = self.possible_agents[:]

        self.level = level
        self.record = record
        self.max_steps = max_steps
        self.t = 0
        self.filename = ""
        self.set_filename()
        self.world = CookingWorld()
        self.recipes = recipes
        self.game = None
        self.recipe_graphs = [RECIPES[recipe]() for recipe in recipes]

        self.termination_info = ""
        self.world.load_level(level=self.level, num_agents=num_agents)
        self.graph_representation_length = sum([tup[1] for tup in GAME_CLASSES_STATE_LENGTH])

        obs_space = {'symbolic_observation': gym.spaces.Box(low=0, high=10,
                                                            shape=(self.world.width, self.world.height,
                                                                   self.graph_representation_length), dtype=np.int32),
                     'agent_location': gym.spaces.Box(low=0, high=max(self.world.width, self.world.height),
                                                      shape=(2,)),
                     'goal_vector': gym.spaces.MultiBinary(NUM_GOALS)}
        self.observation_spaces = {agent: gym.spaces.Dict(obs_space) for agent in self.possible_agents}
        self.action_spaces = {agent: gym.spaces.Discrete(6) for agent in self.possible_agents}
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
        self.filename = f"{self.level}_agents{self.num_agents}"

    def state(self):
        pass

    def reset(self):
        self.world = CookingWorld()
        self.t = 0

        # For tracking data during an episode.
        self.termination_info = ""

        # Load world & distances.
        self.world.load_level(level=self.level, num_agents=self.num_agents)

        for recipe in self.recipe_graphs:
            recipe.update_recipe_state(self.world)

        # if self.record:
        #     self.game = GameImage(
        #         filename=self.filename,
        #         world=self.world,
        #         record=self.record)
        #     self.game.on_init()
        #     self.game.save_image_obs(self.t)
        # else:
        #     self.game = None

        self.agents = self.possible_agents[:]
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
        # translated_actions = [action_translation_dict[actions[f"player_{idx}"]] for idx in range(len(actions))]
        self.world.perform_agent_actions(self.world.agents, actions)

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

        if done:
            self.agents = []

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
        if self.t >= self.max_steps and self.max_steps:
            self.termination_info = f"Terminating because passed {self.max_steps} timesteps"
            done = True

        for idx, recipe in enumerate(self.recipe_graphs):
            goals_before = recipe.goals_completed(NUM_GOALS)
            recipe.update_recipe_state(self.world)
            open_goals[idx] = recipe.goals_completed(NUM_GOALS)
            bonus = recipe.completed() * 0.1
            rewards[idx] = (sum(goals_before) - sum(open_goals[idx]) + bonus) * 10
            if rewards[idx] < 0:
                print(f"Goals before: {goals_before}")
                print(f"Goals after: {open_goals}")

        if all((recipe.completed() for recipe in self.recipe_graphs)):
            self.termination_info = "Terminating because all deliveries were completed"
            done = True
        return done, rewards, open_goals

    def get_tensor_representation(self):
        tensor = np.zeros((self.world.width, self.world.height, self.graph_representation_length))
        objects = defaultdict(list)
        objects.update(self.world.world_objects)
        idx = 0
        for game_class in GAME_CLASSES:
            if game_class is Agent:
                continue
            for obj in objects[ClassToString[game_class]]:
                x, y = obj.location
                tensor[x, y, idx] += 1
            idx += 1
            for stateful_class in STATEFUL_GAME_CLASSES:
                if issubclass(game_class, stateful_class):
                    n = 1
                    for obj in objects[ClassToString[game_class]]:
                        representation = self.handle_stateful_class_representation(obj, stateful_class)
                        n = len(representation)
                        x, y = obj.location
                        for i in range(n):
                            tensor[x, y, idx + i] += representation[i]
                    idx += n
        for agent in self.world.agents:
            x, y = agent.location
            tensor[x, y, idx] = 1
            tensor[x, y, idx + 1] = 1 if agent.orientation == 1 else 0
            tensor[x, y, idx + 2] = 1 if agent.orientation == 2 else 0
            tensor[x, y, idx + 3] = 1 if agent.orientation == 3 else 0
            tensor[x, y, idx + 4] = 1 if agent.orientation == 4 else 0
        return tensor

    def get_agent_names(self):
        return [agent.name for agent in self.world.agents]

    def render(self, mode='human'):
        pass

    @staticmethod
    def handle_stateful_class_representation(obj, stateful_class):
        if stateful_class is ChopFood:
            return [int(obj.chop_state == ChopFoodStates.CHOPPED)]
        if stateful_class is BlenderFood:
            return [obj.current_progress]
        raise ValueError(f"Could not process stateful class {stateful_class}")
