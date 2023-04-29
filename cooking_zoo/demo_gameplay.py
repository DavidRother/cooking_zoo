from cooking_zoo.environment.manual_policy import ManualPolicy
from cooking_zoo.environment.cooking_env import parallel_env

num_agents = 1
max_steps = 400
render = True
obs_spaces = ["feature_vector"]
action_scheme = "scheme3"
meta_file = "example"
level = "switch_test"
recipes = ["TomatoLettuceSalad"]
end_condition_all_dishes = True
agent_visualization = ["human"]
reward_scheme = {"recipe_reward": 20, "max_time_penalty": -5, "recipe_penalty": -40, "recipe_node_reward": 0}

env = parallel_env(level=level, meta_file=meta_file, num_agents=num_agents, max_steps=max_steps, recipes=recipes,
                   agent_visualization=agent_visualization, obs_spaces=obs_spaces,
                   end_condition_all_dishes=end_condition_all_dishes, action_scheme=action_scheme, render=render,
                   reward_scheme=reward_scheme)
env.reset()
env.render()

terminations = {"player_0": False}

manual_policy = ManualPolicy(env, agent_id="player_0")

while not all(terminations.values()):
    action = {"player_0": manual_policy("player_0")}
    observations, rewards, terminations, truncations, infos = env.step(action)
    env.render()

