from cooking_zoo.cooking_world.world_objects import *
from cooking_zoo.cooking_world.actions import *


def perform_agent_actions(world, agents, actions):
    for agent, action in zip(agents, actions):
        agent.interacts_with = []
        if action in world.action_scheme.WALK_ACTIONS:
            if action in [ActionScheme2.TURN_LEFT, ActionScheme2.TURN_RIGHT]:
                agent.change_orientation(world.agent_turn_map[(agent.orientation, action)])

    cleaned_actions = world.check_inbounds(agents, actions)
    collision_actions = world.check_collisions(agents, cleaned_actions)
    for agent, action in zip(agents, collision_actions):
        world.perform_agent_action(agent, action)


def perform_agent_action(world, agent: Agent, action):
    if action in world.action_scheme.WALK_ACTIONS:
        world.resolve_walking_action(agent, action)
    if action in world.action_scheme.INTERACT_ACTIONS:
        world.resolve_interaction(agent, action)


def resolve_walking_action(world, agent: Agent, action):
    if action == ActionScheme2.WALK:
        target_location = world.get_target_location_scheme2(agent)
    else:
        return
    if world.square_walkable(target_location):
        origin = world.get_objects_at(agent.location, StaticObject)
        target = world.get_objects_at(target_location, StaticObject)
        agent.move_to(target_location)
        agent.interacts_with = [target[0]]
        origin[0].content = []
        target[0].add_content(agent)


def resolve_interaction(world, agent: Agent, action):
    if action == world.action_scheme.INTERACT_PRIMARY:
        world.resolve_primary_interaction(agent)
    elif action == world.action_scheme.INTERACT_PICK_UP_SPECIAL:
        world.resolve_interaction_pick_up_special(agent)
    elif action == world.action_scheme.EXECUTE_ACTION:
        world.resolve_execute_action(agent)
