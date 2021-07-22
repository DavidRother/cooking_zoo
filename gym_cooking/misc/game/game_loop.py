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

    def __init__(self, env, num_humans, ai_policies):
        Game.__init__(self, env.world, env.sim_agents, play=True)
        self.env = env
        self.save_dir = 'misc/game/screenshots'
        self.store = {"actions": [], "tensor_obs": []}
        self.num_humans = num_humans
        self.ai_policies = ai_policies
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
                tensor_obs = self.get_tensor_representation()
                for idx, agent in enumerate(self.sim_agents):
                    if idx >= self.num_humans:
                        agent = self.ai_policies[idx - self.num_humans].agent
                        obs = self.ai_policies[idx - self.num_humans].action_state_builder(tensor_obs)
                        ai_action, _, _ = agent.get_action(obs)
                        self.sim_agents[idx].action = action_translation_dict[ai_action.item()]
                for agent in self.sim_agents:
                    interact(agent, self.world)

                self.env.step()
                self.store["actions"].append([reverse_action_translation_dict[agent.action] for agent in self.sim_agents])
                self.store["tensor_obs"].append(tensor_obs)

            # if event.key in KeyToTuple_human2 and self.num_humans > 1:
            #     action = KeyToTuple_human2[event.key]
            #     self.sim_agents[1].action = action
            #     interact(self.sim_agents[1], self.world)
    def get_tensor_representation(self):
        tensor = np.zeros((self.world.width, self.world.height, len(GAME_OBJECTS)))
        objects = {"Player": self.sim_agents}
        objects.update(self.world.objects)
        for idx, name in enumerate(GAME_OBJECTS):
            try:
                for obj in objects[name]:
                    x, y = obj.location
                    tensor[x, y, idx] += 1
            except KeyError:
                continue
        return tensor

    def on_execute(self):

        if self.on_init() == False:
            self._running = False

        while self._running:
            for event in pygame.event.get():
                self.on_event(event)
            self.on_render()
        self.on_cleanup()


