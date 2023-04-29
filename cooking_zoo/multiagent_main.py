import gym

num_agents = 2
max_steps = 400
render = False
obs_spaces = ["feature_vector", "feature_vector"]
action_scheme = "scheme3"
meta_file = "example"
level = "coexistence_test"
recipes = ["TomatoLettuceSalad", "CarrotBanana"]
end_condition_all_dishes = True
agent_visualization = ["robot", "human"]
reward_scheme = {"recipe_reward": 20, "max_time_penalty": -5, "recipe_penalty": -40, "recipe_node_reward": 0}

env = gym.envs.make("cooking_zoo:cookingEnvMA-v1", level=level, meta_file=meta_file, num_agents=num_agents,
                    max_steps=max_steps, recipes=recipes, agent_visualization=agent_visualization,
                    obs_spaces=obs_spaces, end_condition_all_dishes=end_condition_all_dishes,
                    action_scheme=action_scheme, render=render, reward_scheme=reward_scheme)

obs = env.reset()
action_space = env.action_space
done = [False, False]

while not all(done):
    actions = [action_space.sample() for idx in range(num_agents)]
    observation, reward, done, info = env.step(actions)
