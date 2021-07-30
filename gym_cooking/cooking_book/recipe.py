from gym_cooking.utils.core import *
# from gym_cooking.cooking_book.recipe_drawer import recipes
from gym_cooking.utils.world import World
from copy import deepcopy


class RecipeNode:

    def __init__(self, root, id_num, conditions=None, contains=None):
        self.child_nodes = self.generate_child_nodes()
        self.achieved = False
        self.id_num = id_num
        self.root = root
        self.conditions = conditions or []
        self.contains = contains or []

    def is_leaf(self):
        return not bool(self.child_nodes)

    def generate_child_nodes(self):
        child_nodes = []
        if self.conditions:
            for idx in range(len(self.conditions)):
                new_node = deepcopy(self)
                del new_node.conditions[idx]
                child_nodes.append(new_node)
        elif self.contains:
            for item in self.contains:
                child_nodes.append(item)
        return child_nodes


class Recipe:

    def __init__(self, root_node):
        self.root_node = root_node

    def update_achieved_state(self, node: RecipeNode, world: World, toplevel_world_object=None):
        for obj in world.objects[ClassToString[node.root]]:
            if not toplevel_world_object or toplevel_world_object.location != obj.location:
                continue
            # check for all conditions
            condition_flag = self.check_conditions(node, obj)
            # check for all contains

            pass

    @staticmethod
    def check_conditions(node: RecipeNode, world_object):
        for condition in node.conditions:
            if getattr(world_object, condition[0]) != condition[1]:
                return False
        else:
            return True

    def check_contains(self, node: RecipeNode, world_object, world: World):
        for held_node in node.contains:
            contained_world_object = self.check_held_node(held_node, world_object, world)

    def check_held_node(self, held_node, world_object, world: World):
        for obj in world.objects[ClassToString[held_node.root]]:
            if obj.location == world_object.location
