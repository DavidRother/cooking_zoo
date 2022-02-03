from abc import abstractmethod, ABC
from gym_cooking.cooking_world.constants import *


class Object(ABC):

    def __init__(self, unique_id, location, movable, walkable):
        super(Object, self).__init__()
        self.unique_id = unique_id
        self.location = location
        self.movable = movable  # you can pick this one up
        self.walkable = walkable  # you can walk on it

    def name(self) -> str:
        return type(self).__name__

    def move_to(self, new_location):
        self.location = new_location

    @abstractmethod
    def file_name(self) -> str:
        pass


class ActionObject(ABC):

    def __init__(self):
        super(ActionObject, self).__init__()

    @abstractmethod
    def action(self):
        pass


class ToggleObject(ABC):

    def __init__(self, toggle=False):
        super(ToggleObject, self).__init__()
        self.toggle = toggle

    def switch_toggle(self):
        self.toggle = not self.toggle


class ProgressingObject(ABC):

    def __init__(self):
        super(ProgressingObject, self).__init__()

    @abstractmethod
    def progress(self):
        pass


class ContentObject:

    def __init__(self):
        super(ContentObject, self).__init__()
        self.content = []

    @abstractmethod
    def add_content(self, content):
        pass

    @abstractmethod
    def move_to(self, new_location):
        pass


class Food:

    def __init__(self):
        super(Food, self).__init__()

    @abstractmethod
    def done(self):
        pass


class StaticObject(Object):

    def __init__(self, unique_id, location, walkable):
        super().__init__(unique_id, location, False, walkable)

    def move_to(self, new_location):
        raise Exception(f"Can't move static object {self.name()}")

    @abstractmethod
    def accepts(self, dynamic_objects) -> bool:
        pass


class DynamicObject(Object, ABC):

    def __init__(self, unique_id, location):
        super().__init__(unique_id, location, True, False)


class Container(DynamicObject, ContentObject, ABC):

    def __init__(self, unique_id, location, content=None):
        super().__init__(unique_id, location)
        self.content = content or []

    def move_to(self, new_location):
        for content in self.content:
            content.move_to(new_location)
        self.location = new_location

    def add_content(self, content):
        self.content.append(content)


class ChopFood(DynamicObject, Food, ABC):

    def __init__(self, unique_id, location):
        super().__init__(unique_id, location)
        self.chop_state = ChopFoodStates.FRESH

    def chop(self):
        if self.done():
            return False
        self.chop_state = ChopFoodStates.CHOPPED
        return True


class BlenderFood(DynamicObject, Food, ABC):

    def __init__(self, unique_id, location):
        super().__init__(unique_id, location)
        self.current_progress = 10
        self.max_progress = 0
        self.min_progress = 10
        self.blend_state = BlenderFoodStates.FRESH

    def blend(self):
        if self.done():
            return False
        if self.blend_state == BlenderFoodStates.FRESH or self.blend_state == BlenderFoodStates.IN_PROGRESS:
            self.current_progress -= 1
            self.blend_state = BlenderFoodStates.IN_PROGRESS if self.current_progress > self.max_progress \
                else BlenderFoodStates.MASHED
        return True


ABSTRACT_GAME_CLASSES = (ActionObject, ProgressingObject, Container, Food, ChopFood, DynamicObject, StaticObject,
                         BlenderFood)

STATEFUL_GAME_CLASSES = (ChopFood, BlenderFood)
