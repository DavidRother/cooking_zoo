from gym_cooking.environment import cooking_zoo
from gym.utils import seeding

import gym


class GymCookingEnvironment(gym.Env):
    """Environment object for Overcooked."""

    metadata = {'render.modes': ['human'], 'name': "cooking_zoo"}

    def __init__(self, level, record, max_steps, recipe, obs_spaces=["numeric"]):
        super().__init__()
        self.num_agents = 1
        self.zoo_env = cooking_zoo.parallel_env(level=level, num_agents=self.num_agents, record=record,
                                                max_steps=max_steps, recipes=[recipe], obs_spaces=obs_spaces)
        self.observation_space = self.zoo_env.observation_spaces["player_0"]
        self.action_space = self.zoo_env.action_spaces["player_0"]

    def step(self, action):
        converted_action = {"player_0": action}
        obs, reward, done, info = self.zoo_env.step(converted_action)
        return obs["player_0"], reward["player_0"], done["player_0"], info["player_0"]

    def reset(self):
        return self.zoo_env.reset()["player_0"]

    def render(self, mode='human'):
        pass

