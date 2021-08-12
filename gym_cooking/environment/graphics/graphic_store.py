import numpy as np
from gym_cooking.cooking_world.world_objects import *
from collections import namedtuple


GraphicScaling = namedtuple("GraphicScaling", ["holding_scale", "container_scale"])


class GraphicStore:

    OBJECT_PROPERTIES = {Blender: GraphicScaling(None, 0.5)}

    def __init__(self, world_height, world_width):
        self.scale = 80  # num pixels per tile
        self.holding_scale = 0.5
        self.container_scale = 0.7
        self.width = self.scale * world_width
        self.height = self.scale * world_height
        self.tile_size = (self.scale, self.scale)
        self.holding_size = tuple((self.holding_scale * np.asarray(self.tile_size)).astype(int))
        self.container_size = tuple((self.container_scale * np.asarray(self.tile_size)).astype(int))
        self.holding_container_size = tuple((self.container_scale * np.asarray(self.holding_size)).astype(int))


