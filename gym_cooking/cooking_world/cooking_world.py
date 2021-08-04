from collections import defaultdict


class CookingWorld:

    def __init__(self, num_agents):
        self.num_agents = num_agents
        self.width = 0
        self.height = 0
        self.world_objects = defaultdict(list)

    def add_object(self, obj):
        self.world_objects[type(obj).__name__].append(obj)


