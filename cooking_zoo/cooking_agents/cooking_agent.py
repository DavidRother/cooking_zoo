from cooking_zoo.cooking_agents.base_agent import BaseAgent, CustomObject
from cooking_zoo.cooking_book.recipe_drawer import RECIPES, NUM_GOALS, RECIPE_STORE, DEFAULT_NUM_GOALS
import numpy as np
from collections import deque


class CookingAgent(BaseAgent):

    def __init__(self, recipe, name):
        super().__init__()
        self.name = name
        self.recipe = recipe
        self.recipe_graph = RECIPES[recipe]()
        self.location = None
        self.agent = None

    def step(self, observation):
        self.update_location(observation)
        world = CustomObject(observation)
        self.recipe_graph.update_recipe_state(world)
        node = self.find_node()
        if not node:
            return 0
        action = self.compute_optimal_action(node, observation)
        return action

    def find_node(self):
        for node in reversed(self.recipe_graph.node_list):
            if not node.marked:
                return node
        return None

    def compute_optimal_action(self, node, observation):
        condition_based_action = self.compute_condition_action(node, observation)
        return 0

    def compute_condition_action(self, node, observation):
        world_objects = []
        for obj in observation[node.name]:
            # check for all conditions
            num_conditions = self.check_node_conditions(node, obj)
            dist = self.distance(self.location, obj.location)
            world_objects.append((obj, num_conditions, dist))
        best_world_object = sorted(world_objects, key=lambda x: (x[1], x[2]))[0][0]

        return 0

    @staticmethod
    def check_node_conditions(node, world_object):
        num_cond = 0
        for condition in node.conditions:
            if getattr(world_object, condition[0]) == condition[1]:
                num_cond += 1
        return num_cond

    def update_location(self, observation):
        for agent in observation["Agent"]:
            if agent.name == self.name:
                self.agent = agent
                self.location = agent.location
                return

    def chop_sequence(self, obj, observation):
        # check if obj is on Cutboard
        # if yes walk to it
        # if no check if is in hand
        # if no walk to obj
        # if yes walk to Cutboard
        for cutboard in observation["Cutboard"]:
            if obj in cutboard.content:
                return self.walk_to_location(obj.location, observation)
        

    def walk_to_location(self, location, observation):
        start = tuple(self.location)
        goal = tuple(location)

        if start == goal:
            return 0  # Stand still

        visited = set()
        queue = deque([(start, [])])

        floor_tiles = set(tuple(tile) for tile in observation["Floor"])

        while queue:
            current, path = queue.popleft()
            if current == goal:
                if path:
                    next_step = path[0]
                    for action, delta in self.action_dict.items():
                        if tuple(np.add(current, delta)) == next_step:
                            return action
                return 0  # Stand still if path is empty (should not happen as we check start == goal initially)

            visited.add(current)

            for action, delta in self.action_dict.items():
                next_tile = tuple(np.add(current, delta))
                if next_tile not in visited and next_tile in floor_tiles:
                    queue.append((next_tile, path + [next_tile]))

        # If there's no path found
        return 0

