from cooking_zoo.cooking_agents.base_agent import BaseAgent, CustomObject
from cooking_zoo.cooking_world.world_objects import *


class CookingAgent(BaseAgent):

    def __init__(self, recipe, name, others_recipe_info=None):
        super().__init__(recipe, name)
        if others_recipe_info:
            self.others_recipe = others_recipe_info["recipe"]
            self.other_name = others_recipe_info["name"]
            self.other_agent = CookingAgent(self.others_recipe, self.other_name)
        else:
            self.others_recipe = None
            self.other_name = None
            self.other_agent = None

    def step(self, observation):
        self.update_location(observation)
        world = CustomObject(observation)
        self.recipe_graph.update_recipe_state(world)
        node = self.find_node()
        if not node:
            action = 0
        else:
            action = self.compute_optimal_action(node, observation)
        # if not action:
        #     action = self.help_other_agent(observation)
        return action

    def compute_optimal_action(self, node, observation):
        condition_based_action = self.compute_condition_action(node, observation)
        if condition_based_action:
            return condition_based_action
        contains_based_action = self.compute_contains_action(node, observation)
        return contains_based_action

    def compute_contains_action(self, node, observation):
        # check if contained node is already on plate
        node_obj, contains_obj = self.compute_closest_node_in_contains_to_get(node, observation)
        if not contains_obj:
            return 0
        if contains_obj.location == self.location:
            return self.walk_to_location(node_obj.location, observation)
        else:
            return self.walk_to_location(contains_obj.location, observation)

    def compute_closest_node_in_contains_to_get(self, node, observation):
        node_obj, num_wrong_obj = self.get_location_with_most_objects(node, observation)
        if not node_obj:
            return None, None
        if num_wrong_obj:
            closest_free_container = self.get_closest_free_container(node_obj, observation)
            if closest_free_container:
                return closest_free_container, node_obj
            else:
                return None, None
        closest_contains = self.get_best_contains_obj(node, observation, node_obj)
        return node_obj, closest_contains

    def compute_condition_action(self, node, observation):
        world_objects = []
        for obj in observation[node.name]:
            # check for all conditions
            num_conditions = self.check_node_conditions(node, obj)
            dist = self.distance(self.location, obj.location)
            world_objects.append((obj, num_conditions, dist))
        best_world_object = sorted(world_objects, key=lambda x: (x[1], x[2]))[0][0]
        if best_world_object:
            for condition in node.conditions:
                if getattr(best_world_object, condition[0]) != condition[1]:
                    return self.handle_condition_sequence(best_world_object, observation, condition)
        return 0

    def get_best_contains_obj(self, node, observation, node_world_object):
        closest_object = None
        min_distance = float('inf')  # initialize to infinity

        # Loop over each child node in node.contains
        for child_node in node.contains:
            # Convert child node to world objects
            child_world_objects = [obj for obj in self.convert_node_to_world_objects(child_node, observation)
                                   if node_world_object.location != obj.location]

            # For each world object, compute the distance and check if it's the closest so far
            for obj in child_world_objects:
                distance = self.distance(self.location, obj.location)
                if distance < min_distance:
                    min_distance = distance
                    closest_object = obj
        return closest_object

    def convert_node_to_world_objects(self, node, observation):
        world_objects = []
        for obj in observation[node.name]:
            for condition in node.conditions:
                if getattr(obj, condition[0]) != condition[1]:
                    break
            else:
                # else executes if the for loop completes without breaking
                if self.reachable(obj.location, self.location, observation):
                    world_objects.append(obj)
        return world_objects

    def get_closest_world_object(self, node, observation):
        # Convert the node to world objects that are reachable from the agent's current location
        world_objects = self.convert_node_to_world_objects(node, observation)

        # Initialize variables to keep track of the closest object and its distance
        closest_object = None
        min_distance = float('inf')  # Initialize to infinity

        # Loop through the world objects to find the closest one
        for obj in world_objects:
            distance = self.distance(self.location, obj.location)
            if distance < min_distance:
                min_distance = distance
                closest_object = obj

        return closest_object  # Returns None if no objects are reachable

    def get_location_with_most_objects(self, node, observation):
        main_world_objects = self.convert_node_to_world_objects(node, observation)

        if self.agent.holding:
            for contained_node in node.contains:
                if isinstance(self.agent.holding, contained_node.root_type):
                    break
            else:
                return self.agent.holding, 1
        # For each world object of the main node, check how many contained objects are there
        best_count = -1
        worst_count = 100000000
        best_obj = None
        for main_obj in main_world_objects:
            count = 0
            wrong_obj_count = 0
            for contained_node in node.contains:
                # Convert each contained node to its world objects
                contained_world_objects = self.convert_node_to_world_objects(contained_node, observation)
                # Check for objects that are at the same location as the main object and fulfill the conditions
                for obj in contained_world_objects:
                    if obj.location == main_obj.location and all(
                            getattr(obj, condition[0]) == condition[1] for condition in contained_node.conditions):
                        count += 1
            if isinstance(main_obj, Agent):
                obj = main_obj.holding
                if obj:
                    matching_contains_node = [container_node for container_node in node.contains
                                              if isinstance(obj, container_node.root_type)]
                    if not matching_contains_node:
                        wrong_obj_count += 1
                        continue
                    if not any([all(getattr(obj, condition[0]) == condition[1] for condition in contains_node.conditions)
                                for contains_node in matching_contains_node]):
                        wrong_obj_count += 1
            else:
                for obj in main_obj.content:
                    matching_contains_node = [container_node for container_node in node.contains
                                              if isinstance(obj, container_node.root_type)]
                    if not matching_contains_node:
                        wrong_obj_count += 1
                        continue
                    if not any([all(getattr(obj, condition[0]) == condition[1]
                                    for condition in contains_node.conditions)
                                for contains_node in matching_contains_node]):
                        wrong_obj_count += 1
            # Update best_obj if the current main_obj has more matched contained objects
            if wrong_obj_count < worst_count or (wrong_obj_count == worst_count and (count > best_count or (
                    count == best_count and self.distance(self.location, main_obj.location) < self.distance(
                    self.location, best_obj.location)))):
                best_count = count
                worst_count = wrong_obj_count
                best_obj = main_obj
        if self.agent.holding and worst_count:
            return self.agent.holding, 1
        return best_obj, worst_count

    def get_closest_free_container(self, node_obj, observation):
        obj_location = node_obj.location

        content_objects = []
        for obj_list in observation.values():
            for obj in obj_list:
                if obj == node_obj:
                    continue
                if not self.reachable(obj.location, obj_location, observation):
                    continue
                if isinstance(obj, Counter):
                    if len(obj.content) < obj.max_content:
                        content_objects.append(obj)

        # Initialize variables to keep track of the closest object and its distance
        closest_object = None
        min_distance = float('inf')  # Initialize to infinity

        # Loop through the world objects to find the closest one
        for obj in content_objects:
            distance = self.distance(obj_location, obj.location)
            if distance < min_distance:
                min_distance = distance
                closest_object = obj

        return closest_object  # Returns None if no objects are reachable

    def help_other_agent(self, observation):
        if not self.others_recipe:
            return 0
        self.other_agent.update_location(observation)
        world = CustomObject(observation)
        self.other_agent.recipe_graph.update_recipe_state(world)
        node = self.other_agent.find_node()
        # identify non reachable object that other agent needs for his recipe
        # and he has no access to, has to be reachable for us
        node_world_object = None
        if node.contains:
            for contains_node in node.contains:
                obj = self.other_agent.get_closest_world_object(contains_node, observation)
                if obj:
                    continue
                obj = self.get_closest_world_object(contains_node, observation)
                if obj:
                    node_world_object = obj
                    break
        else:
            closest_object = self.other_agent.get_closest_world_object(node, observation)
            if closest_object:
                return 0
            closest_object = self.get_closest_world_object(node, observation)
            if not closest_object:
                return 0
        # identify reachable counters for other agent and yourself
        reachable_counter = []
        for counter in observation["Counter"]:
            reachable1 = self.reachable(self.location, counter.location, observation)
            reachable2 = self.other_agent.reachable(self.other_agent.location, counter.location, observation)
            if reachable1 and reachable2:
                reachable_counter.append(counter)
        # make space on one counter if none is free
        free_counter = None
        for counter in reachable_counter:
            if not counter.content:
                free_counter = counter
                break
        else:

            return 0
        # bring object into his reach
        return 0


def is_recipe_node_free_from_junk(node, observation):
    for obj in observation[node.name]:
        if isinstance(obj, Counter):
            if len(obj.content) > 0:
                return False
    return True



