# modules for game
from gym_cooking.environment.game.game import Game
from gym_cooking.misc.game.utils import *

# helpers
import pygame
import os
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
        assert len(ai_policies) == len(env.unwrapped.world.agents) - num_humans
        if not os.path.exists(self.save_dir):
            os.makedirs(self.save_dir)

    def on_event(self, event):
        if event.type == pygame.QUIT:
            self._running = False
        elif event.type == pygame.KEYDOWN:
            # Save current image
            if event.key == pygame.K_RETURN:
                image_name = '{}_{}.png'.format(self.env.unwrapped.filename, datetime.now().strftime('%m-%d-%y_%H-%M-%S'))
                pygame.image.save(self.screen, '{}/{}'.format(self.save_dir, image_name))
                print('just saved image {} to {}'.format(image_name, self.save_dir))
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
                        ai_policy = self.ai_policies[idx - self.num_humans].agent
                        env_agent = self.env.unwrapped.world_agent_to_env_agent_mapping[agent]
                        last_obs_raw = self.last_obs[env_agent]
                        obs = self.ai_policies[idx - self.num_humans].action_state_builder(last_obs_raw)
                        ai_action, _, _ = ai_policy.get_action(obs)
                        store_action_dict[agent] = ai_action.item()
                        self.env.unwrapped.world.agents[idx].action = action_translation_dict[ai_action.item()]

                observations, rewards, dones, infos = \
                    self.env.step({agent: reverse_action_translation_dict[
                        self.env.unwrapped.world_agent_mapping[agent].action] for agent in self.env.agents})

                self.store["actions"].append(store_action_dict)
                self.store["info"].append(infos)
                self.store["rewards"].append(rewards)
                self.store["done"].append(dones)
                self.last_obs = observations

                if all(dones.values()):
                    self._running = False

    def on_execute(self):
        self._running = self.on_init()

        while self._running:
            for event in pygame.event.get():
                self.on_event(event)
            self.on_render()
        self.on_cleanup()

        return self.store


