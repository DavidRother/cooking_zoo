from cooking_zoo.cooking_world.world_objects import *


def perform_agent_actions(world, agents, actions):
    target_locations = []
    for agent, action in zip(agents, actions):
        agent.interacts_with = []
        if action in world.action_scheme.WALK_ACTIONS:
            target_locations.append(world.get_target_location(agent, action))
            agent.change_orientation(action)
        else:
            target_locations.append(agent.location)
    cleaned_actions = world.check_inbounds(agents, actions)
    collision_actions = world.check_collisions(agents, cleaned_actions)
    for agent, action, target_location in zip(agents, collision_actions, target_locations):
        perform_agent_action(world, agent, action, target_location)


def perform_agent_action(world, agent, action, target_location):
    orig_location = agent.location
    resolve_walking_action(world, agent, action)
    if orig_location is agent.location and action != 0:
        resolve_interaction(world, agent, target_location)


def resolve_walking_action(world, agent, action):
    target_location = world.get_target_location(agent, action)
    if world.square_walkable(target_location):
        origin = world.get_objects_at(agent.location, StaticObject)
        target = world.get_objects_at(target_location, StaticObject)
        agent.move_to(target_location)
        agent.interacts_with = [target[0]]
        origin[0].content = []
        target[0].add_content(agent)


def resolve_interaction(world, agent, target_location):
    target = world.get_objects_at(target_location, StaticObject)
    dynamic_objects = world.get_objects_at(target_location, DynamicObject)
    if isinstance(target[0], ActionObject) and any([not d.done() for d in dynamic_objects]):
        world.resolve_execute_action(agent)
    else:
        world.resolve_primary_interaction(agent)
