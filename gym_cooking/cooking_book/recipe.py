from gym_cooking.cooking_world.world_objects import *
from gym_cooking.cooking_world.cooking_world import CookingWorld

import numpy as np


class NodeTypes(Enum):
    CHECKPOINT = "Checkpoint"
    ACTION = "Action"


class RecipeNode:

    def __init__(self, root_type, id_num, name, parent=None, conditions=None, contains=None,
                 node_type=NodeTypes.CHECKPOINT):
        self.parent = parent
        self.achieved = False
        self.id_num = id_num
        self.root_type = root_type
        self.conditions = conditions or []
        self.contains = contains or []
        self.world_objects = []
        self.name = name
        self.node_type = node_type

    def is_leaf(self):
        return not bool(self.contains)


class Recipe:

    def __init__(self, root_node: RecipeNode):
        self.root_node = root_node
        self.node_list = [root_node] + self.expand_child_nodes(root_node)

    def goals_completed(self, num_goals):
        goals = np.zeros(num_goals, dtype=np.int32)
        for node in self.node_list:
            goals[node.id_num] = int(not node.achieved)
        return goals

    def completed(self):
        return self.root_node.achieved

    def update_recipe_state(self, world: CookingWorld):
        for node in reversed(self.node_list):
            node.achieved = False
            node.world_objects = []
            if not all((contains.achieved for contains in node.contains)):
                continue
            for obj in world.world_objects[node.name]:
                # check for all conditions
                if self.check_conditions(node, obj):
                    node.world_objects.append(obj)
                    node.achieved = True

    def expand_child_nodes(self, node: RecipeNode):
        child_nodes = []
        for child in node.contains:
            child_nodes.extend(self.expand_child_nodes(child))
        return node.contains + child_nodes

    @staticmethod
    def check_conditions(node: RecipeNode, world_object):
        for condition in node.conditions:
            if getattr(world_object, condition[0]) != condition[1]:
                return False
        else:
            all_contained = []
            for contains in node.contains:
                all_contained.append(any([obj.location == world_object.location for obj in contains.world_objects]))
            return all(all_contained)
