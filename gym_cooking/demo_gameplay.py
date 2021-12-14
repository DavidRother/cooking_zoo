from gym_cooking.environment.game.game import Game

from gym_cooking.environment import cooking_zoo


n_agents = 1
num_humans = 1
max_steps = 100
render = False

level = 'open_room_tomato_salad'
seed = 1
record = False
max_num_timesteps = 100
recipes = ["TomatoSalad"]

parallel_env = cooking_zoo.parallel_env(level=level, num_agents=n_agents, record=record,
                                        max_steps=max_num_timesteps, recipes=recipes, obs_spaces=["numeric"])

game = Game(parallel_env, num_humans, [], max_steps)
store = game.on_execute()

print("done")

