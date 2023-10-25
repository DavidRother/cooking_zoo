import numpy as np
from cooking_zoo.cooking_world.world_objects import *


def _random_valid_index(rng, condition):
    shape = condition.shape
    return np.unravel_index(rng.choice(np.flatnonzero(condition)), shape)


def _str_grid_to_array(string):
    """Converts a string-grid into a numpy char array"""
    return np.array(
        [list(line) for line in string.splitlines()]
    ).T


def _get_floor_mask(world):
    shape = (world.width, world.height)
    floor_mask = np.zeros(shape, dtype=bool)
    floors = world.world_objects["Floor"]
    for floor in floors:
        floor_mask[floor.location] = True
    return floor_mask


def _set_obj_attributes(obj, attributes):
    for key, val in attributes.items():
        if key == "states":
            # handle states separately due to enum
            for state in val:
                enum_state = globals()[state.type](state.state)
                setattr(obj, state.attr, enum_state)
        else:
            setattr(obj, key, val)


def parse_level_layout(world, level_config, rng, global_rng_group=0):
    # Generate an array for the floor layout
    local_rng_group = None
    total_layout = None
    for floor_config in level_config.floor.configs:
        current_layout = _str_grid_to_array(floor_config.layout)
        if total_layout is None:
            total_layout = np.zeros(current_layout.shape, dtype=bool)
        # Handle hardcoded layout ('X')
        total_layout[current_layout=='X'] = True
        # Handle randoms. Can throw error if no valid spawn location possible
        if not np.all(np.isin(current_layout, ['X','.'])):
            current_rng_group = (global_rng_group
                                 if floor_config.get("rng", "local") == "global" else
                                 local_rng_group)
            if current_rng_group is None:
                rnd_loc = _random_valid_index(rng,
                        np.isin(current_layout, list("*0123456789"))
                        & ~total_layout
                     )
                if (group := current_layout[rnd_loc]) != '*':
                    local_rng_group = group # collapsed the local rng group
            else:
                rnd_loc = _random_valid_index(rng,
                        np.isin(current_layout, ['*', current_rng_group])
                        & ~total_layout
                     )
            total_layout[rnd_loc] = True
    # then, set objects
    world.width, world.height = total_layout.shape
    for loc, is_counter in np.ndenumerate(total_layout):
        world.add_object(
                Counter(location=loc) if is_counter
                else Floor(location=loc)
            )


def parse_static_objects(world, level_config, rng, blocked_locations=None, global_rng_group=0):
    local_rng_group = None
    for obj_config in level_config.static_objects.configs:
        if obj_config.get("prob", 1.0) < rng.random():
            continue
        obj_name = obj_config.type
        current_layout = _str_grid_to_array(obj_config.layout)
        if blocked_locations is None:
            blocked_locations = np.zeros(current_layout.shape, dtype=bool)
        current_rng_group = (global_rng_group
                             if obj_config.get("rng", "local") == "global" else
                             local_rng_group)
        if current_rng_group is None:
            rnd_loc = _random_valid_index(rng,
                    np.isin(current_layout, list("*0123456789"))
                    & ~blocked_locations
                 )
            if (group := current_layout[rnd_loc]) != '*':
                local_rng_group = group # collapsed the local rng group
        else:
            rnd_loc = _random_valid_index(rng,
                    np.isin(current_layout, ['*', current_rng_group])
                    & ~blocked_locations
                  )
        # Initalise the object & replace existing floor/counter
        obj_to_delete = None
        if (counters := world.get_objects_at(rnd_loc, Counter)):
            assert (len(counters) == 1), \
                    f"Expected 1 counter at {rnd_loc} (got {len(counters)})"
            obj_to_delete = counters[0]
        if (floors := world.get_objects_at(rnd_loc, Floor)):
            assert (len(floors) == 1), \
                    f"Expected 1 floor object at {rnd_loc} (got {len(floors)})"
            obj_to_delete = floors[0]
        if obj_to_delete:
            # We found a counter or floor tile as expected.
            # Now replace it with the static object.
            if world.meta_object_information[obj_name] <= world.loaded_object_counter[obj_name]:
                raise ValueError(f"Too many {obj_name} objects loaded")
            world.loaded_object_counter[obj_name] += 1
            world.delete_object(obj_to_delete)
            obj = StringToClass[obj_name](location=rnd_loc)
            for key, val in obj_config.get("attributes", {}).items():
                setattr(obj, key, val)
            world.add_object(obj)
            blocked_locations[rnd_loc] = True
        else:
            raise ValueError(f"Expected a floor or counter at {rnd_loc}")


def parse_dynamic_objects(world, level_config, rng, blocked_locations=None, global_rng_group=0):
    local_rng_group = None
    for obj_config in level_config.dynamic_objects.configs:
        if obj_config.get("prob", 1.0) < rng.random():
            continue
        # create the object already: we'll use this to check valid locations
        obj_name = obj_config.type
        obj = StringToClass[obj_name](location=(0,0))
        _set_obj_attributes(obj, obj_config.get("attributes", {}))
        current_layout = _str_grid_to_array(obj_config.layout)
        current_rng_group = (global_rng_group
                             if obj_config.get("rng", "local") == "global" else
                             local_rng_group)
        candidate_locations = ((current_layout=='*')
                               | (current_layout==current_rng_group))
        if current_rng_group is None:
            candidate_locations = np.isin(current_layout, list("*0123456789"))
        else:
            candidate_locations = np.isin(current_layout, ['*', current_rng_group])
        # Check if each candidate location:
        for flat_idx in np.flatnonzero(candidate_locations):
            loc = np.unravel_index(flat_idx, candidate_locations.shape)
            placed = False
            # Check if any dynamic object accept the new object
            for existing_obj in world.get_objects_at(loc, DynamicObject):
                if (hasattr(existing_obj, "accepts")
                    and existing_obj.accepts(obj)):
                    placed = True
                    break
            # Check if any static object accept the new object
            if not placed:
                for existing_obj in world.get_objects_at(loc, StaticObject):
                    if (hasattr(existing_obj, "accepts")
                        and existing_obj.accepts(obj)):
                        placed = True
                        break
            candidate_locations[loc] = placed
        # Generate a random location and spawn the object
        rnd_loc = _random_valid_index(rng, candidate_locations)
        if (current_rng_group is None) and (group := current_layout[rnd_loc]):
            local_rng_group = group # collapsed the local rng group
        obj.location = rnd_loc
        dynamic_objects = world.get_objects_at(rnd_loc, DynamicObject)
        static_objects = world.get_objects_at(rnd_loc, StaticObject)
        placed = False
        for existing_obj in dynamic_objects:
            if (hasattr(existing_obj, "accepts")
                and existing_obj.accepts(obj)):
                world.add_object(obj)
                existing_obj.add_content(obj)
                placed = True
                break
        if not placed:
            for existing_obj in static_objects:
                if (hasattr(existing_obj, "accepts")
                    and existing_obj.accepts(obj)):
                    world.add_object(obj)
                    existing_obj.add_content(obj)
                    placed = True
                    break
        if world.meta_object_information[obj_name] <= world.loaded_object_counter[obj_name]:
            raise ValueError(f"Too many {obj_name} objects loaded")
        world.loaded_object_counter[obj_name] += 1


def parse_agents(world, level_config, rng, num_agents, blocked_locations=None, global_rng_group=0):
    agents_spawned = 0
    local_rng_group = None
    for agent_config in level_config.agents.configs:
        if agents_spawned >= num_agents:
            return
        if agent_config.get("prob", 1.0) < rng.random():
            continue
        current_layout = _str_grid_to_array(agent_config.layout)
        if blocked_locations is None:
            # agents can only spawn on the floor
            blocked_locations = ~_get_floor_mask(world)
        current_rng_group = (global_rng_group
                             if agent_config.get("rng", "local") == "global" else
                             local_rng_group)
        if current_rng_group is None:
            rnd_loc = _random_valid_index(rng,
                    np.isin(current_layout, list("*0123456789"))
                    & ~blocked_locations
                 )
            if (group := current_layout[rnd_loc]) != '*':
                local_rng_group = group # collapsed the local rng group
                current_rng_group = local_rng_group
        else:
            rnd_loc = _random_valid_index(rng,
                    np.isin(current_layout, ['*', current_rng_group])
                    & ~blocked_locations
                  )
        # Initialise the agent
        agent = Agent(rnd_loc,
                      world.COLORS[len(world.agents)],
                      'agent-' + str(len(world.agents) + 1)
                      )
        name = "Agent"
        if world.meta_object_information[name] <= world.loaded_object_counter[name]:
            raise ValueError(f"Too many {name} objects loaded")
        world.loaded_object_counter[name] += 1
        world.agents.append(agent)
        world.agent_store.append(agent)
        world.agent_grace_period.append(world.grace_period)
        world.active_agents.append(True)
        world.status_changed.append(False)
        world.agent_spawn_locations.append(
            list(zip(*np.unravel_index(np.flatnonzero(
                    np.isin(current_layout, ['*', current_rng_group])
                    ),
                    (world.width, world.height))
            )))
        floor = world.get_objects_at(rnd_loc, Floor)[0]
        floor.add_content(agent)
        agents_spawned += 1
        blocked_locations[rnd_loc] = True


def generate_location(world, possible_spawn_locations, rng):
    valid_spawn_locations = []
    for proposed_spawn_location in possible_spawn_locations:
        floor = world.get_objects_at(proposed_spawn_location, Floor)
        if (not any([proposed_spawn_location == agent.location
                    for agent in world.agents])
            and floor):
            valid_spawn_locations.append(proposed_spawn_location)
    return rng.choice(valid_spawn_locations)
