from cooking_zoo.cooking_book.recipe_drawer import RECIPES
from cooking_zoo.cooking_world.world_objects import *
import numpy as np
from abc import abstractmethod
from collections import deque


class CustomObject:

    def __init__(self, dictionary):
        self.world_objects = dictionary


class BaseAgent:

    def __init__(self, recipe, name):
        # WALK_UP = 4
        # WALK_DOWN = 3
        # WALK_RIGHT = 2
        # WALK_LEFT = 1
        # NO_OP = 0
        # pygame.K_UP: (0, -1),  # 273
        # pygame.K_DOWN: (0, 1),  # 274
        # pygame.K_RIGHT: (1, 0),  # 275
        # pygame.K_LEFT: (-1, 0),  # 276
        self.action_dict = {
            0: np.array([0, 0]),
            1: np.array([-1, 0]),
            2: np.array([1, 0]),
            3: np.array([0, 1]),
            4: np.array([0, -1]),
        }

        self.name = name
        self.recipe = recipe
        if isinstance(recipe, str):
            self.recipe_graph = RECIPES[recipe]
        else:
            self.recipe_graph = recipe
        self.location = None
        self.agent = None
        self.cache = {}

    @abstractmethod
    def step(self, observation) -> int:
        pass

    @staticmethod
    def distance(point1, point2):
        return ((point1[0] - point2[0]) ** 2 + (point1[1] - point2[1]) ** 2) ** 0.5

    def find_node(self):
        for node in reversed(self.recipe_graph.node_list):
            if not node.marked:
                return node
        return None

    def update_location(self, observation):
        for agent in observation["Agent"]:
            if agent.name == self.name:
                self.agent = agent
                self.location = agent.location
                return

    def walk_to_location(self, location, observation):
        start = tuple(self.location)
        goal = tuple(location)

        if start == goal:
            return 0  # Stand still

        visited = set()
        queue = deque([(start, [])])

        floor_tiles = set(tuple(floor.location) for floor in observation["Floor"])

        while queue:
            current, path = queue.popleft()
            if current == goal:
                if path:
                    next_step = path[0]
                    for action, delta in self.action_dict.items():
                        if tuple(np.add(start, delta)) == next_step:
                            return action
                return 0  # Stand still if path is empty (should not happen as we check start == goal initially)

            visited.add(current)

            for action, delta in self.action_dict.items():
                next_tile = tuple(np.add(current, delta))
                if next_tile not in visited and (next_tile in floor_tiles or next_tile == goal):
                    queue.append((next_tile, path + [next_tile]))

        # If there's no path found
        return 0  # Stand still

    def reachable(self, location1, location2, observation):
        if (location1, location2) in self.cache or (location2, location1) in self.cache:
            return self.cache[(location1, location2)]

        if location1 == location2:
            self.cache[(location1, location2)] = True
            self.cache[(location2, location1)] = True
            return True

        visited = set()
        queue = deque([location1])

        floor_tiles = set(tuple(floor.location) for floor in observation["Floor"])

        while queue:
            current = queue.popleft()

            if current == location2:
                self.cache[(location1, location2)] = True
                self.cache[(location2, location1)] = True
                return True

            visited.add(current)

            # Iterate over all possible moves (up, down, left, right)
            for delta in [np.array([-1, 0]), np.array([1, 0]), np.array([0, 1]), np.array([0, -1])]:
                next_tile = tuple(np.add(current, delta))
                if next_tile not in visited and (next_tile in floor_tiles or next_tile == location2):
                    queue.append(next_tile)

        self.cache[(location1, location2)] = False
        self.cache[(location2, location1)] = False
        return False

    def closest(self, location, locations, observation):
        closest = None
        min_dist = np.inf
        for loc in locations:
            if not self.reachable(location, loc, observation):
                continue
            dist = self.distance(location, loc)
            if dist < min_dist:
                closest = loc
                min_dist = dist
        return closest

    def handle_condition_sequence(self, world_obj, observation, condition):
        sequence_dict = {
            ChopFoodStates.CHOPPED: "Cutboard",
            BlenderFoodStates.MASHED: "Blender",
            MicrowaveFoodStates.HOT: "Microwave",
            ToasterFoodStates.TOASTED: "Toaster",
            PotFoodStates.COOKED: "Pot"
        }
        appliance_name = sequence_dict.get(condition[1])

        if appliance_name:
            return self.generic_sequence(appliance_name, world_obj, observation)
        else:
            return 0

    def generic_sequence(self, appliance_name, obj, observation):
        for appliance in observation[appliance_name]:
            if not self.reachable(self.location, appliance.location, observation):
                continue
            if obj in appliance.content:
                return self.walk_to_location(obj.location, observation)
        if obj is self.agent.holding:
            appliance_locations = [appliance.location for appliance in observation[appliance_name]
                                   if self.reachable(self.location, appliance.location, observation)
                                   and not appliance.content]
            if appliance_locations:
                closest_appliance_location = self.closest(obj.location, appliance_locations, observation)
                return self.walk_to_location(closest_appliance_location, observation)
            else:
                counter_obj = [counter.location for counter in observation["Counter"]
                               if self.reachable(self.location, counter.location, observation)]
                closest_counter_location = self.closest(obj.location, counter_obj, observation)
                return self.walk_to_location(closest_counter_location, observation)
        else:
            appliance_locations = [appliance.location for appliance in observation[appliance_name]
                                   if self.reachable(self.location, appliance.location, observation)
                                   and not appliance.content]
            if appliance_locations:
                if self.agent.holding:
                    counter_obj = [counter.location for counter in observation["Counter"]
                                   if self.reachable(self.location, counter.location, observation)
                                   and not counter.content]
                    closest_counter_location = self.closest(self.location, counter_obj, observation)
                    return self.walk_to_location(closest_counter_location, observation)
                else:
                    return self.walk_to_location(obj.location, observation)
            else:
                appliance_locations = [appliance.location for appliance in observation[appliance_name]
                                       if self.reachable(self.location, appliance.location, observation)]
                closest_appliance_location = self.closest(self.location, appliance_locations, observation)
                if not closest_appliance_location:
                    return 0
                return self.walk_to_location(closest_appliance_location, observation)

    @staticmethod
    def check_node_conditions(node, world_object):
        num_cond = 0
        for condition in node.conditions:
            if getattr(world_object, condition[0]) != condition[1]:
                num_cond += 1
        return num_cond

