from cooking_zoo.environment.cooking_env import parallel_env
from cooking_zoo.environment.manual_policy import ManualPolicy


num_agents = 2
max_steps = 400
render = True
obs_spaces = ["feature_vector", "feature_vector"]
action_scheme = "scheme3"
meta_file = "example"
level = "coop_test"
recipes = ["TomatoLettuceSalad", "CarrotBanana"]
end_condition_all_dishes = True
agent_visualization = ["human", "robot"]
reward_scheme = {"recipe_reward": 20, "max_time_penalty": -5, "recipe_penalty": -40, "recipe_node_reward": 0}

env = parallel_env(level=level, meta_file=meta_file, num_agents=num_agents, max_steps=max_steps, recipes=recipes,
                   agent_visualization=agent_visualization, obs_spaces=obs_spaces,
                   end_condition_all_dishes=end_condition_all_dishes, action_scheme=action_scheme, render=render,
                   reward_scheme=reward_scheme)

obs = env.reset()

env.render()

action_space = env.action_spaces["player_0"]

manual_policy = ManualPolicy(env, agent_id="player_0")

terminations = {"player_0": False}

while not all(terminations.values()):
    action = {"player_0": manual_policy("player_0"), "player_1": action_space.sample()}
    observations, rewards, terminations, truncations, infos = env.step(action)
    env.render()
