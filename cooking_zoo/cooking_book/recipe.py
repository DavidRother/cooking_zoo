from cooking_zoo.cooking_world.cooking_world import CookingWorld
from cooking_zoo.cooking_world.world_objects import *
from enum import Enum

import numpy as np


class NodeTypes(Enum):
    CHECKPOINT = "Checkpoint"
    ACTION = "Action"


class RecipeNode:

    def __init__(self, root_type, id_num, name, parent=None, conditions=None, contains=None, objects_to_seek=None):
        self.parent = parent
        self.marked = False
        self.id_num = id_num
        self.root_type = root_type
        self.conditions = conditions or []
        self.contains = contains or []
        self.world_objects = []
        self.name = name
        self.child_nodes = objects_to_seek or []

    def is_leaf(self):
        return not bool(self.contains)


class Recipe:

    def __init__(self, root_node: RecipeNode, num_goals: int):
        self.root_node = root_node
        self.node_list = [root_node] + self.expand_child_nodes(root_node)
        self.goal_encoding = self.goals_completed(num_goals)
        self.conditions_fulfilled = 0

    def goals_completed(self, num_goals):
        goals = np.zeros(num_goals, dtype=np.int32)
        for node in self.node_list:
            goals[node.id_num] = int(not node.marked)
        return goals

    def get_objects_to_seek(self):
        objects_to_seek = set()
        for node in self.node_list:
            if node.marked or not all((contains.marked for contains in node.contains)):
                continue
            objects_to_seek.update(node.objects_to_seek)
        return objects_to_seek

    def get_required_objects(self):
        # returns all objects that are required in the next step for the recipe
        required_objects = set()
        if self.root_node.marked:
            return required_objects
        if all([child.marked for child in self.root_node.contains]):
            required_objects.add(self.root_node)
            return required_objects
        for child in self.root_node.contains:
            if not child.marked:
                required_objects.update(self.get_recursive_required_objects(child))
        return required_objects

    def get_recursive_required_objects(self, node):
        required_objects = set()
        if all([child.marked for child in node.contains]):
            required_objects.add(node)
            return required_objects
        else:
            for child in node.contains:
                if not child.marked:
                    required_objects.update(self.get_recursive_required_objects(child))
            return required_objects

    def completed(self):
        return self.root_node.marked

    def update_recipe_state(self, world: CookingWorld):
        self.conditions_fulfilled = 0
        for node in reversed(self.node_list):
            node.marked = False
            node.world_objects = []
            markable = True
            if not all((contains.marked for contains in node.contains)):
                markable = False
            max_fulfilled = 0
            for obj in world.world_objects[node.name]:
                num_fulfilled_conditions, condition_check = self.check_conditions(node, obj)
                num_fulfilled_contains, contains_check = self.check_contains(node, obj, world)
                # check for all conditions
                max_fulfilled = max(num_fulfilled_conditions + num_fulfilled_contains, max_fulfilled)
                if condition_check and contains_check:
                    if markable:
                        node.world_objects.append(obj)
                        node.marked = True
                # if node.root_type == Carrot:
                #     print(f"World objects {node.world_objects}: Marked {node.marked}")
            self.conditions_fulfilled += max_fulfilled

    def expand_child_nodes(self, node: RecipeNode):
        child_nodes = []
        for child in node.contains:
            child_nodes.extend(self.expand_child_nodes(child))
        return node.contains + child_nodes

    @staticmethod
    def check_conditions(node: RecipeNode, world_object):
        fulfilled_conditions = []
        for condition in node.conditions:
            if getattr(world_object, condition[0]) != condition[1]:
                fulfilled_conditions.append(False)
            else:
                fulfilled_conditions.append(True)
        return sum(fulfilled_conditions), all(fulfilled_conditions)

    @staticmethod
    def check_contains_old(node: RecipeNode, world_object, world):
        all_contained = []
        for contains in node.contains:
            all_contained.append(any([obj.location == world_object.location for obj in contains.world_objects]))
        return sum(all_contained), all(all_contained)

    def check_contains(self, node: RecipeNode, parent_world_object, world):
        all_contained = []
        for contains in node.contains:
            identified_objects = sum([obj.location == parent_world_object.location for obj in contains.world_objects])
            all_contained.append(identified_objects == 1)
        candidate_objects = world.get_abstract_object_at(parent_world_object.location, DynamicObject)
        wrong_objects = []
        for obj in candidate_objects:
            wrong = self.check_if_obj_in_contains(obj, node)
            if wrong and obj != parent_world_object:
                wrong_objects.append(obj)
        if wrong_objects and node.contains:
            return 0, False
        return sum(all_contained), all(all_contained)

    def check_if_obj_in_contains(self, obj, node):
        for contains_obj in node.world_objects:
            if obj == contains_obj:
                return False
        for contains in node.contains:
            if not self.check_if_obj_in_contains(obj, contains):
                return False
        return True
