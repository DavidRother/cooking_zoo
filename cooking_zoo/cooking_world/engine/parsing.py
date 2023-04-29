import random
from cooking_zoo.cooking_world.world_objects import *


def parse_level_layout(world, level_object):
    level_layout = level_object["LEVEL_LAYOUT"]
    x = 0
    y = 0
    for y, line in enumerate(iter(level_layout.splitlines())):
        for x, char in enumerate(line):
            if char == "-":
                counter = Counter(location=(x, y))
                world.add_object(counter)
            else:
                floor = Floor(location=(x, y))
                world.add_object(floor)
    world.width = x + 1
    world.height = y + 1


def parse_static_objects(world, level_object):
    static_objects = level_object["STATIC_OBJECTS"]
    for static_object in static_objects:
        name = list(static_object.keys())[0]
        for idx in range(static_object[name]["COUNT"]):
            time_out = 0
            while True:
                try:
                    optional = static_object[name]["OPTIONAL"]
                    if optional <= random.random():
                        break
                except KeyError:
                    pass
                x = random.sample(static_object[name]["X_POSITION"], 1)[0]
                y = random.sample(static_object[name]["Y_POSITION"], 1)[0]
                if x < 0 or y < 0 or x > world.width or y > world.height:
                    raise ValueError(f"Position {x} {y} of object {name} is out of bounds set by the level layout!")
                static_objects_loc = world.get_objects_at((x, y), StaticObject)
                counter = [obj for obj in static_objects_loc if isinstance(obj, Counter)]
                floor = [obj for obj in static_objects_loc if isinstance(obj, Floor)]
                if counter:
                    if len(counter) != 1:
                        raise ValueError("Too many counter in one place detected during initialization")
                    if world.meta_object_information[name] <= world.loaded_object_counter[name]:
                        raise ValueError(f"Too many {name} objects loaded")
                    world.loaded_object_counter[name] += 1
                    world.delete_object(counter[0])
                    obj = StringToClass[name](location=(x, y))
                    try:
                        for key in static_object[name]["ATTRIBUTES"].keys():
                            setattr(obj, key, static_object[name][key])
                    except KeyError:
                        pass
                    world.add_object(obj)
                    break
                elif floor:
                    if len(floor) != 1:
                        raise ValueError("Too many floor tiles in one place detected during initialization")
                    if world.meta_object_information[name] <= world.loaded_object_counter[name]:
                        raise ValueError(f"Too many {name} objects loaded")
                    world.loaded_object_counter[name] += 1
                    world.delete_object(floor[0])
                    obj = StringToClass[name](location=(x, y))
                    try:
                        for key in static_object[name]["ATTRIBUTES"].keys():
                            setattr(obj, key, static_object[name][key])
                    except KeyError:
                        pass
                    world.add_object(obj)
                    break
                else:
                    time_out += 1
                    if time_out > 10000:
                        raise ValueError(f"Can't find valid position for object: "
                                         f"{static_object} in {time_out} steps")
                    continue


def parse_dynamic_objects(world, level_object):
    dynamic_objects = level_object["DYNAMIC_OBJECTS"]
    dynamic_excluded_positions = level_object["DYNAMIC_EXCLUDED_POSITIONS"]
    for dynamic_object in dynamic_objects:
        name = list(dynamic_object.keys())[0]
        for idx in range(dynamic_object[name]["COUNT"]):
            time_out = 0
            while True:
                try:
                    optional = dynamic_object[name]["OPTIONAL"]
                    if optional <= random.random():
                        break
                except KeyError:
                    pass

                x = random.sample(dynamic_object[name]["X_POSITION"], 1)[0]
                y = random.sample(dynamic_object[name]["Y_POSITION"], 1)[0]
                if x < 0 or y < 0 or x > world.width or y > world.height:
                    raise ValueError(f"Position {x} {y} of object {name} is out of bounds set by the level layout!")
                static_objects_loc = world.get_objects_at((x, y), Counter)
                dynamic_objects_loc = world.get_objects_at((x, y), DynamicObject)

                if len(static_objects_loc) == 1 and not dynamic_objects_loc and [x,
                                                                                 y] not in dynamic_excluded_positions:
                    if world.meta_object_information[name] <= world.loaded_object_counter[name]:
                        raise ValueError(f"Too many {name} objects loaded")
                    world.loaded_object_counter[name] += 1
                    obj = StringToClass[name](location=(x, y))
                    world.add_object(obj)
                    static_objects_loc[0].add_content(obj)
                    break
                else:
                    time_out += 1
                    if time_out > 10000:
                        raise ValueError(f"Can't find valid position for object: "
                                         f"{dynamic_object} in {time_out} steps")
                    continue


def parse_agents(world, level_object, num_agents):
    agent_objects = level_object["AGENTS"]
    agent_idx = 0
    for agent_object in agent_objects:
        for idx in range(agent_object["MAX_COUNT"]):
            agent_idx += 1
            if agent_idx > num_agents:
                return
            time_out = 0
            while True:
                x = random.sample(agent_object["X_POSITION"], 1)[0]
                y = random.sample(agent_object["Y_POSITION"], 1)[0]
                if x < 0 or y < 0 or x > world.width or y > world.height:
                    raise ValueError(f"Position {x} {y} of agent is out of bounds set by the level layout!")
                static_objects_loc = world.get_objects_at((x, y), Floor)
                if not any([(x, y) == agent.location for agent in world.agents]) and static_objects_loc:
                    agent = Agent((int(x), int(y)), world.COLORS[len(world.agents)],
                                  'agent-' + str(len(world.agents) + 1))
                    name = "Agent"
                    if world.meta_object_information[name] <= world.loaded_object_counter[name]:
                        raise ValueError(f"Too many {name} objects loaded")
                    world.loaded_object_counter[name] += 1
                    world.agents.append(agent)
                    static_objects_loc[0].add_content(agent)
                    break
                else:
                    time_out += 1
                    if time_out > 1000:
                        raise ValueError(f"Can't find valid position for agent: {agent_object} in {time_out} steps")
