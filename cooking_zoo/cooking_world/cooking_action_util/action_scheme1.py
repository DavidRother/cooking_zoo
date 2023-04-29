from cooking_zoo.cooking_world.world_objects import *


def perform_agent_actions(world, agents, actions):
    for agent, action in zip(agents, actions):
        agent.interacts_with = []
        if action in world.action_scheme.WALK_ACTIONS:
            agent.change_orientation(action)

    cleaned_actions = world.check_inbounds(agents, actions)
    collision_actions = world.check_collisions(agents, cleaned_actions)
    for agent, action in zip(agents, collision_actions):
        perform_agent_action(world, agent, action)


def perform_agent_action(world, agent, action):
    if action in world.action_scheme.WALK_ACTIONS:
        resolve_walking_action(world, agent, action)
    if action in world.action_scheme.INTERACT_ACTIONS:
        resolve_interaction(world, agent, action)


def resolve_walking_action(world, agent, action):
    target_location = world.get_target_location(agent, action)
    if world.square_walkable(target_location):
        origin = world.get_objects_at(agent.location, StaticObject)
        target = world.get_objects_at(target_location, StaticObject)
        agent.move_to(target_location)
        agent.interacts_with = [target[0]]
        origin[0].content = []
        target[0].add_content(agent)


def resolve_interaction(world, agent, action):
    if action == world.action_scheme.INTERACT_PRIMARY:
        world.resolve_primary_interaction(agent)
    elif action == world.action_scheme.INTERACT_PICK_UP_SPECIAL:
        world.resolve_interaction_pick_up_special(agent)
    elif action == world.action_scheme.EXECUTE_ACTION:
        world.resolve_execute_action(agent)
