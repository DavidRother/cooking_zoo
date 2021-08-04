import numpy as np
from collections import defaultdict
import copy
from gym_cooking.utils.core import Object, GridSquare, Floor


class World:
    """World class that hold all of the non-agent objects in the environment."""
    NAV_ACTIONS = [(0, 1), (0, -1), (-1, 0), (1, 0)]

    def __init__(self, play):
        self.rep = []  # [row0, row1, ..., rown]
        self.play = play
        self.objects = defaultdict(lambda: [])
        self.loc_to_gridsquare = {}
        self.width = 0
        self.height = 0

    def __str__(self):
        _display = list(map(lambda x: ''.join(map(lambda y: y + ' ', x)), self.rep))
        return '\n'.join(_display)

    def __copy__(self):
        new = World(self.play)
        new.__dict__ = self.__dict__.copy()
        new.objects = copy.deepcopy(self.objects)
        return new

    def update_display(self):
        # Reset the current display (self.rep).
        self.rep = [[' ' for i in range(self.width)] for j in range(self.height)]
        objs = []
        for o in self.objects.values():
            objs += o
        for obj in objs:
            self.add_object(obj, obj.location)
        for obj in self.objects["Tomato"]:
            self.add_object(obj, obj.location)
        return self.rep

    def print_objects(self):
        for k, v in self.objects.items():
            print(k, list(map(lambda o: o.location, v)))

    def make_loc_to_gridsquare(self):
        """Creates a mapping between object location and object."""
        self.loc_to_gridsquare = {}
        for obj in self.get_object_list():
            if isinstance(obj, GridSquare):
                self.loc_to_gridsquare[obj.location] = obj

    def is_occupied(self, location):
        return any(((not isinstance(obj, Floor) and obj.location == location) for obj in self.objects))

    def clear_object(self, position):
        """Clears object @ position in self.rep and replaces it with an empty space"""
        x, y = position
        self.rep[y][x] = ' '

    def clear_all(self):
        self.rep = []

    def add_object(self, object_, position):
        x, y = position
        self.rep[y][x] = str(object_)

    def insert(self, obj):
        self.objects[obj.name].append(obj)

    def remove(self, obj):
        num_objs = len(self.objects[obj.name])
        index = None
        for i in range(num_objs):
            if self.objects[obj.name][i].location == obj.location:
                index = i
        assert index is not None, "Could not find {}!".format(obj.name)
        self.objects[obj.name].pop(index)
        assert len(self.objects[obj.name]) < num_objs, "Nothing from {} was removed from world.objects".format(obj.name)

    def get_object_list(self):
        all_obs = []
        for o in self.objects.values():
            all_obs += o
        return all_obs

    def is_collidable(self, location):
        return location in list(map(lambda o: o.location, list(filter(lambda o: o.collidable, self.get_object_list()))))

    def get_object_at(self, location, desired_obj, find_held_objects):
        # Map obj => location => filter by location => return that object.
        all_objs = self.get_object_list()

        if desired_obj is None:
            objs = list(filter(
                lambda obj: obj.location == location and isinstance(obj, Object) and obj.is_held is find_held_objects,
                all_objs))
        else:
            objs = list(filter(lambda obj: obj.name == desired_obj.name and obj.location == location and
                                           isinstance(obj, Object) and obj.is_held is find_held_objects,
                               all_objs))

        assert len(objs) == 1, f"looking for {desired_obj}, found {','.join(o.get_name() for o in objs)} at {location}"

        return objs[0]

    def get_gridsquare_at(self, location):
        gss = list(filter(lambda o: o.location == location and \
                                    isinstance(o, GridSquare), self.get_object_list()))

        assert len(gss) == 1, f"{len(gss)} gridsquares at {location}: {gss}"
        return gss[0]

    def inbounds(self, location):
        """Correct locaiton to be in bounds of world object."""
        x, y = location
        return min(max(x, 0), self.width - 1), min(max(y, 0), self.height - 1)
