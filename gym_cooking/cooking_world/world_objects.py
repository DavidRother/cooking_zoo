from gym_cooking.cooking_world.abstract_classes import *
from gym_cooking.cooking_world.constants import *
import inspect
import sys
from typing import List


class Floor(StaticObject, ContentObject):

    def __init__(self, unique_id, location):
        super().__init__(unique_id, location, True)

    def accepts(self, dynamic_object) -> bool:
        return False

    def releases(self) -> bool:
        return True

    def add_content(self, content):
        assert isinstance(content, Agent), f"Floors can only hold Agents as content! not {content}"
        self.content.append(content)

    def numeric_state_representation(self):
        return 1

    @staticmethod
    def state_length():
        return 1

    def file_name(self) -> str:
        return "floor"


class Counter(StaticObject, ContentObject):

    def __init__(self, unique_id, location):
        super().__init__(unique_id, location, False)

    def accepts(self, dynamic_object) -> bool:
        return not bool(self.content)

    def releases(self) -> bool:
        return True

    def add_content(self, content):
        self.content.append(content)

    def numeric_state_representation(self):
        return 1

    @staticmethod
    def state_length():
        return 1

    def file_name(self) -> str:
        return "counter"


class DeliverSquare(StaticObject, ContentObject):

    def __init__(self, unique_id, location):
        super().__init__(unique_id, location, False)

    def accepts(self, dynamic_object) -> bool:
        return True

    def add_content(self, content):
        self.content.append(content)

    def releases(self) -> bool:
        return True

    def numeric_state_representation(self):
        return 1

    @staticmethod
    def state_length():
        return 1

    def file_name(self) -> str:
        return "delivery"


class CutBoard(StaticObject, ActionObject, ContentObject):

    def __init__(self, unique_id, location):
        super().__init__(unique_id, location, False)

    def action(self) -> bool:
        if len(self.content) == 1:
            try:
                return self.content[0].chop()
            except AttributeError:
                return False
        return False

    def accepts(self, dynamic_object) -> bool:
        return isinstance(dynamic_object, ChopFood)

    def releases(self) -> bool:
        return True

    def add_content(self, content):
        self.content.append(content)

    def numeric_state_representation(self):
        return 1

    @staticmethod
    def state_length():
        return 1

    def file_name(self) -> str:
        return "cutboard"


class Oven(StaticObject, ProgressingObject, ContentObject, ToggleObject, ActionObject):

    def __init__(self, unique_id, location):
        super().__init__(unique_id, location, False)

    def progress(self):
        assert len(self.content) < 2, "Too many Dynamic Objects placed into the Oven"
        if self.content and self.toggle:
            self.content[0].apply_temperature(Temperature.HOT)
            if self.content[0].done():
                self.switch_toggle()

    def accepts(self, dynamic_object) -> bool:
        return isinstance(dynamic_object, TemperatureObject) and (not self.toggle)

    def releases(self) -> bool:
        return not self.toggle

    def add_content(self, content):
        self.content.append(content)

    def action(self) -> bool:
        self.switch_toggle()
        return True

    def numeric_state_representation(self):
        return 1

    @staticmethod
    def state_length():
        return 1

    def file_name(self) -> str:
        return "Oven_on" if self.toggle else "Oven"


class Blender(StaticObject, ProgressingObject, ContentObject, ToggleObject, ActionObject):

    def __init__(self, unique_id, location):
        super().__init__(unique_id, location, False)

    def progress(self):
        assert len(self.content) < 2, "Too many Dynamic Objects placed into the Blender"
        if self.content and self.toggle:
            self.content[0].blend()
            if self.content[0].done():
                self.switch_toggle()

    def accepts(self, dynamic_object) -> bool:
        return isinstance(dynamic_object, BlenderFood) and (not self.toggle)

    def releases(self) -> bool:
        return not self.toggle

    def add_content(self, content):
        self.content.append(content)

    def action(self) -> bool:
        self.switch_toggle()
        return True

    def numeric_state_representation(self):
        return 1

    @staticmethod
    def state_length():
        return 1

    def file_name(self) -> str:
        return "blender_on" if self.toggle else "blender3"


class Toaster(StaticObject, ProgressingObject, ContentObject, ToggleObject, ActionObject):

    def __init__(self, unique_id, location):
        super().__init__(unique_id, location, False)

        self.max_content = 2

    def progress(self):
        assert len(self.content) < self.max_content + 1, "Too many Dynamic Objects placed into the Toaster"
        if self.content and self.toggle:
            for con in self.content:
                con.toast()

            if all([cont.toast_state == ToasterFoodStates.TOASTED for cont in self.content]):
                self.switch_toggle()

    def accepts(self, dynamic_object) -> bool:
        return len(self.content) + 1 <= self.max_content and (not self.toggle) and \
               isinstance(dynamic_object, ToasterFood) and dynamic_object.toast_state == ToasterFoodStates.READY

    def releases(self) -> bool:
        return not self.toggle

    def add_content(self, content):
        if self.accepts(content):
            self.content.append(content)
        else:
            raise Exception(f"Tried to add invalid object {content.__name__} to Toaster")

    def action(self) -> bool:
        self.switch_toggle()
        return True

    def numeric_state_representation(self):
        return 1

    @staticmethod
    def state_length():
        return 1

    def file_name(self) -> str:
        return "toaster_on" if self.toggle else "toaster_off"


class Plate(DynamicObject, ContentObject):

    def __init__(self, unique_id, location):
        super().__init__(unique_id, location)

    def move_to(self, new_location):
        for content in self.content:
            content.move_to(new_location)
        self.location = new_location

    def add_content(self, content):
        if not isinstance(content, Food):
            raise TypeError(f"Only Food can be added to a plate! Tried to add {content.name()}")
        if not content.done():
            raise Exception(f"Can't add food in unprepared state.")
        self.content.append(content)

    def accepts(self, dynamic_object):
        return isinstance(dynamic_object, Food) and dynamic_object.done()

    def numeric_state_representation(self):
        return 1

    @staticmethod
    def state_length():
        return 1

    def file_name(self) -> str:
        return "Plate"


class Onion(ChopFood):

    def __init__(self, unique_id, location):
        super().__init__(unique_id, location)

    def done(self):
        if self.chop_state == ChopFoodStates.CHOPPED:
            return True
        else:
            return False

    def numeric_state_representation(self):
        return 1, 1

    @staticmethod
    def state_length():
        return 2

    def file_name(self) -> str:
        if self.done():
            return "ChoppedOnion"
        else:
            return "FreshOnion"


class Spaghetti(TemperatureObject):

    def apply_temperature(self, new_temperature):
        pass

    def __init__(self, unique_id, location):
        super().__init__(unique_id, location)
        self.food_state = SpaghettiStates.RAW

    def numeric_state_representation(self):
        return 1

    @staticmethod
    def state_length():
        return 1



class Tomato(ChopFood):

    def __init__(self, unique_id, location):
        super().__init__(unique_id, location)

    def done(self):
        if self.chop_state == ChopFoodStates.CHOPPED:
            return True
        else:
            return False

    def numeric_state_representation(self):
        return 1, 0

    @staticmethod
    def state_length():
        return 2

    def file_name(self) -> str:
        if self.done():
            return "ChoppedTomato"
        else:
            return "FreshTomato"


class Lettuce(ChopFood):

    def __init__(self, unique_id, location):
        super().__init__(unique_id, location)

    def done(self):
        if self.chop_state == ChopFoodStates.CHOPPED:
            return True
        else:
            return False

    def numeric_state_representation(self):
        return 1, 0

    @staticmethod
    def state_length():
        return 2

    def file_name(self) -> str:
        if self.done():
            return "ChoppedLettuce"
        else:
            return "FreshLettuce"


class Carrot(BlenderFood, ChopFood):

    def __init__(self, unique_id, location):
        super().__init__(unique_id, location)
        self.current_progress = 1

    def done(self):
        if self.chop_state == ChopFoodStates.CHOPPED or self.blend_state == BlenderFoodStates.MASHED:
            return True
        else:
            return False

    def numeric_state_representation(self):
        return 1, 0, 1

    @staticmethod
    def state_length():
        return 3

    def file_name(self) -> str:
        if self.done():
            if self.chop_state == ChopFoodStates.CHOPPED:
                return "ChoppedCarrot"
            elif self.blend_state == BlenderFoodStates.MASHED:
                return "CarrotMashed"
        else:
            return "FreshCarrot"


class Bread(ToasterFood, ChopFood):

    def __init__(self, unique_id, location):
        super().__init__(unique_id, location)
        self.current_progress = 1

    def done(self):
        return self.toast_state == ToasterFoodStates.TOASTED

    def chop(self):
        if self.chop_state == ChopFoodStates.CHOPPED:
            return False
        self.toast_state = ToasterFoodStates.READY
        self.chop_state = ChopFoodStates.CHOPPED
        return True

    def toast(self):
        if self.chop_state == ChopFoodStates.CHOPPED and \
                (self.toast_state == ToasterFoodStates.READY or self.toast_state == ToasterFoodStates.IN_PROGRESS):
            self.current_progress -= 1
            self.toast_state = ToasterFoodStates.IN_PROGRESS if self.current_progress > self.max_progress \
                else ToasterFoodStates.TOASTED
            return True
        return False

    def numeric_state_representation(self):
        return 1, 0, 0

    @staticmethod
    def state_length():
        return 3

    def file_name(self) -> str:
        if self.chop_state == ChopFoodStates.CHOPPED and self.toast_state == ToasterFoodStates.TOASTED:
            return "ChoppedToastedBread"
        elif self.chop_state == ChopFoodStates.CHOPPED:
            return "ChoppedFreshBread"
        else:
            return "Bread"


class Agent(Object):

    def __init__(self, unique_id, location, color, name):
        super().__init__(unique_id, location, False, False)
        self.holding = None
        self.color = color
        self.name = name
        self.orientation = 1
        self.interacts_with = []

    def grab(self, obj: DynamicObject):
        self.holding = obj
        obj.move_to(self.location)

    def put_down(self, location):
        self.holding.move_to(location)
        self.holding = None

    def move_to(self, new_location):
        self.location = new_location
        if self.holding:
            self.holding.move_to(new_location)

    def change_orientation(self, new_orientation):
        assert 0 < new_orientation < 5
        self.orientation = new_orientation

    def numeric_state_representation(self):
        return 1, int(self.orientation == 1), int(self.orientation == 2), int(self.orientation == 3), \
               int(self.orientation == 4)

    @staticmethod
    def state_length():
        return 5

    def file_name(self) -> str:
        pass


GAME_CLASSES = [m[1] for m in inspect.getmembers(sys.modules[__name__], inspect.isclass) if m[1].__module__ == __name__]

StringToClass = {game_cls.__name__: game_cls for game_cls in GAME_CLASSES}
ClassToString = {game_cls: game_cls.__name__ for game_cls in GAME_CLASSES}


