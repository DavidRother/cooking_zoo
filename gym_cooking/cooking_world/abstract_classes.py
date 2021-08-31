from abc import abstractmethod, ABC
from gym_cooking.cooking_world.constants import *


class Object:

    def __init__(self, location, movable, walkable):
        self.location = location
        self.movable = movable  # you can pick this one up
        self.walkable = walkable  # you can walk on it

    def name(self) -> str:
        return type(self).__name__

    def move_to(self, new_location):
        self.location = new_location


class ActionObject(ABC):

    @abstractmethod
    def action(self, objects):
        pass


class ProgressingObject(ABC):

    @abstractmethod
    def progress(self, dynamic_objects):
        pass


class StaticObject(Object):

    def __init__(self, location, walkable):
        super().__init__(location, False, walkable)

    def move_to(self, new_location):
        raise Exception(f"Can't move static object {self.name()}")

    @abstractmethod
    def accepts(self, dynamic_objects) -> bool:
        pass


class DynamicObject(Object):

    def __init__(self, location):
        super().__init__(location, True, False)


class Container(DynamicObject):

    def __init__(self, location, content=None):
        super().__init__(location)
        self.content = content or []

    def move_to(self, new_location):
        for content in self.content:
            content.move_to(new_location)
        self.location = new_location

    def add_content(self, content):
        self.content.append(content)


class Food(DynamicObject):

    def __init__(self, location, food_state):
        super().__init__(location)
        self.state = food_state

    @abstractmethod
    def done(self):
        pass


class ChopFood(Food, ABC):

    def __init__(self, location, food_state):
        super().__init__(location, food_state)

    def chop(self):
        if self.done():
            return False
        self.state = ChopFoodStates.CHOPPED
        return True

    def done(self):
        return self.state == ChopFoodStates.CHOPPED


class BlenderFood(Food, ABC):

    def __init__(self, location, food_state):
        super().__init__(location, food_state)
        self.current_progress = 10
        self.max_progress = 0
        self.min_progress = 10

    def blend(self):
        if self.done():
            return False
        if self.state == BlenderFoodStates.FRESH or self.state == BlenderFoodStates.IN_PROGRESS:
            self.current_progress -= 1
            self.state = BlenderFoodStates.IN_PROGRESS if self.current_progress > self.max_progress \
                else BlenderFoodStates.MASHED
        return True

    def done(self):
        return self.state == BlenderFoodStates.MASHED


ABSTRACT_GAME_CLASSES = [ActionObject, ProgressingObject, Container, Food, ChopFood, DynamicObject, StaticObject,
                         BlenderFood]
