from gym_cooking.utils.core import *
from gym_cooking.utils.world import World


class RecipeNode:

    def __init__(self, root_type, id_num, parent=None, conditions=None, contains=None):
        self.parent = parent
        self.achieved = False
        self.id_num = id_num
        self.root = root_type
        self.conditions = conditions or []
        self.contains = contains or []
        self.world_objects = []

    def is_leaf(self):
        return not bool(self.contains)


class Recipe:

    def __init__(self, root_node: RecipeNode):
        self.root_node = root_node
        self.node_list = [root_node] + self.expand_child_nodes(root_node)

    def goals_completed(self, num_goals):
        goals = np.zeros(num_goals, dtype=np.int)
        for node in self.node_list:
            goals[node.id_num] = int(node.achieved)
        return goals

    def completed(self):
        return self.root_node.achieved

    def update_recipe_state(self, world: World):
        for node in reversed(self.node_list):
            node.achieved = False
            node.world_objects = []
            if not all((contains.achieved for contains in node.contains)):
                continue
            for obj in world.objects[ClassToString[node.root_type]]:
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
            if any((obj.location == world_object.location for contains in node.contains for obj in contains)):
                return True
            else:
                return False
