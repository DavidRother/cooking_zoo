from gym_cooking.environment.game.game import Game

from gym_cooking.environment import cooking_zoo

n_agents = 2
num_humans = 1
max_steps = 100
render = False

level = 'open_room_david'
seed = 1
record = False
max_num_timesteps = 1000
recipes = ["TomatoLettuceOnionSalad", 'TomatoLettuceOnionSalad']

parallel_env = cooking_zoo.parallel_env(level=level, num_agents=n_agents, record=record,
                                        max_steps=max_num_timesteps, recipes=recipes)

action_spaces = parallel_env.action_spaces
player_2_action_space = action_spaces["player_1"]


class CookingAgent:

    def __init__(self, action_space):
        self.action_space = action_space

    def get_action(self, observation) -> int:
        return self.action_space.sample()


cooking_agent = CookingAgent(player_2_action_space)

game = Game(parallel_env, num_humans, [cooking_agent], max_steps)
store = game.on_execute()

print("done")
