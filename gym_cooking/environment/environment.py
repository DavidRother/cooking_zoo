from gym_cooking.environment import cooking_zoo

import gym


class GymCookingEnvironment(gym.Env):
    """Environment object for Overcooked."""

    metadata = {'render.modes': ['human'], 'name': "cooking_zoo"}

    def __init__(self, level, seed, record, max_num_timesteps, recipe):
        super().__init__()
        self.num_agents = 1
        self.zoo_env = cooking_zoo.parallel_env(level=level, num_agents=self.num_agents, seed=seed, record=record,
                                                max_num_timestes=max_num_timesteps, recipes=[recipe])
        self.observation_space = self.zoo_env.observation_spaces["player_0"]
        self.action_space = self.zoo_env.action_spaces["player_0"]

    def step(self, action):
        converted_action = {"player_0": action}
        obs, reward, done, info = self.zoo_env.step(converted_action)
        for player_dict in [obs, reward, done, info]:
            player_dict = player_dict["player_0"]
        return obs, reward, done, info

    def reset(self):
        return self.zoo_env.reset()

    def render(self, mode='human'):
        pass
