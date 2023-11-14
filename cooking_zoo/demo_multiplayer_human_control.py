from cooking_zoo.environment.cooking_env import parallel_env
from cooking_zoo.environment.manual_policy import ManualPolicy


num_agents = 2
max_steps = 400
render_mode = "human"
obs_spaces = ["symbolic", "feature_vector"]
action_scheme = "scheme3"
level = "partially_prepared"
recipes = ["TomatoLettuceSalad", "CarrotBanana"]
end_condition_all_dishes = True
agent_visualization = ["robot", "human"]
reward_scheme = {"recipe_reward": 20, "max_time_penalty": -5, "recipe_penalty": -40, "recipe_node_reward": 0}

env = parallel_env(level=level, num_agents=num_agents, max_steps=max_steps, recipes=recipes,
                   agent_visualization=agent_visualization, obs_spaces=obs_spaces,
                   end_condition_all_dishes=end_condition_all_dishes, action_scheme=action_scheme, render_mode=render_mode,
                   reward_scheme=reward_scheme)

obs, info = env.reset()

env.render()

action_space = env.action_space("player_0")

manual_policy = ManualPolicy(env, agent_id="player_0")

terminations = {"player_0": False}

while not all(terminations.values()):
    action = {"player_0": manual_policy("player_0"), "player_1": action_space.sample()}
    observations, rewards, terminations, truncations, infos = env.step(action)
    env.render()
