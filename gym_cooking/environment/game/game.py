import os
from gym_cooking.environment.game import graphic_pipeline
from gym_cooking.misc.game.utils import *

import pygame

import os.path
from collections import defaultdict
from datetime import datetime
from time import sleep


os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = 'hide'


class Game:

    def __init__(self, env, num_humans, ai_policies, max_steps=100, render=False):
        self._running = True
        self.env = env
        self.play = bool(num_humans)
        self.render = render or self.play
        # Visual parameters
        self.graphics_pipeline = graphic_pipeline.GraphicPipeline(env, self.render)
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

    def on_init(self):
        pygame.init()
        self.graphics_pipeline.on_init()
        return True

    def on_event(self, event):
        self.step_done = False
        if event.type == pygame.QUIT:
            self._running = False
        elif event.type == pygame.KEYDOWN:
            # Save current image
            if event.key == pygame.K_RETURN:
                image_name = '{}_{}.png'.format(self.env.unwrapped.filename, datetime.now().strftime('%m-%d-%y_%H-%M-%S'))
                pygame.image.save(self.graphics_pipeline.screen, '{}/{}'.format(self.save_dir, image_name))
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
                        self.env.unwrapped.world.agents[idx].action = ai_action

                self.yielding_action_dict = {agent: self.env.unwrapped.world_agent_mapping[agent].action
                                             for agent in self.env.agents}
                observations, rewards, dones, infos = self.env.step(self.yielding_action_dict)

                self.store["actions"].append(store_action_dict)
                self.store["info"].append(infos)
                self.store["rewards"].append(rewards)
                self.store["done"].append(dones)

                if all(dones.values()):
                    self._running = False

                self.last_obs = observations
                self.step_done = True

    def ai_only_event(self):
        self.step_done = False

        store_action_dict = {}

        self.store["observation"].append(self.last_obs)
        self.store["agent_states"].append([agent.location for agent in self.env.unwrapped.world.agents])
        for idx, agent in enumerate(self.env.unwrapped.world.agents):
            if idx >= self.num_humans:
                ai_policy = self.ai_policies[idx - self.num_humans].agent
                env_agent = self.env.unwrapped.world_agent_to_env_agent_mapping[agent]
                last_obs_raw = self.last_obs[env_agent]
                ai_action = ai_policy.get_action(last_obs_raw)
                store_action_dict[agent] = ai_action
                self.env.unwrapped.world.agents[idx].action = ai_action

        self.yielding_action_dict = {agent: self.env.unwrapped.world_agent_mapping[agent].action
                                     for agent in self.env.agents}
        observations, rewards, dones, infos = self.env.step(self.yielding_action_dict)

        self.store["actions"].append(store_action_dict)
        self.store["info"].append(infos)
        self.store["rewards"].append(rewards)
        self.store["done"].append(dones)

        if all(dones.values()):
            self._running = False

        self.last_obs = observations
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
            sleep(0.2)
            self.ai_only_event()
            self.on_render()
        self.on_cleanup()

        return self.store

    def on_render(self):
        self.graphics_pipeline.on_render()

    @staticmethod
    def on_cleanup():
        # pygame.display.quit()
        pygame.quit()

    def get_image_obs(self):
        return self.graphics_pipeline.get_image_obs()

    def save_image_obs(self, t):
        self.graphics_pipeline.save_image_obs(t)

