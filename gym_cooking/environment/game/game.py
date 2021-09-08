import os
from gym_cooking.misc.game.utils import *
from gym_cooking.cooking_world.world_objects import *

from collections import defaultdict

import pygame
import numpy as np

import os.path
import pathlib

os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = 'hide'

graphics_dir = 'misc/game/graphics'
_image_library = {}


def get_image(path):
    global _image_library
    image = _image_library.get(path)
    if image == None:
        canonicalized_path = path.replace('/', os.sep).replace('\\', os.sep)
        image = pygame.image.load(canonicalized_path)
        _image_library[path] = image
    return image


class Game:

    def __init__(self, env, play=False):
        self._running = True
        self.env = env
        self.play = play
        self.screen = None

        # Visual parameters
        self.scale = 80  # num pixels per tile
        self.holding_scale = 0.5
        self.container_scale = 0.7
        self.width = self.scale * self.env.unwrapped.world.width
        self.height = self.scale * self.env.unwrapped.world.height
        self.tile_size = (self.scale, self.scale)
        self.holding_size = tuple((self.holding_scale * np.asarray(self.tile_size)).astype(int))
        self.container_size = tuple((self.container_scale * np.asarray(self.tile_size)).astype(int))
        self.holding_container_size = tuple((self.container_scale * np.asarray(self.holding_size)).astype(int))
        # self.font = pygame.font.SysFont('arialttf', 10)
        my_path = os.path.realpath(__file__)
        dir_name = os.path.dirname(my_path)
        path = pathlib.Path(dir_name)
        root = path.parent.parent
        self.root_dir = root

    def on_init(self):
        pygame.init()
        if self.play:
            self.screen = pygame.display.set_mode((self.width, self.height))
        else:
            # Create a hidden surface
            self.screen = pygame.Surface((self.width, self.height))
        return True

    def on_event(self, event):
        if event.type == pygame.QUIT:
            self._running = False

    def on_render(self):
        self.screen.fill(Color.FLOOR)

        self.draw_static_objects()

        self.draw_agents()

        self.draw_dynamic_objects()

        if self.play:
            pygame.display.flip()
            pygame.display.update()

    def draw_static_objects(self):
        objects = self.env.unwrapped.world.get_object_list()
        static_objects = [obj for obj in objects if isinstance(obj, StaticObject)]
        for static_object in static_objects:
            self.draw_static_object(static_object)

    def draw_static_object(self, static_object: StaticObject):
        sl = self.scaled_location(static_object.location)
        fill = pygame.Rect(sl[0], sl[1], self.scale, self.scale)
        if isinstance(static_object, Counter):
            pygame.draw.rect(self.screen, Color.COUNTER, fill)
            pygame.draw.rect(self.screen, Color.COUNTER_BORDER, fill, 1)
        elif isinstance(static_object, DeliverSquare):
            pygame.draw.rect(self.screen, Color.DELIVERY, fill)
            self.draw('delivery', self.tile_size, sl)
        elif isinstance(static_object, CutBoard):
            pygame.draw.rect(self.screen, Color.COUNTER, fill)
            pygame.draw.rect(self.screen, Color.COUNTER_BORDER, fill, 1)
            self.draw('cutboard', self.tile_size, sl)
        elif isinstance(static_object, Blender):
            pygame.draw.rect(self.screen, Color.COUNTER, fill)
            pygame.draw.rect(self.screen, Color.COUNTER_BORDER, fill, 1)
            self.draw('blender3', self.tile_size, sl)
        # elif isinstance(static_object, Floor):
        #     pygame.draw.rect(self.screen, Color.FLOOR, fill)

    def draw_dynamic_objects(self):
        objects = self.env.unwrapped.world.get_object_list()
        dynamic_objects = [obj for obj in objects if isinstance(obj, DynamicObject)]
        dynamic_objects_grouped = defaultdict(list)
        for obj in dynamic_objects:
            dynamic_objects_grouped[obj.location].append(obj)
        for location, obj_list in dynamic_objects_grouped.items():
            if any([agent.location == location for agent in self.env.unwrapped.world.agents]):
                self.draw_dynamic_object_stack(obj_list, self.holding_size, self.holding_location(location),
                                               self.holding_container_size, self.holding_container_location(location))
            else:
                self.draw_dynamic_object_stack(obj_list, self.tile_size, self.scaled_location(location),
                                               self.container_size, self.container_location(location))

    def draw_dynamic_object_stack(self, dynamic_objects, base_size, base_location, holding_size, holding_location):
        highest_order_object = self.env.unwrapped.world.get_highest_order_object(dynamic_objects)
        if isinstance(highest_order_object, Container):
            self.draw('Plate', base_size, base_location)
            rest_stack = [obj for obj in dynamic_objects if obj != highest_order_object]
            if rest_stack:
                file_name = self.get_file_name(rest_stack)
                self.draw(file_name, holding_size, holding_location)
        else:
            file_name = self.get_file_name(dynamic_objects)
            self.draw(file_name, base_size, base_location)

    def draw_agents(self):
        for agent in self.env.unwrapped.world.agents:
            self.draw('agent-{}'.format(agent.color), self.tile_size, self.scaled_location(agent.location))

    def draw(self, path, size, location):
        image_path = f'{self.root_dir}/{graphics_dir}/{path}.png'
        image = pygame.transform.scale(get_image(image_path), size)
        self.screen.blit(image, location)

    def draw_agent_object(self, obj):
        # Holding shows up in bottom right corner.
        if obj is None:
            return
        if any([isinstance(c, Plate) for c in obj.contents]):
            self.draw('Plate', self.holding_size, self.holding_location(obj.location))
            if len(obj.contents) > 1:
                plate = obj.unmerge('Plate')
                self.draw(obj.full_name, self.holding_container_size, self.holding_container_location(obj.location))
                obj.merge(plate)
        else:
            self.draw(obj.full_name, self.holding_size, self.holding_location(obj.location))

    def draw_object(self, obj):
        if obj is None:
            return
        if any([isinstance(c, Plate) for c in obj.contents]):
            self.draw('Plate', self.tile_size, self.scaled_location(obj.location))
            if len(obj.contents) > 1:
                plate = obj.unmerge('Plate')
                self.draw(obj.full_name, self.container_size, self.container_location(obj.location))
                obj.merge(plate)
        else:
            self.draw(obj.full_name, self.tile_size, self.scaled_location(obj.location))

    @staticmethod
    def get_file_name(dynamic_objects):
        order = [Lettuce, Onion, Tomato, Carrot]
        name = []
        for order_type in order:
            for obj in dynamic_objects:
                if isinstance(obj, order_type):
                    name.append(obj.state.value + obj.name())
                    break
        return '-'.join(name)

    def scaled_location(self, loc):
        """Return top-left corner of scaled location given coordinates loc, e.g. (3, 4)"""
        return tuple(self.scale * np.asarray(loc))

    def holding_location(self, loc):
        """Return top-left corner of location where agent holding will be drawn (bottom right corner)
        given coordinates loc, e.g. (3, 4)"""
        scaled_loc = self.scaled_location(loc)
        return tuple((np.asarray(scaled_loc) + self.scale * (1 - self.holding_scale)).astype(int))

    def container_location(self, loc):
        """Return top-left corner of location where contained (i.e. plated) object will be drawn,
        given coordinates loc, e.g. (3, 4)"""
        scaled_loc = self.scaled_location(loc)
        return tuple((np.asarray(scaled_loc) + self.scale * (1 - self.container_scale) / 2).astype(int))

    def holding_container_location(self, loc):
        """Return top-left corner of location where contained, held object will be drawn
        given coordinates loc, e.g. (3, 4)"""
        scaled_loc = self.scaled_location(loc)
        factor = (1 - self.holding_scale) + (1 - self.container_scale) / 2 * self.holding_scale
        return tuple((np.asarray(scaled_loc) + self.scale * factor).astype(int))

    def on_cleanup(self):
        # pygame.display.quit()
        pygame.quit()
