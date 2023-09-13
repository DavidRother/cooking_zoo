from abc import abstractmethod
import numpy as np


class CustomObject:

    def __init__(self, dictionary):
        self.world_objects = dictionary


class BaseAgent:

    def __init__(self):
        # WALK_UP = 4
        # WALK_DOWN = 3
        # WALK_RIGHT = 2
        # WALK_LEFT = 1
        # NO_OP = 0
        self.action_dict = {
            0: np.array([0, 0]),
            1: np.array([-1, 0]),
            2: np.array([1, 0]),
            3: np.array([0, 1]),
            4: np.array([0, -1]),
        }

    @abstractmethod
    def step(self, observation) -> int:
        pass

    @staticmethod
    def distance(point1, point2):
        return ((point1[0] - point2[0]) ** 2 + (point1[1] - point2[1]) ** 2) ** 0.5

