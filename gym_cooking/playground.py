# from environment import OvercookedEnvironment
# from gym_cooking.envs import OvercookedEnvironment
from gym_cooking.envs import OvercookedEnvironment
from recipe_planner.recipe import *
from utils.world import World
from utils.agent import RealAgent, SimAgent, COLORS
from utils.core import *
from misc.game.gameplay import GamePlay
from misc.metrics.metrics_bag import Bag
# from .recipe_planner

import numpy as np
import random
import argparse
from collections import namedtuple

import gym


def initialize_agents(arglist):
    real_agents = []

    with open('utils/levels/{}.txt'.format(arglist.level), 'r') as f:
        phase = 1
        recipes = []
        for line in f:
            line = line.strip('\n')
            if line == '':
                phase += 1

            # phase 2: read in recipe list
            elif phase == 2:
                recipes.append(globals()[line]())

            # phase 3: read in agent locations (up to num_agents)
            elif phase == 3:
                if len(real_agents) < arglist.n_agents:
                    loc = line.split(' ')
                    real_agent = RealAgent(
                            arglist=arglist,
                            name='agent-'+str(len(real_agents)+1),
                            id_color=COLORS[len(real_agents)],
                            recipes=recipes)
                    real_agents.append(real_agent)

    return real_agents


Namespace = namedtuple('Namespace', ["level", "num_agents", "max_num_timesteps", "max_num_subtasks", "seed",
                                     "with_image_obs", "beta", "alpha", "tau", "cap", "main_cap", "play", "record",
                                     "model1", "model2", "model3", "model4"])

arglist = Namespace('partial-divider_salad', 2, 100, 14, 1, True, 1.3, 0.01, 2, 75, 100, False, False, "bd", "bd",
                    None, None)

print("Initializing environment and agents.")
env = gym.envs.make("gym_cooking:overcookedEnv-v0", arglist=arglist)
obs = env.reset()
# game = GameVisualize(env)
real_agents = initialize_agents(arglist=arglist)

# Info bag for saving pkl files
bag = Bag(arglist=arglist, filename=env.filename)
bag.set_recipe(recipe_subtasks=env.all_subtasks)

while not env.done():
    action_dict = {}

    for agent in real_agents:
        action = agent.select_action(obs=obs)
        action_dict[agent.name] = action

    obs, reward, done, info = env.step(action_dict=action_dict)
    print(reward)

    # Agents
    for agent in real_agents:
        agent.refresh_subtasks(world=env.world)

    # Saving info
    bag.add_status(cur_time=info['t'], real_agents=real_agents)


# Saving final information before saving pkl file
bag.set_collisions(collisions=env.collisions)
bag.set_termination(termination_info=env.termination_info,
        successful=env.successful)