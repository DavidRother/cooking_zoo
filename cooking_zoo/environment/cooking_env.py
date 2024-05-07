# Other core modules
import copy

from cooking_zoo.cooking_world.cooking_world import CookingWorld
from cooking_zoo.cooking_world.world_objects import *
from cooking_zoo.cooking_world.actions import *
from cooking_zoo.cooking_book.recipe_drawer import RECIPES, NUM_GOALS, RECIPE_STORE, DEFAULT_NUM_GOALS

import numpy as np
from collections import namedtuple, defaultdict
from pettingzoo import AECEnv
from pettingzoo.utils import agent_selector
from pettingzoo.utils import wrappers
from pettingzoo.utils.conversions import parallel_wrapper_fn
from gymnasium.utils import seeding
from cooking_zoo.environment.game.graphic_pipeline import GraphicPipeline
import gymnasium as gym


CollisionRepr = namedtuple("CollisionRepr", "time agent_names agent_locations")
COLORS = ['blue', 'magenta', 'yellow', 'green']

FPS = 20


def env(level, meta_file, num_agents, max_steps, recipes, agent_visualization=None, obs_spaces=None,
        end_condition_all_dishes=False, action_scheme="scheme1", render=False, reward_scheme=None,
        agent_respawn_rate=0.0, grace_period=20, agent_despawn_rate=0.0):
    """
    The env function wraps the environment in 3 wrappers by default. These
    wrappers contain logic that is common to many pettingzoo environments.
    We recommend you use at least the OrderEnforcingWrapper on your own environment
    to provide sane error messages. You can find full documentation for these methods
    elsewhere in the developer documentation.
    """
    env_init = CookingEnvironment(level, meta_file, num_agents, max_steps, recipes, agent_visualization,
                                  obs_spaces, end_condition_all_dishes=end_condition_all_dishes,
                                  action_scheme=action_scheme, render=render, reward_scheme=reward_scheme,
                                  agent_respawn_rate=agent_respawn_rate, grace_period=grace_period,
                                  agent_despawn_rate=agent_despawn_rate)
    env_init = wrappers.CaptureStdoutWrapper(env_init)
    env_init = wrappers.OrderEnforcingWrapper(env_init)
    return env_init


parallel_env = parallel_wrapper_fn(env)


class CookingEnvironment(AECEnv):
    """Environment object for Overcooked."""

    metadata = {
        "render_modes": ["human", "rgb_array"],
        'render.modes': ['human', "rgb_array"],
        "name": "cookingzoo_v1",
        "is_parallelizable": True,
        "render_fps": FPS,
    }

    action_scheme_map = {"scheme1": ActionScheme1, "scheme2": ActionScheme2, "scheme3": ActionScheme3}

    def __init__(self, level, meta_file, num_agents, max_steps, recipes, agent_visualization=None, obs_spaces=None,
                 end_condition_all_dishes=False, allowed_objects=None, action_scheme="scheme1", render=False,
                 reward_scheme=None, agent_respawn_rate=0.0, grace_period=20, agent_despawn_rate=0.0):
        super().__init__()

        obs_spaces = obs_spaces or ["feature_vector"]
        self.allowed_obs_spaces = ["symbolic", "full", "feature_vector", "tensor"]
        self.action_scheme = action_scheme
        self.action_scheme_class = self.action_scheme_map[self.action_scheme]
        assert len(set(obs_spaces + self.allowed_obs_spaces)) == len(self.allowed_obs_spaces), \
            f"Selected invalid obs spaces. Allowed {self.allowed_obs_spaces}"
        assert len(obs_spaces) != 0, f"Please select an observation space from: {self.allowed_obs_spaces}"
        self.obs_spaces = obs_spaces
        self.allowed_objects = allowed_objects or []
        self.possible_agents = ["player_" + str(r) for r in range(num_agents)]
        self.agents = self.possible_agents[:]
        self.agent_visualization = agent_visualization or ["human"] * num_agents
        self.reward_scheme = reward_scheme or {"recipe_reward": 20, "max_time_penalty": -5, "recipe_penalty": -40,
                                               "recipe_node_reward": 0}
        self.agent_respawn_rate = agent_respawn_rate
        self.agent_despawn_rate = agent_despawn_rate
        self.grace_period = grace_period

        self.level = level
        self.max_steps = max_steps
        self.t = 0
        self.filename = ""
        self.set_filename()
        self.meta_file = meta_file
        self.world = CookingWorld(self.action_scheme_class, meta_file, agent_respawn_rate=agent_respawn_rate,
                                  grace_period=grace_period, agent_despawn_rate=agent_despawn_rate)
        assert self.num_agents <= self.world.meta_object_information["Agent"], \
            "Too many agents for this level"
        self.recipe_names = recipes
        self.recipes = recipes
        self.game = None
        self.render_flag = render
        if RECIPE_STORE:
            self.recipes = RECIPE_STORE
            self.num_goals = NUM_GOALS
        else:
            self.recipes = RECIPES
            self.num_goals = DEFAULT_NUM_GOALS
        self.recipe_graphs = [self.recipes[recipe] for recipe in recipes]

        self.termination_info = ""
        self.world.load_level(level=self.level, num_agents=num_agents)
        self.graph_representation_length = sum([cls.state_length() for cls in GAME_CLASSES]) + Agent.state_length()
        objects = defaultdict(list)
        objects.update(self.world.world_objects)
        objects["Agent"] = self.world.agents
        self.feature_vector_representation_length = 0
        for name, num in self.world.meta_object_information.items():
            cls = StringToClass[name]
            self.feature_vector_representation_length += cls.feature_vector_length() * num
        self.tensor_space = gym.spaces.Box(low=0, high=1, shape=(self.world.width, self.world.height,
                                                                  self.graph_representation_length), dtype=np.int32)
        numeric_obs_space = {'feature_vector': gym.spaces.Box(low=0, high=10,
                                                              shape=(self.world.width, self.world.height,
                                                                     self.graph_representation_length), dtype=np.int32),
                             'agent_location': gym.spaces.Box(low=0, high=max(self.world.width, self.world.height),
                                                              shape=(2,)),
                             'goal_vector': gym.spaces.MultiBinary(self.num_goals)}
        self.feature_obs_space = gym.spaces.Box(low=-1, high=1,
                                                shape=(self.feature_vector_representation_length,))
        obs_space_dict = {"full": numeric_obs_space,
                          "feature_vector": self.feature_obs_space,
                          "symbolic": {},
                          "tensor": self.tensor_space}
        self.observation_spaces = {agent: obs_space_dict[obs_space]
                                   for agent, obs_space in zip(self.possible_agents, self.obs_spaces)}
        self.action_spaces = {agent: gym.spaces.Discrete(len(self.action_scheme_class.ACTIONS))
                              for agent in self.possible_agents}
        self.has_reset = True
        self.end_condition_all_dishes = end_condition_all_dishes

        self.recipe_mapping = dict(zip(self.possible_agents, self.recipe_graphs))
        self.agent_name_mapping = dict(zip(self.possible_agents, list(range(len(self.possible_agents)))))
        self.world_agent_mapping = dict(zip(self.possible_agents, self.world.agents))
        self.world_agent_to_env_agent_mapping = dict(zip(self.world.agents, self.possible_agents))
        self.agent_selection = None
        self._agent_selector = agent_selector(self.agents)
        self.done = False
        self.rewards = dict(zip(self.agents, [0 for _ in self.agents]))
        self._cumulative_rewards = dict(zip(self.agents, [0 for _ in self.agents]))
        self.terminations = dict(zip(self.agents, [False for _ in self.agents]))
        self.truncations = dict(zip(self.agents, [False for _ in self.agents]))
        self.infos = dict(zip(self.agents, [{} for _ in self.agents]))
        self.accumulated_actions = []
        self.current_tensor_observation = np.zeros((self.world.width, self.world.height,
                                                    self.graph_representation_length))
        self.render_mode = "human"
        self.np_random = None
        self.loaded_recipes = []
        if not RECIPE_STORE:
            self.loaded_recipes = list(RECIPES.keys())
        else:
            self.loaded_recipes = list(RECIPE_STORE.keys())
        # get index of recipe in recipe_list
        idx = [self.loaded_recipes.index(recipe) for recipe in self.recipe_names]
        # get one hot numpy vector
        eye_matrix = np.eye(len(self.loaded_recipes))
        self.goal_vectors = dict(zip(self.agents, [np.eye(len(self.loaded_recipes))[i] for i in idx]))

        self.graphic_pipeline = None
        self.done_once = [False] * self.num_agents

    def set_filename(self):
        self.filename = f"{self.level}_agents{self.num_agents}"

    def state(self):
        pass

    def observation_space(self, agent):
        return self.observation_spaces[agent]

    def action_space(self, agent):
        return self.action_spaces[agent]

    def seed(self, seed=None):
        self.np_random, seed = seeding.np_random(seed)

    def reset(self, seed=None, return_info=False, options=None):
        options = options or {"full_reset": True}
        # self.world = CookingWorld(self.action_scheme_class)
        self.t = 0

        # For tracking data during an episode.
        self.termination_info = ""

        self.agents = self.possible_agents[:]
        self._agent_selector.reinit(self.agents)
        self.agent_selection = self._agent_selector.next()
        
        # Load world & distances.
        if options["full_reset"]:
            self.world = CookingWorld(self.action_scheme_class, self.meta_file,
                                      agent_respawn_rate=self.agent_respawn_rate, grace_period=self.grace_period,
                                      agent_despawn_rate=self.agent_despawn_rate)
        self.world.load_level(level=self.level, num_agents=self.num_agents)

        for recipe in self.recipe_graphs:
            recipe.update_recipe_state(self.world)

        # Get an image observation
        self.recipe_mapping = dict(zip(self.possible_agents, self.recipe_graphs))
        self.agent_name_mapping = dict(zip(self.possible_agents, list(range(len(self.possible_agents)))))
        self.world_agent_mapping = dict(zip(self.possible_agents, self.world.agents))
        self.world_agent_to_env_agent_mapping = dict(zip(self.world.agents, self.possible_agents))
        self.rewards = dict(zip(self.agents, [0 for _ in self.agents]))
        self._cumulative_rewards = dict(zip(self.agents, [0 for _ in self.agents]))
        self.terminations = dict(zip(self.agents, [False for _ in self.agents]))
        self.truncations = dict(zip(self.agents, [False for _ in self.agents]))
        infos = self.compute_infos(self.agents, [0] * self.num_agents)
        self.infos = dict(zip(self.agents, infos))
        self.accumulated_actions = []
        self.graphic_pipeline = None
        self.done_once = [False] * self.num_agents

    def close(self):
        return

    def step(self, action):
        if action is None:
            if any(self.world.status_changed):
                self.agents = [agent for idx, agent in enumerate(self.possible_agents[:])
                               if self.world.active_agents[idx]]
                self._agent_selector = agent_selector(self.agents)
                if not self.agents:
                    return
                self.agent_selection = self._agent_selector.next()
            return
        if self.terminations[self.agent_selection] or self.truncations[self.agent_selection]:
            self._was_dead_step(action)
            return
        agent = self.agent_selection
        self.accumulated_actions.append(action)
        for idx, agent in enumerate(self.agents):
            self.rewards[agent] = 0
        if self._agent_selector.is_last():
            self.accumulated_step(self.accumulated_actions)
            self.accumulated_actions = []
            for ag in self.agents:
                if self.terminations[ag] or self.truncations[ag]:
                    self.agent_selection = ag
                    self._cumulative_rewards[agent] = 0
                    return
        self.agent_selection = self._agent_selector.next()
        self._cumulative_rewards[agent] = 0

    def accumulated_step(self, actions):
        self.t += 1
        active_agents_start = self.world.active_agents[:]
        self.world.world_step(actions)
        dones, rewards, goals, infos, truncations = self.compute_rewards(active_agents_start, actions)
        info = {"t": self.t, "termination_info": self.termination_info}

        self.rewards = {}
        self.terminations = {}
        self.truncations = {}
        self.infos = {}

        offset_idx = 0
        for idx, agent in enumerate(self.possible_agents[:]):
            if not (self.world.active_agents[idx] or self.world.status_changed[idx]):
                offset_idx += 1
                continue

            self.rewards[agent] = rewards[idx - offset_idx]
            self.terminations[agent] = dones[idx - offset_idx]
            self.truncations[agent] = truncations[idx - offset_idx]
            self.infos[agent] = {**info, **infos[idx - offset_idx]}
            self._cumulative_rewards[agent] += rewards[idx - offset_idx]

        self.agents = [agent for idx, agent in enumerate(self.possible_agents[:])
                       if self.world.active_agents[idx] or self.world.status_changed[idx]]
        self._agent_selector = agent_selector(self.agents)

    def observe(self, agent):
        obs_space = self.obs_spaces[self.possible_agents.index(agent)]
        observation = []
        if "full" == obs_space:
            num_observation = {'feature_vector': self.current_tensor_observation,
                               'agent_location': np.asarray(self.world_agent_mapping[agent].location, np.int32),
                               'goal_vector': self.recipe_mapping[agent].goals_completed(self.num_goals)}
            observation.append(num_observation)
        if "symbolic" == obs_space:
            objects = defaultdict(list)
            objects.update(self.world.world_objects)
            objects["Agent"] = self.world.agents
            sym_observation = copy.deepcopy(objects)
            observation.append(sym_observation)
        if "feature_vector" == obs_space:
            observation.append(self.get_feature_vector(agent))
        if "tensor" == obs_space:
            observation.append(self.get_tensor_observations(agent))
        returned_observation = observation if not len(observation) == 1 else observation[0]
        return returned_observation

    def compute_rewards(self, active_agents_start, actions):
        rewards = [0] * len(self.recipe_graphs)
        open_goals = [[0]] * len(self.recipe_graphs)
        # Done if the episode maxes out
        truncations = self.compute_truncated()

        for idx, recipe in enumerate(self.recipe_graphs):
            # goals_before = recipe.goals_completed(self.num_goals)
            num_fulfilled_before = recipe.conditions_fulfilled
            recipe.update_recipe_state(self.world)
            num_fulfilled_after = recipe.conditions_fulfilled
            open_goals[idx] = recipe.goals_completed(self.num_goals)
            malus = not recipe.completed() and self.done_once[idx]
            bonus = recipe.completed() and not self.done_once[idx]
            # rewards[idx] += (sum(goals_before) - sum(open_goals[idx])) * self.reward_scheme["recipe_node_reward"]
            rewards[idx] += (num_fulfilled_after - num_fulfilled_before) * self.reward_scheme["recipe_node_reward"]
            rewards[idx] += bonus * self.reward_scheme["recipe_reward"]
            rewards[idx] += malus * self.reward_scheme["recipe_penalty"]
            rewards[idx] += (self.reward_scheme["max_time_penalty"] / self.max_steps)
            if self.done_once[idx]:
                rewards[idx] = 0
            self.done_once[idx] = self.done_once[idx] or recipe.completed()

        infos = self.compute_infos(active_agents_start, actions)
        if self.end_condition_all_dishes:
            recipe_dones = all(self.done_once)
        else:
            recipe_dones = any(self.done_once)
        dones = []
        for idx, truncation in enumerate(truncations):
            dones.append(recipe_dones)
            self.world.status_changed[idx] = recipe_dones or truncation
            self.world.active_agents[idx] = not (recipe_dones or truncation)
        self.compute_relevant_agents()
        return dones, rewards, open_goals, infos, truncations

    def compute_relevant_agents(self):
        self.world.relevant_agents = [agent for idx, agent in enumerate(self.world.agents)
                                      if self.world.active_agents[idx] or self.world.status_changed[idx]]

    def compute_goal_vector(self):
        goal_vector = [recipe.goals_completed(self.num_goals) for recipe in self.recipe_graphs]
        return goal_vector

    def compute_infos(self, active_agents_start, actions):
        infos = []
        offset_idx = 0
        for idx, agent in enumerate(self.possible_agents):
            world_agent = self.world_agent_mapping[agent]
            if world_agent not in self.world.relevant_agents:
                offset_idx += 1
                continue
            if not active_agents_start[idx]:
                offset_idx += 1
            action = 0 if not active_agents_start[idx] else actions[idx - offset_idx]
            infos.append({f"task_done": self.done_once[idx], "action": action,
                          "task": self.recipe_names[idx], "goal_vector": self.goal_vectors[agent]})
        return infos

    def compute_truncated(self):
        if self.t >= self.max_steps:
            self.termination_info = f"Terminating because {self.max_steps} timesteps passed"
            truncated = [True] * len(self.world.relevant_agents)
            self.world.active_agents = [False] * self.num_agents
            self.world.status_changed = [True if agent in self.world.relevant_agents else False
                                         for agent in self.world.agents]
        else:
            truncated = [False] * len(self.world.relevant_agents)

        offset_idx = 0
        for idx, agent in enumerate(self.world.agents):
            if agent not in self.world.relevant_agents:
                offset_idx += 1
                continue
            if self.world.status_changed[idx] and not self.world.active_agents[idx]:
                truncated[idx - offset_idx] = True
        return truncated

    def get_feature_vector(self, agent):
        feature_vector = []
        objects = defaultdict(list)
        objects.update(self.world.world_objects)
        objects["Agent"] = self.world.agents
        x, y = self.world_agent_mapping[agent].location
        agent_features = self.world_agent_mapping[agent].feature_vector_representation()
        # agent_features[0] = agent_features[0] / self.world.width
        # agent_features[1] = agent_features[1] / self.world.height
        agent_features[0] = 0
        agent_features[1] = 0
        feature_vector.extend(agent_features)
        start_features = 0
        # print(f"Agent 1 start: {start_features} end: {len(feature_vector)}")
        start_features += len(agent_features)
        for name, num in self.world.meta_object_information.items():
            cls = StringToClass[name]
            current_num = 0
            for obj in objects[ClassToString[cls]]:
                if obj is self.world_agent_mapping[agent]:
                    current_num += 1
                    continue
                features = list(obj.feature_vector_representation())
                if features and obj is not self.world_agent_mapping[agent]:
                    features[0] = (features[0] - x) / self.world.width
                    features[1] = (features[1] - y) / self.world.height
                assert len(features) == cls.feature_vector_length()
                feature_vector.extend(features)
                current_num += 1
                # print(f"{name} {current_num} start: {start_features} end: {start_features + len(features)}")
                start_features += len(features)
            assert current_num <= num
            zeroes = [0] * (num - current_num) * cls.feature_vector_length()
            feature_vector.extend(zeroes)
            start_features += len(zeroes)
        new_vector = np.array(feature_vector)
        assert len(new_vector) == self.feature_vector_representation_length
        return new_vector

    def get_agent_names(self):
        return [agent.name for agent in self.world.agents]

    def render(self, **kwargs):
        if not self.graphic_pipeline:
            self.graphic_pipeline = GraphicPipeline(self.world, self.agent_visualization, self.render_flag)
            self.graphic_pipeline.initialize()
        self.graphic_pipeline.render(self.render_flag)

    def screenshot(self, path="screenshot.png"):
        self.graphic_pipeline.save_image(path)

    def get_tensor_observations(self, agent):
        objects = defaultdict(list)
        objects.update(self.world.world_objects)
        objects["Agent"] = self.world.agents
        x, y = self.world_agent_mapping[agent].location
        agent_features = self.world_agent_mapping[agent].numeric_state_representation()
        world_tensor = np.zeros((self.world.width, self.world.height, self.graph_representation_length))
        current_state_length = 0
        world_tensor[x, y, current_state_length:current_state_length+Agent.state_length()] = agent_features
        for name, num in self.world.meta_object_information.items():
            cls = StringToClass[name]
            state_length = cls.state_length()
            for obj in objects[ClassToString[cls]]:
                if obj is self.world_agent_mapping[agent]:
                    continue
                features = list(obj.numeric_state_representation())
                if features and obj is not self.world_agent_mapping[agent]:
                    x, y = obj.location
                    world_tensor[x, y, current_state_length:current_state_length + state_length] = features
            current_state_length += state_length
        return world_tensor

