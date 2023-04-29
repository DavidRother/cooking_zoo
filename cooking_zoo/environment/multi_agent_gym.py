from cooking_zoo.environment import cooking_env
import gymnasium as gym


class GymCookingEnvironment(gym.Env):
    """Environment object for Overcooked."""

    metadata = {'render.modes': ['human'], 'name': "multi_agent_cooking_zoo"}

    def __init__(self, level, meta_file, num_agents, max_steps, recipes, agent_visualization=None, obs_spaces=None,
                 end_condition_all_dishes=False, action_scheme="scheme1", render=False, reward_scheme=None):
        super().__init__()
        self.zoo_env = cooking_env.parallel_env(level=level, meta_file=meta_file, num_agents=num_agents,
                                                max_steps=max_steps, recipes=recipes,
                                                agent_visualization=agent_visualization, obs_spaces=obs_spaces,
                                                end_condition_all_dishes=end_condition_all_dishes,
                                                action_scheme=action_scheme, render=render, reward_scheme=reward_scheme)
        self.observation_space = self.zoo_env.observation_space("player_0")
        self.action_space = self.zoo_env.action_space("player_0")

    def step(self, actions):
        action_dict = {f"player_{i}": actions[i] for i in range(len(actions))}
        obs, reward, termination, truncation, info = self.zoo_env.step(action_dict)
        return [obs[f"player_{i}"] for i in range(len(obs))], [reward[f"player_{i}"] for i in range(len(reward))], \
               [termination[f"player_{i}"] for i in range(len(termination))], \
               [truncation[f"player_{i}"] for i in range(len(truncation))], \
               [info[f"player_{i}"] for i in range(len(info))]

    def reset(self):
        obs = self.zoo_env.reset()
        return [obs[f"player_{i}"] for i in range(len(obs))]

    def render(self, mode='human'):
        self.zoo_env.render()

