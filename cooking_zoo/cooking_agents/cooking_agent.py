from cooking_zoo.cooking_agents.base_agent import BaseAgent, CustomObject


class CookingAgent(BaseAgent):

    def __init__(self, recipe, name):
        super().__init__(recipe, name)

    def step(self, observation):
        self.update_location(observation)
        world = CustomObject(observation)
        self.recipe_graph.update_recipe_state(world)
        node = self.find_node()
        if not node:
            return 0
        action = self.compute_optimal_action(node, observation)
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
        node_obj = self.get_location_with_most_objects(node, observation)
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
        world_objects = [obj for obj in observation[node.name]
                         if self.reachable(obj.location, self.location, observation)]
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

        # For each world object of the main node, check how many contained objects are there
        best_count = -1
        best_obj = None
        for main_obj in main_world_objects:
            count = 0
            for contained_node in node.contains:
                # Convert each contained node to its world objects
                contained_world_objects = self.convert_node_to_world_objects(contained_node, observation)
                # Check for objects that are at the same location as the main object and fulfill the conditions
                for obj in contained_world_objects:
                    if obj.location == main_obj.location and all(
                            getattr(obj, condition[0]) == condition[1] for condition in contained_node.conditions):
                        count += 1
            # Update best_obj if the current main_obj has more matched contained objects
            if count > best_count or (
                    count == best_count and self.distance(self.location, main_obj.location) < self.distance(
                    self.location, best_obj.location)):
                best_count = count
                best_obj = main_obj

        return best_obj



