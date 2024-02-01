from collections import defaultdict
from cooking_zoo.cooking_world.world_objects import *
from cooking_zoo.cooking_world.actions import *
from cooking_zoo.cooking_world.cooking_action_util import action_scheme1, action_scheme2, action_scheme3
from cooking_zoo.cooking_world.engine import load_level, parsing
import numpy as np


class CookingWorld:

    LEFT = 1
    RIGHT = 2
    DOWN = 3
    UP = 4

    agent_turn_map = {(LEFT, ActionScheme2.TURN_LEFT): DOWN, (RIGHT, ActionScheme2.TURN_LEFT): UP,
                      (UP, ActionScheme2.TURN_LEFT): LEFT, (DOWN, ActionScheme2.TURN_LEFT): RIGHT,
                      (RIGHT, ActionScheme2.TURN_RIGHT): DOWN, (LEFT, ActionScheme2.TURN_RIGHT): UP,
                      (UP, ActionScheme2.TURN_RIGHT): RIGHT, (DOWN, ActionScheme2.TURN_RIGHT): LEFT}

    COLORS = ['blue', 'magenta', 'yellow', 'green']

    def __init__(self, action_scheme_class=ActionScheme1, meta_file="", recipes=None, agent_respawn_rate=0.0,
                 grace_period=20, agent_despawn_rate=0.0):
        self.agents = []
        self.agent_store = []
        self.agent_spawn_locations = []
        self.width = 0
        self.height = 0
        self.world_objects = defaultdict(list)
        self.abstract_index = defaultdict(list)
        self.action_scheme = action_scheme_class
        self.init_world = None
        self.init_agents = []
        self.meta_object_information = load_level.load_meta_file(meta_file)
        self.loaded_object_counter = defaultdict(int)
        self.recipes = recipes or []
        self.agent_respawn_rate = agent_respawn_rate
        self.agent_despawn_rate = agent_despawn_rate
        self.grace_period = grace_period
        self.agent_grace_period = []
        self.active_agents = []
        self.status_changed = []
        self.relevant_agents = []

    def add_object(self, obj):
        self.world_objects[type(obj).__name__].append(obj)

    def delete_object(self, obj):
        self.world_objects[type(obj).__name__].remove(obj)

    def index_objects(self):
        for type_name, obj_list in self.world_objects.items():
            for abstract_class in ABSTRACT_GAME_CLASSES:
                if issubclass(StringToClass[type_name], abstract_class):
                    self.abstract_index[abstract_class].extend(obj_list)

    def delete_from_index(self, obj):
        for abstract_class in ABSTRACT_GAME_CLASSES:
            if isinstance(obj, abstract_class):
                try:
                    self.abstract_index[abstract_class].remove(obj)
                except ValueError:
                    pass

    def add_to_index(self, obj):
        for abstract_class in ABSTRACT_GAME_CLASSES:
            if isinstance(obj, abstract_class):
                self.abstract_index[abstract_class].append(obj)

    def get_object_list(self):
        object_list = []
        for value in self.world_objects.values():
            object_list.extend(value)
        return object_list

    def progress_world(self):
        obj_list_deleted = []
        obj_list_created = []
        for obj in self.abstract_index[ProcessingObject]:
            creation, deletion = obj.process()
            obj_list_deleted.extend(deletion)
            obj_list_created.extend(creation)
        for obj in self.abstract_index[ProgressingObject]:
            creation, deletion = obj.progress()
            obj_list_deleted.extend(deletion)
            obj_list_created.extend(creation)
        for obj in self.abstract_index[ContentObject]:
            if len(obj.content) > 0:
                for c in obj.content:
                    if hasattr(c, "free"):
                        c.free = False
                if hasattr(obj.content[-1], 'free'):
                    obj.content[-1].free = True

        self.handle_object_deletion(obj_list_deleted)
        self.handle_object_creation(obj_list_created)

    def resolve_linked_interactions(self):
        for obj in self.abstract_index[LinkedObject]:
            obj.process_linked_objects()

    def perform_agent_actions(self, agents, actions):
        if self.action_scheme == ActionScheme1:
            action_scheme1.perform_agent_actions(self, agents, actions)
        elif self.action_scheme == ActionScheme2:
            action_scheme2.perform_agent_actions(self, agents, actions)
        elif self.action_scheme == ActionScheme3:
            action_scheme3.perform_agent_actions(self, agents, actions)
        else:
            raise Exception("No valid Action Scheme Found")

    def world_step(self, actions):
        agents = self.compute_active_agents()
        self.status_changed = [False] * len(self.agents)
        assert len(agents) == len(actions)
        self.perform_agent_actions(agents, actions)
        self.progress_world()
        self.resolve_linked_interactions()
        self.handle_agent_spawn()
        self.relevant_agents = self.compute_relevant_agents()

    def resolve_primary_interaction(self, agent: Agent):
        interaction_location = self.get_target_location(agent, agent.orientation)
        if any([agent.location == interaction_location for agent in self.agents]):
            return
        dynamic_objects = self.get_objects_at(interaction_location, DynamicObject)
        static_object = self.get_objects_at(interaction_location, StaticObject)[0]

        if not agent.holding and not dynamic_objects:
            return
        elif not agent.holding and dynamic_objects:
            if static_object.releases():
                # changed, to preserve content order when picking up again (LIFO)
                object_to_grab = dynamic_objects[-1]
                if object_to_grab in static_object.content:
                    agent.grab(object_to_grab)
                    static_object.content.remove(object_to_grab)
                    agent.interacts_with = [object_to_grab]
        elif agent.holding:
            self.attempt_merge(agent, dynamic_objects, interaction_location, static_object)

    def resolve_interaction_pick_up_special(self, agent: Agent):
        interaction_location = self.get_target_location(agent, agent.orientation)
        if any([agent.location == interaction_location for agent in self.agents]):
            return
        dynamic_objects = self.get_objects_at(interaction_location, DynamicObject)
        if not agent.holding and dynamic_objects:
            content_obj_l = self.filter_obj(dynamic_objects, ContentObject)
            if len(content_obj_l) == 1:
                try:
                    obj = content_obj_l[0].content.pop(-1)  # pick the last object put on
                    agent.grab(obj)
                except IndexError:
                    pass
            else:
                return
        else:
            return

    def resolve_execute_action(self, agent: Agent):
        interaction_location = self.get_target_location(agent, agent.orientation)
        if any([agent.location == interaction_location for agent in self.agents]):
            return False
        static_object = self.get_objects_at(interaction_location, StaticObject)[0]
        if isinstance(static_object, ActionObject):
            obj_list_created, obj_list_deleted, action_executed = static_object.action()
            if action_executed:
                agent.interacts_with = [static_object]
            self.handle_object_deletion(obj_list_deleted)
            self.handle_object_creation(obj_list_created)
            return action_executed
        return False

    def handle_object_deletion(self, objects_to_delete):
        for obj in objects_to_delete:
            self.delete_object(obj)
            self.delete_from_index(obj)

    def handle_object_creation(self, objects_to_create):
        for obj in objects_to_create:
            self.add_object(obj)
            self.add_to_index(obj)

    @staticmethod
    def get_target_location(agent, action):
        if action == 1:
            target_location = (agent.location[0] - 1, agent.location[1])
        elif action == 2:
            target_location = (agent.location[0] + 1, agent.location[1])
        elif action == 3:
            target_location = (agent.location[0], agent.location[1] + 1)
        elif action == 4:
            target_location = (agent.location[0], agent.location[1] - 1)
        else:
            target_location = (agent.location[0], agent.location[1])
        return target_location

    def get_target_location_scheme2(self, agent):
        return self.get_target_location(agent, agent.orientation)

    def filter_obj(self, objects: List, obj_type):
        return [obj for obj in objects if isinstance(obj, obj_type)]

    def check_inbounds(self, agents, actions):
        cleaned_actions = []
        for agent, action in zip(agents, actions):
            if action == 0 or action == 5:
                cleaned_actions.append(action)
                continue
            target_location = self.get_target_location(agent, action)
            if target_location[0] > self.width - 1 or target_location[0] < 0:
                action = 0
            if target_location[1] > self.height - 1 or target_location[1] < 0:
                action = 0
            cleaned_actions.append(action)
        return cleaned_actions

    def check_collisions(self, agents, actions):
        collision_actions = []
        target_locations = []
        walkable = []
        for agent, action in zip(agents, actions):
            target_location = self.get_target_location(agent, action)
            target_walkable = self.square_walkable(target_location)
            end_location = target_location if target_walkable else agent.location
            target_locations.append(end_location)
            walkable.append(target_walkable)
        for idx, (action, target_location, target_walkable) in enumerate(zip(actions, target_locations, walkable)):
            if target_location in target_locations[:idx] + target_locations[idx+1:] and target_walkable:
                collision_actions.append(0)
            else:
                collision_actions.append(action)
        return collision_actions

    def square_walkable(self, location):
        objects = self.get_objects_at(location, StaticObject)
        if len(objects) != 1:
            raise Exception(f"Not exactly one static object at location: {location}")
        return objects[0].walkable

    def get_abstract_object_at(self, location, object_type):
        return [obj for obj in self.abstract_index[object_type] if obj.location == location]

    def get_objects_at(self, location, object_type=object):
        located_objects = []
        for obj_class_string, objects in self.world_objects.items():
            obj_class = StringToClass[obj_class_string]
            if not issubclass(obj_class, object_type):
                continue
            for obj in objects:
                if obj.location == location:
                    located_objects.append(obj)
        return located_objects

    def attempt_merge(self, agent: Agent, dynamic_objects: List[DynamicObject], target_location, static_object):
        content_obj = self.filter_obj(dynamic_objects, ContentObject)
        if content_obj and len(content_obj) == 1:
            if content_obj[0].accepts(agent.holding):
                content_obj[0].add_content(agent.holding)
                agent.put_down(target_location)
                agent.interacts_with.append(content_obj[0])
        elif isinstance(agent.holding, ContentObject) and dynamic_objects:
            pick_index = -1  # pick the last object put on
            if agent.holding.accepts(dynamic_objects[pick_index]):
                agent.holding.add_content(dynamic_objects[pick_index])
                dynamic_objects[pick_index].move_to(agent.location)
                agent.interacts_with.append(dynamic_objects[pick_index])
                static_object.content.remove(dynamic_objects[pick_index])
        elif isinstance(static_object, ContentObject):
            if static_object.accepts(agent.holding):
                static_object.add_content(agent.holding)
                agent.put_down(target_location)
                agent.interacts_with.append(static_object)

    def load_level(self, level, num_agents):
        reset_world_counter()
        load_level.load_level(self, level, num_agents)

    def handle_agent_spawn(self):
        for i in range(len(self.active_agents)):
            if self.agent_grace_period[i] > 0:
                self.agent_grace_period[i] -= 1
            else:
                # active = self.active_agents[i]
                if self.active_agents.count(True) > 1 and self.active_agents[i] \
                   and np.random.random() < self.agent_despawn_rate:
                    self.despawn_agent(i)
                elif not self.active_agents[i] and np.random.random() < self.agent_respawn_rate:
                    self.respawn_agent(i)

    def despawn_agent(self, index):
        if self.agents[index].holding:
            return
            # self.agents[index].put_down(self.agents[index].location)
        self.active_agents[index] = False
        self.status_changed[index] = True

    def respawn_agent(self, index):
        self.active_agents[index] = True
        self.status_changed[index] = True
        self.agent_grace_period[index] = self.grace_period
        self.agents[index].location = parsing.generate_location(self, *self.agent_spawn_locations[index])

    def compute_relevant_agents(self):
        return [agent for idx, agent in enumerate(self.agents) if self.active_agents[idx] or self.status_changed[idx]]

    def compute_active_agents(self):
        return [agent for idx, agent in enumerate(self.agents) if self.active_agents[idx]]
