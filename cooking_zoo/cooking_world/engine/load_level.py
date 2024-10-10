from cooking_zoo.cooking_world.engine import parsing
from pathlib import Path
from collections import defaultdict
from cooking_zoo.cooking_world.abstract_classes import LinkedObject

import os.path
import json
import copy


def load_new_style_level(world, level_name, num_agents):
    if level_name.endswith(".json"):
        file = level_name
    else:
        my_path = os.path.realpath(__file__)
        dir_name = os.path.dirname(my_path)
        path = Path(dir_name)
        file = path.parent.parent / f"utils/level/{level_name}.json"
    with open(file) as json_file:
        level_object = json.load(json_file)
        json_file.close()
        world.level_object = level_object
    parse_level_object(world, level_object, num_agents)


def parse_level_object(world, level_object, num_agents):
    parsing.parse_level_layout(world, level_object)
    parsing.parse_static_objects(world, level_object)
    parsing.parse_dynamic_objects(world, level_object)
    parsing.parse_agents(world, level_object, num_agents)


def cross_link(world):
    linked_objects = world.abstract_index[LinkedObject]
    for obj in linked_objects:
        for obj2 in linked_objects:
            if obj == obj2:
                continue
            if obj.linked_group_id == obj2.linked_group_id:
                obj.link(obj2)


def load_meta_file(meta_file):
    if meta_file.endswith(".json"):
        file = meta_file
    else:
        my_path = os.path.realpath(__file__)
        dir_name = os.path.dirname(my_path)
        path = Path(dir_name)
        file = path.parent.parent / f"utils/meta_files/{meta_file}.json"
    with open(file) as json_file:
        meta_object = json.load(json_file)
        json_file.close()
    # dictionaries in python are ordered since 3.7
    meta_dict = {list(dic.keys())[0]: list(dic.values())[0] for dic in meta_object}
    return meta_dict


def load_level(world, level, num_agents):
    if world.init_world is not None:
        world.world_objects = defaultdict(list)
        world.abstract_index = defaultdict(list)
        world.world_objects.update(copy.deepcopy(world.init_world))
        world.agents = copy.deepcopy(world.init_agents)
    else:
        load_new_style_level(world, level, num_agents)
        world.abstract_index = defaultdict(list)
        world.init_world = defaultdict(list)
        world.init_world.update(copy.deepcopy(world.world_objects))
        world.init_agents = copy.deepcopy(world.agents)
    world.active_agents = [True] * len(world.agents)
    world.status_changed = [False] * len(world.agents)
    world.relevant_agents = world.compute_relevant_agents()
    world.index_objects()
    cross_link(world)


def reset_world(world, num_agents):
    world.agents = []
    world.agent_store = []
    world.agent_spawn_locations = []
    world.width = 0
    world.height = 0
    world.world_objects = defaultdict(list)
    world.abstract_index = defaultdict(list)
    world.init_world = None
    world.init_agents = []
    world.loaded_object_counter = defaultdict(int)
    world.agent_grace_period = []
    world.active_agents = []
    world.status_changed = []
    world.relevant_agents = []
    parse_level_object(world, world.level_object, num_agents)
    world.active_agents = [True] * len(world.agents)
    world.status_changed = [False] * len(world.agents)
    world.relevant_agents = world.compute_relevant_agents()
    world.index_objects()
    cross_link(world)
