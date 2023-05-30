import gym

num_agents = 1
max_steps = 400
render = False
obs_spaces = ["feature_vector"]
action_scheme = "scheme3"
meta_file = "example"
level = "switch_test"
recipes = ["TomatoLettuceSalad"]
end_condition_all_dishes = True
agent_visualization = ["human"]
reward_scheme = {"recipe_reward": 20, "max_time_penalty": -5, "recipe_penalty": -40, "recipe_node_reward": 0}

env = gym.envs.make("cooking_zoo:cookingEnv-v1", level=level, meta_file=meta_file,
                    max_steps=max_steps, recipes=recipes, agent_visualization=agent_visualization,
                    obs_spaces=obs_spaces, end_condition_all_dishes=end_condition_all_dishes,
                    action_scheme=action_scheme, render=render, reward_scheme=reward_scheme)

obs, info = env.reset()

action_space = env.action_space

terminated = False
truncated = False

while not terminated or truncated:
    action = action_space.sample()
    observation, reward, terminated, truncated, info = env.step(action)
