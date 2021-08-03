# modules for game
from gym_cooking.misc.game.game import Game
from gym_cooking.misc.game.utils import *
from gym_cooking.utils.core import *
from gym_cooking.utils.interact import interact

# helpers
import pygame
import numpy as np
import argparse
from collections import defaultdict
from random import randrange
import os
from datetime import datetime


class GamePlay(Game):

    def __init__(self, env, num_humans, ai_policies, max_steps=100):
        Game.__init__(self, env.world, env.sim_agents, play=True)
        self.env = env
        self.save_dir = 'misc/game/screenshots'
        self.store = {"actions": [], "tensor_obs": [], "agent_states": [], "rewards": [], "done": []}
        self.num_humans = num_humans
        self.ai_policies = ai_policies
        self.max_steps = max_steps
        self.current_step = 0
        self.last_obs = env.get_tensor_representation()
        assert len(ai_policies) == len(env.sim_agents) - num_humans
        if not os.path.exists(self.save_dir):
            os.makedirs(self.save_dir)

        # tally up all gridsquare types
        self.gridsquares = []
        self.gridsquare_types = defaultdict(set)  # {type: set of coordinates of that type}
        for name, gridsquares in self.world.objects.items():
            for gridsquare in gridsquares:
                self.gridsquares.append(gridsquare)
                self.gridsquare_types[name].add(gridsquare.location)

    def on_event(self, event):
        if event.type == pygame.QUIT:
            self._running = False
        elif event.type == pygame.KEYDOWN:
            # Save current image
            if event.key == pygame.K_RETURN:
                image_name = '{}_{}.png'.format(self.env.filename, datetime.now().strftime('%m-%d-%y_%H-%M-%S'))
                pygame.image.save(self.screen, '{}/{}'.format(self.save_dir, image_name))
                print('just saved image {} to {}'.format(image_name, self.save_dir))
                return

            # Control current human agent
            if event.key in KeyToTuple_human1 and self.num_humans > 0:
                action_translation_dict = {0: (0, 0), 1: (1, 0), 2: (0, 1), 3: (-1, 0), 4: (0, -1)}
                reverse_action_translation_dict = {(0, 0): 0, (1, 0): 1, (0, 1): 2, (-1, 0): 3, (0, -1): 4}
                action = KeyToTuple_human1[event.key]
                self.sim_agents[0].action = action
                self.store["tensor_obs"].append(self.last_obs)
                self.store["agent_states"].append([agent.location for agent in self.sim_agents])
                for idx, agent in enumerate(self.sim_agents):
                    if idx >= self.num_humans:
                        agent = self.ai_policies[idx - self.num_humans].agent
                        obs = self.ai_policies[idx - self.num_humans].action_state_builder(self.last_obs)
                        ai_action, _, _ = agent.get_action(obs)
                        self.sim_agents[idx].action = action_translation_dict[ai_action.item()]

                action_dict = {}
                for idx, agent in enumerate(self.sim_agents):
                    action_dict[f"agent-{idx + 1}"] = agent.action
                obs, reward, done, info = self.env.step(action_dict)
                self.store["actions"].append([reverse_action_translation_dict[agent.action] for agent in self.sim_agents])
                self.store["rewards"].append(reward)
                self.store["done"].append(done)
                self.last_obs = info["tensor_obs"]

                if done:
                    self._running = False

    def on_execute(self):

        if self.on_init() == False:
            self._running = False

        while self._running:
            for event in pygame.event.get():
                self.on_event(event)
            self.on_render()
        self.on_cleanup()

        return self.store


