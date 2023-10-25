from cooking_zoo.cooking_world.engine import parsing
from pathlib import Path
from collections import defaultdict
from cooking_zoo.cooking_world.abstract_classes import LinkedObject

import os.path
import json
import copy

from omegaconf import OmegaConf
from omegaconf.dictconfig import DictConfig
import numpy as np


def load_new_style_level(world, level, num_agents, rng):
    if isinstance(level, str):
        if level.endswith(".yaml"):
            level_object = OmegaConf.load(level)
        else:
            my_path = os.path.realpath(__file__)
            dir_name = os.path.dirname(my_path)
            path = Path(dir_name)
            file = path.parent.parent / f"utils/level/{level}.yaml"
            level_object = OmegaConf.load(file)
    elif isinstance(level, DictConfig):
        level_object = level
    else:
        raise ValueError(f"Unexpected level specification ({type(level)})")

    world.meta_object_information = level_object.meta_object_information
    parsing.parse_level_layout(world, level_object, rng)
    parsing.parse_static_objects(world, level_object, rng)
    parsing.parse_dynamic_objects(world, level_object, rng)
    parsing.parse_agents(world, level_object, rng, num_agents)


def cross_link(world):
    linked_objects = world.abstract_index[LinkedObject]
    for obj in linked_objects:
        for obj2 in linked_objects:
            if obj == obj2:
                continue
            if obj.linked_group_id == obj2.linked_group_id:
                obj.link(obj2)


def load_level(world, level, num_agents, rng):
    if world.init_world is not None:
        world.world_objects = defaultdict(list)
        world.abstract_index = defaultdict(list)
        world.world_objects.update(copy.deepcopy(world.init_world))
        world.agents = copy.deepcopy(world.init_agents)
    else:
        load_new_style_level(world, level, num_agents, rng)
        world.abstract_index = defaultdict(list)
        world.init_world = defaultdict(list)
        world.init_world.update(copy.deepcopy(world.world_objects))
        world.init_agents = copy.deepcopy(world.agents)
    world.active_agents = [True] * len(world.agents)
    world.status_changed = [False] * len(world.agents)
    world.relevant_agents = world.compute_relevant_agents()
    world.index_objects()
    cross_link(world)
