# modules for game
from gym_cooking.environment.game.game import Game
from gym_cooking.misc.game.utils import *

# helpers
import pygame
import os
from time import sleep
from datetime import datetime
from collections import defaultdict


action_translation_dict = {0: (0, 0), 1: (1, 0), 2: (0, 1), 3: (-1, 0), 4: (0, -1)}
reverse_action_translation_dict = {(0, 0): 0, (1, 0): 1, (0, 1): 2, (-1, 0): 3, (0, -1): 4}


class GamePlay(Game):

    def __init__(self, env, num_humans, ai_policies, max_steps=100):
        Game.__init__(self, env, play=True)
        self.env = env
        self.save_dir = 'misc/game/screenshots'
        self.store = defaultdict(list)
        self.num_humans = num_humans
        self.ai_policies = ai_policies
        self.max_steps = max_steps
        self.current_step = 0
        self.last_obs = env.reset()
        self.step_done = False
        self.yielding_action_dict = {}
        assert len(ai_policies) == len(env.unwrapped.world.agents) - num_humans
        if not os.path.exists(self.save_dir):
            os.makedirs(self.save_dir)

    def on_event(self, event):
        self.step_done = False
        if event.type == pygame.QUIT:
            self._running = False
        elif event.type == pygame.KEYDOWN:
            # Save current image
            if event.key == pygame.K_RETURN:
                image_name = '{}_{}.png'.format(self.env.unwrapped.filename, datetime.now().strftime('%m-%d-%y_%H-%M-%S'))
                pygame.image.save(self.screen, '{}/{}'.format(self.save_dir, image_name))
                print('Saved image {} to {}'.format(image_name, self.save_dir))
                return

            # Control current human agent
            if event.key in KeyToTuple_human1 and self.num_humans > 0:
                store_action_dict = {}
                action = KeyToTuple_human1[event.key]
                self.env.unwrapped.world.agents[0].action = action
                store_action_dict[self.env.unwrapped.world.agents[0]] = action
                self.store["observation"].append(self.last_obs)
                self.store["agent_states"].append([agent.location for agent in self.env.unwrapped.world.agents])
                for idx, agent in enumerate(self.env.unwrapped.world.agents):
                    if idx >= self.num_humans:
                        ai_policy = self.ai_policies[idx - self.num_humans]
                        env_agent = self.env.unwrapped.world_agent_to_env_agent_mapping[agent]
                        last_obs_raw = self.last_obs[env_agent]
                        ai_action = ai_policy.get_action(last_obs_raw)
                        store_action_dict[agent] = ai_action
                        self.env.unwrapped.world.agents[idx].action = action_translation_dict[ai_action]

                self.yielding_action_dict = {agent: reverse_action_translation_dict[
                    self.env.unwrapped.world_agent_mapping[agent].action] for agent in self.env.agents}
                observations, rewards, dones, infos = self.env.step(self.yielding_action_dict)

                self.store["actions"].append(store_action_dict)
                self.store["info"].append(infos)
                self.store["rewards"].append(rewards)
                self.store["done"].append(dones)
                self.last_obs = observations

                if all(dones.values()):
                    self._running = False

                self.step_done = True

    def ai_only_event(self):
        self.step_done = False

        store_action_dict = {}

        for idx, agent in enumerate(self.env.unwrapped.world.agents):
            if idx >= self.num_humans:
                ai_policy = self.ai_policies[idx - self.num_humans].agent
                env_agent = self.env.unwrapped.world_agent_to_env_agent_mapping[agent]
                last_obs_raw = self.last_obs[env_agent]
                obs = self.ai_policies[idx - self.num_humans].action_state_builder(last_obs_raw)
                ai_action, _, _ = ai_policy.get_action(obs)
                store_action_dict[agent] = ai_action.item()
                self.env.unwrapped.world.agents[idx].action = action_translation_dict[ai_action.item()]

        self.yielding_action_dict = {agent: reverse_action_translation_dict[
            self.env.unwrapped.world_agent_mapping[agent].action] for agent in self.env.agents}
        # print(self.yielding_action_dict)
        observations, rewards, dones, infos = self.env.step(self.yielding_action_dict)

        if all(dones.values()):
            self._running = False

        self.step_done = True

    def on_execute(self):
        self._running = self.on_init()

        while self._running:
            for event in pygame.event.get():
                self.on_event(event)
            self.on_render()
        self.on_cleanup()

        return self.store

    def on_execute_yielding(self):
        self._running = self.on_init()

        while self._running:
            for event in pygame.event.get():
                self.on_event(event)
            self.on_render()
            if self.step_done:
                self.step_done = False
                yield self.store["observation"][-1], self.store["done"][-1], self.store["info"][-1], \
                      self.store["rewards"][-1], self.yielding_action_dict
        self.on_cleanup()

    def on_execute_ai_only_with_delay(self):
        self._running = self.on_init()

        while self._running:
            sleep(0.4)
            self.ai_only_event()
            self.on_render()
        self.on_cleanup()

        return self.store


