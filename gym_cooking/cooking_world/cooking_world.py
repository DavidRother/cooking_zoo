import copy
from collections import defaultdict
from gym_cooking.cooking_world.world_objects import *
from gym_cooking.cooking_world.actions import *

from pathlib import Path
import os.path
import json
import random
import itertools


class CookingWorld:

    LEFT = 1
    RIGHT = 2
    DOWN = 3
    UP = 4

    agent_turn_map = {(LEFT, ActionScheme2.TURN_LEFT): DOWN, (RIGHT, ActionScheme2.TURN_LEFT): UP,
                      (UP, ActionScheme2.TURN_LEFT): LEFT, (DOWN, ActionScheme2.TURN_LEFT): RIGHT,
                      (RIGHT, ActionScheme2.TURN_RIGHT): DOWN, (LEFT, ActionScheme2.TURN_RIGHT):UP,
                      (UP, ActionScheme2.TURN_RIGHT): RIGHT, (DOWN, ActionScheme2.TURN_RIGHT): LEFT}

    COLORS = ['blue', 'magenta', 'yellow', 'green']

    SymbolToClass = {
        ' ': Floor,
        '-': Counter,
        '/': CutBoard,
        '*': DeliverSquare,
        't': Tomato,
        'l': Lettuce,
        'o': Onion,
        'p': Plate,
        'b': Blender
    }

    # AGENT_ACTIONS: 0: Noop, 1: Left, 2: right, 3: down, 4: up, 5: interact

    def __init__(self, action_scheme_class=ActionScheme1):
        self.agents = []
        self.width = 0
        self.height = 0
        self.world_objects = defaultdict(list)
        self.abstract_index = defaultdict(list)
        self.id_counter = itertools.count(start=0, step=1)
        self.action_scheme = action_scheme_class
        self.init_world = None

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
        for obj in self.abstract_index[ProcessingObject]:
            obj.process()
        for obj in self.abstract_index[ProgressingObject]:
            obj.progress()
        for obj in self.abstract_index[ContentObject]:
            if len(obj.content) > 0:
                for c in obj.content:
                    if hasattr(c, "free"):
                        c.free = False
                if hasattr(obj.content[-1], 'free'):
                    obj.content[-1].free = True


    def perform_agent_actions(self, agents, actions):
        for agent, action in zip(agents, actions):
            agent.interacts_with = []
            if action in self.action_scheme.WALK_ACTIONS:
                if self.action_scheme == ActionScheme1:
                    agent.change_orientation(action)
                elif self.action_scheme == ActionScheme2:
                    if action in [ActionScheme2.TURN_LEFT, ActionScheme2.TURN_RIGHT]:
                        agent.change_orientation(self.agent_turn_map[(agent.orientation, action)])

        cleaned_actions = self.check_inbounds(agents, actions)
        collision_actions = self.check_collisions(agents, cleaned_actions)
        for agent, action in zip(agents, collision_actions):
            self.perform_agent_action(agent, action)
        self.progress_world()

    def perform_agent_action(self, agent: Agent, action):
        if action in self.action_scheme.WALK_ACTIONS:
            self.resolve_walking_action(agent, action)
        if action in self.action_scheme.INTERACT_ACTIONS:
            self.resolve_interaction(agent, action)

    def resolve_walking_action(self, agent: Agent, action):
        if self.action_scheme == ActionScheme1:
            target_location = self.get_target_location(agent, action)
        elif self.action_scheme == ActionScheme2:
            if action == ActionScheme2.WALK:
                target_location = self.get_target_location_scheme2(agent)
            else:
                return
        else:
            target_location = self.get_target_location(agent, action)
        if self.square_walkable(target_location):
            origin = self.get_objects_at(agent.location, StaticObject)
            target = self.get_objects_at(target_location, StaticObject)
            agent.move_to(target_location)
            agent.interacts_with = [target[0]]
            origin[0].content = []
            target[0].add_content(agent)

    def resolve_interaction(self, agent: Agent, action):
        if action == self.action_scheme.INTERACT_PRIMARY:
            self.resolve_primary_interaction(agent)
        elif action == self.action_scheme.INTERACT_PICK_UP_SPECIAL:
            self.resolve_interaction_pick_up_special(agent)
        elif action == self.action_scheme.EXECUTE_ACTION:
            self.resolve_execute_action(agent)

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
                for obj in dynamic_objects:
                    if hasattr(obj, "free") and obj.free:
                        object_to_grab = obj
                        break
                # content_obj_l = self.filter_obj(dynamic_objects, ContentObject)
                # pick_index = -1 #pick the last object put on
                # if content_obj_l:
                #     object_to_grab = content_obj_l[pick_index]
                # else:
                #     object_to_grab = dynamic_objects[pick_index]
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
                    obj = content_obj_l[0].content.pop(-1) #pick the last object put on
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
            return
        static_object = self.get_objects_at(interaction_location, StaticObject)[0]
        if isinstance(static_object, ActionObject):
            obj_list_created, obj_list_deleted, action_executed = static_object.action()
            if action_executed:
                agent.interacts_with = [static_object]
            for del_obj in obj_list_deleted:
                self.delete_object(del_obj)
                self.delete_from_index(del_obj)
            for new_obj in obj_list_created:
                new_obj.unique_id = next(self.id_counter)
                self.add_object(new_obj)
                self.add_to_index(new_obj)

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

    @staticmethod
    def get_target_location_scheme2(agent):
        if agent.orientation == 1:
            target_location = (agent.location[0] - 1, agent.location[1])
        elif agent.orientation == 2:
            target_location = (agent.location[0] + 1, agent.location[1])
        elif agent.orientation == 3:
            target_location = (agent.location[0], agent.location[1] + 1)
        elif agent.orientation == 4:
            target_location = (agent.location[0], agent.location[1] - 1)
        else:
            target_location = (agent.location[0], agent.location[1])
        return target_location

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

    def load_new_style_level(self, level_name, num_agents):
        self.id_counter = itertools.count(start=0, step=1)
        my_path = os.path.realpath(__file__)
        dir_name = os.path.dirname(my_path)
        path = Path(dir_name)
        parent = path.parent / f"utils/new_style_level/{level_name}.json"
        with open(parent) as json_file:
            level_object = json.load(json_file)
            json_file.close()
        self.parse_level_layout(level_object)
        self.parse_static_objects(level_object)
        self.parse_dynamic_objects(level_object)
        self.parse_agents(level_object, num_agents)

    def parse_level_layout(self, level_object):
        level_layout = level_object["LEVEL_LAYOUT"]
        x = 0
        y = 0
        for y, line in enumerate(iter(level_layout.splitlines())):
            for x, char in enumerate(line):
                if char == "-":
                    counter = Counter(unique_id=next(self.id_counter), location=(x, y))
                    self.add_object(counter)
                else:
                    floor = Floor(unique_id=next(self.id_counter), location=(x, y))
                    self.add_object(floor)
        self.width = x + 1
        self.height = y + 1

    def parse_static_objects(self, level_object):
        static_objects = level_object["STATIC_OBJECTS"]
        for static_object in static_objects:
            name = list(static_object.keys())[0]
            for idx in range(static_object[name]["COUNT"]):
                time_out = 0
                while True:
                    x = random.sample(static_object[name]["X_POSITION"], 1)[0]
                    y = random.sample(static_object[name]["Y_POSITION"], 1)[0]
                    if x < 0 or y < 0 or x > self.width or y > self.height:
                        raise ValueError(f"Position {x} {y} of object {name} is out of bounds set by the level layout!")
                    static_objects_loc = self.get_objects_at((x, y), StaticObject)

                    counter = [obj for obj in static_objects_loc if isinstance(obj, (Counter, Floor))]
                    if counter:
                        if len(counter) != 1:
                            raise ValueError("Too many counter in one place detected during initialization")
                        self.delete_object(counter[0])
                        obj = StringToClass[name](unique_id=next(self.id_counter), location=(x, y))
                        self.add_object(obj)
                        break
                    else:
                        time_out += 1
                        if time_out > 100:
                            raise ValueError(f"Can't find valid position for object: "
                                             f"{static_object} in {time_out} steps")
                        continue

    def parse_dynamic_objects(self, level_object):
        dynamic_objects = level_object["DYNAMIC_OBJECTS"]
        for dynamic_object in dynamic_objects:
            name = list(dynamic_object.keys())[0]
            for idx in range(dynamic_object[name]["COUNT"]):
                time_out = 0
                while True:
                    x = random.sample(dynamic_object[name]["X_POSITION"], 1)[0]
                    y = random.sample(dynamic_object[name]["Y_POSITION"], 1)[0]
                    if x < 0 or y < 0 or x > self.width or y > self.height:
                        raise ValueError(f"Position {x} {y} of object {name} is out of bounds set by the level layout!")
                    static_objects_loc = self.get_objects_at((x, y), Counter)
                    dynamic_objects_loc = self.get_objects_at((x, y), DynamicObject)

                    if len(static_objects_loc) == 1 and not dynamic_objects_loc:
                        obj = StringToClass[name](unique_id=next(self.id_counter), location=(x, y))
                        self.add_object(obj)
                        static_objects_loc[0].add_content(obj)
                        break
                    else:
                        time_out += 1
                        if time_out > 1000:
                            raise ValueError(f"Can't find valid position for object: "
                                             f"{dynamic_object} in {time_out} steps")
                        continue

    def parse_agents(self, level_object, num_agents):
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
                    if x < 0 or y < 0 or x > self.width or y > self.height:
                        raise ValueError(f"Position {x} {y} of agent is out of bounds set by the level layout!")
                    static_objects_loc = self.get_objects_at((x, y), Floor)
                    if not any([(x, y) == agent.location for agent in self.agents]) and static_objects_loc:
                        agent = Agent(next(self.id_counter), (int(x), int(y)), self.COLORS[len(self.agents)],
                                      'agent-' + str(len(self.agents) + 1))
                        self.agents.append(agent)
                        static_objects_loc[0].add_content(agent)
                        break
                    else:
                        time_out += 1
                        if time_out > 100:
                            raise ValueError(f"Can't find valid position for agent: {agent_object} in {time_out} steps")

    def load_level(self, level, num_agents):
        if self.init_world is not None:
            self.world_objects = defaultdict(list)
            self.world_objects.update(copy.deepcopy(self.init_world))
            self.agents = copy.deepcopy(self.init_agents)
        else:
            self.load_new_style_level(level, num_agents)
            self.init_world = defaultdict(list)
            self.init_world.update(copy.deepcopy(self.world_objects))
            self.init_agents = copy.deepcopy(self.agents)
        self.index_objects()
