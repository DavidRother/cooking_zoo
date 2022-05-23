from abc import abstractmethod, ABC
from gym_cooking.cooking_world.constants import *
from typing import List, Tuple


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

    @property
    def physical_state(self):
        return self.get_physical_state()

    @abstractmethod
    def numeric_state_representation(self):
        pass

    @staticmethod
    @abstractmethod
    def state_length():
        pass

    @abstractmethod
    def file_name(self) -> str:
        pass

    @abstractmethod
    def icons(self) -> List[str]:
        return []

    @abstractmethod
    def display_text(self) -> str:
        return self.name()

    # @abstractmethod
    def get_physical_state(self) -> dict:
        state = {}
        # in state observation
        state_attributes = [
            "location",
            "orientation",
            "holding",
            "walkable",
            "movable",
            "content",
            "chop_state",
            "blend_state",
            "toast_state",
            "interacts_with",
            "toggle",
            "status",
            "notFull",
            "notEmpty",
            "free",
        ]
        for attr in state_attributes:
            if hasattr(self, attr):
                ent_attr = getattr(self, attr)
                value = getattr(ent_attr, "value", ent_attr)
                state[attr] = value
        return state

class ActionObject(ABC):

    def __init__(self):
        super(ActionObject, self).__init__()
        self.status = ActionObjectState.NOT_USABLE

    @abstractmethod
    def action(self) -> Tuple[List, List, bool]:
        pass


class ToggleObject(ABC):

    def __init__(self, toggle=False):
        super(ToggleObject, self).__init__()
        self.toggle = toggle

    def switch_toggle(self):
        self.toggle = not self.toggle


class TemperatureObject:

    def __init__(self):
        super(TemperatureObject, self).__init__()
        self.temperature = Temperature.MILD

    @abstractmethod
    def apply_temperature(self, new_temperature):
        pass


class ProcessingObject(ABC):

    def __init__(self):
        super(ProcessingObject, self).__init__()

    @abstractmethod
    def process(self):
        pass


class ProgressingObject(ABC):

    def __init__(self):
        super(ProgressingObject, self).__init__()

    @abstractmethod
    def progress(self):
        pass


class ContentObject:

    def __init__(self, max_content=1):
        super(ContentObject, self).__init__()
        self.content = []
        self.max_content = max_content

    @property
    def notFull(self):
        return len(self.content) < self.max_content

    @property
    def notEmpty(self):
        return len(self.content) > 0

    @abstractmethod
    def add_content(self, content):
        pass

    @abstractmethod
    def move_to(self, new_location):
        pass

    @abstractmethod
    def accepts(self, dynamic_object) -> bool:
        pass


class Food:

    def __init__(self):
        super(Food, self).__init__()

    @abstractmethod
    def done(self):
        pass


class StaticObject(Object, ABC):

    def __init__(self, unique_id, location, walkable):
        super().__init__(unique_id, location, False, walkable)

    def move_to(self, new_location):
        raise Exception(f"Can't move static object {self.name()}")

    @abstractmethod
    def accepts(self, dynamic_objects) -> bool:
        pass

    @abstractmethod
    def releases(self) -> bool:
        pass


class DynamicObject(Object, ABC):

    def __init__(self, unique_id, location):
        super().__init__(unique_id, location, True, False)
        self.free = True


class TemperatureFood(DynamicObject, Food, TemperatureObject, ABC):

    def __init__(self, food_state):
        super(TemperatureFood, self).__init__()
        self.current_progress = 1
        self.max_progress = 0
        self.min_progress = 1
        self.food_state = food_state


class ChopFood(DynamicObject, Food, ABC):

    def __init__(self, unique_id, location):
        super().__init__(unique_id, location)
        self.chop_state = ChopFoodStates.FRESH

    def chop(self):
        if self.chop_state == ChopFoodStates.CHOPPED:
            return [], [], False
        self.chop_state = ChopFoodStates.CHOPPED
        return [], [], True


class BlenderFood(DynamicObject, Food, ABC):

    def __init__(self, unique_id, location):
        super().__init__(unique_id, location)
        self.current_progress = 1
        self.max_progress = 0
        self.min_progress = 1
        self.blend_state = BlenderFoodStates.FRESH

    def blend(self):
        if self.done():
            return False
        if self.blend_state == BlenderFoodStates.FRESH or self.blend_state == BlenderFoodStates.IN_PROGRESS:
            self.current_progress -= 1
            self.blend_state = BlenderFoodStates.IN_PROGRESS if self.current_progress > self.max_progress \
                else BlenderFoodStates.MASHED
        return True


class ToasterFood(DynamicObject, Food, ABC):

    def __init__(self, unique_id, location):
        super().__init__(unique_id, location)
        self.current_progress = 1
        self.max_progress = 0
        self.min_progress = 1
        self.toast_state = ToasterFoodStates.FRESH

    def toast(self):
        if self.toast_state == ToasterFoodStates.READY or self.toast_state == ToasterFoodStates.IN_PROGRESS:
            self.current_progress -= 1
            self.toast_state = ToasterFoodStates.IN_PROGRESS if self.current_progress > self.max_progress \
                else ToasterFoodStates.TOASTED
            return True
        return False


class MicrowaveFood(DynamicObject, Food, ABC):

    def __init__(self, unique_id, location):
        super().__init__(unique_id, location)
        self.current_progress = 1
        self.max_progress = 0
        self.min_progress = 1
        self.microwave_state = MicrowaveFoodStates.FRESH

    def microwave(self):
        if self.microwave_state == MicrowaveFoodStates.READY or self.microwave_state == MicrowaveFoodStates.IN_PROGRESS:
            self.current_progress -= 1
            self.microwave_state = MicrowaveFoodStates.IN_PROGRESS if self.current_progress > self.max_progress \
                else MicrowaveFoodStates.HOT
            return True
        return False


class PotFood(DynamicObject, Food, ABC):

    def __init__(self, unique_id, location):
        super().__init__(unique_id, location)
        self.current_progress = 1
        self.max_progress = 0
        self.min_progress = 1
        self.boil_state = PotFoodStates.FRESH

    def boil(self):
        if self.boil_state == PotFoodStates.READY or self.boil_state == PotFoodStates.IN_PROGRESS:
            self.current_progress -= 1
            self.boil_state = PotFoodStates.IN_PROGRESS if self.current_progress > self.max_progress \
                else PotFoodStates.COOKED
            return True
        return False


ABSTRACT_GAME_CLASSES = (ActionObject, ProcessingObject, ProgressingObject, ContentObject, Food, ChopFood,
                         DynamicObject, StaticObject, BlenderFood, ToasterFood)

STATEFUL_GAME_CLASSES = (ChopFood, BlenderFood, ToasterFood)
