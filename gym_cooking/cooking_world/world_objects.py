from gym_cooking.cooking_world.abstract_classes import *
from gym_cooking.cooking_world.constants import *
import inspect
import sys
import numpy as np
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

    def get_physical_state(self) -> dict:
        return {}


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

    def get_physical_state(self) -> dict:
        return {}


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

    def get_physical_state(self) -> dict:
        return {}


class CutBoard(StaticObject, ActionObject, ContentObject):

    def __init__(self, unique_id, location):
        super().__init__(unique_id, location, False)

        self.max_content = 8

    def get_physical_state(self) -> dict:
        return {}

    def action(self) -> Tuple[List, List, bool]:
        for obj in self.content:
            if isinstance(obj, ChopFood):
                new_obj_list, deleted_obj_list, action_executed = obj.chop()
                if action_executed:
                    for del_obj in deleted_obj_list:
                        self.content.remove(del_obj)
                    for new_obj in new_obj_list:
                        self.content.append(new_obj)
                    return new_obj_list, deleted_obj_list, action_executed
        return [], [], False

    def accepts(self, dynamic_object) -> bool:
        return isinstance(dynamic_object, ChopFood) and len(self.content) < self.max_content

    def releases(self) -> bool:
        if len(self.content) == 1:
            self.status = ActionObjectState.NOT_USABLE
        return True

    def add_content(self, content):
        # self.content.append(content)

        if self.accepts(content):
            self.status = ActionObjectState.READY
            self.content.append(content)
        else:
            raise Exception(f"Tried to add invalid object {content.__name__} to CutBoard")

    def numeric_state_representation(self):
        return 1

    @staticmethod
    def state_length():
        return 1

    def file_name(self) -> str:
        return "cutboard"


#TODO not finished
class Oven(StaticObject, ProgressingObject, ContentObject, ToggleObject, ActionObject):

    def __init__(self, unique_id, location):
        super().__init__(unique_id, location, False)
        self.max_content = 1

    def process(self):
        assert len(self.content) <= self.max_content, "Too many Dynamic Objects placed into the Oven"

        if self.content and self.toggle:
            self.content[0].apply_temperature(Temperature.HOT)
            if self.content[0].done():
                self.switch_toggle()

                self.status = ActionObjectState.NOT_USABLE

                for cont in self.content:
                    cont.current_progress = cont.min_progress

    def accepts(self, dynamic_object) -> bool:
        return isinstance(dynamic_object, TemperatureObject) and (not self.toggle) and len(self.content) + 1 <= self.max_content

    def releases(self) -> bool:
        return not self.toggle

    def add_content(self, content):
        self.content.append(content)

    def action(self) -> Tuple[List, List, bool]:
        self.switch_toggle()
        return [], [], True

    def numeric_state_representation(self):
        return 1

    @staticmethod
    def state_length():
        return 1

    def file_name(self) -> str:
        return "Oven_on" if self.toggle else "Oven"

    def get_physical_state(self) -> dict:
        return {}


class Blender(StaticObject, ProcessingObject, ContentObject, ToggleObject, ActionObject):

    def __init__(self, unique_id, location):
        super().__init__(unique_id, location, False)
        self.max_content = 1

    def process(self):
        assert len(self.content) <= self.max_content, "Too many Dynamic Objects placed into the Blender"

        if self.content and self.toggle:

            for con in self.content:
                con.blend()

            if all([cont.blend_state == BlenderFoodStates.MASHED for cont in self.content]):
                self.switch_toggle()

                self.status = ActionObjectState.NOT_USABLE

                for cont in self.content:
                    cont.current_progress = cont.min_progress

    def accepts(self, dynamic_object) -> bool:
        return isinstance(dynamic_object, BlenderFood) and (not self.toggle) and len(self.content) + 1 <= self.max_content and dynamic_object.blend_state == BlenderFoodStates.FRESH

    def releases(self) -> bool:
        valid = not self.toggle
        if valid:
            # if last removed, not usable
            if len(self.content) - 1 == 0:
                self.status = ActionObjectState.NOT_USABLE
        return valid

    def add_content(self, content):
        if self.accepts(content):
            self.status = ActionObjectState.READY
            self.content.append(content)

    def action(self) -> Tuple[List, List, bool]:
        valid = self.status == ActionObjectState.READY
        if valid:
            self.switch_toggle()
        return [], [], valid

    def numeric_state_representation(self):
        return 1

    @staticmethod
    def state_length():
        return 1

    def file_name(self) -> str:
        return "blender_on" if self.toggle else "blender3"

    def get_physical_state(self) -> dict:
        return {}


class Toaster(StaticObject, ProcessingObject, ContentObject, ToggleObject, ActionObject):

    def __init__(self, unique_id, location):
        super().__init__(unique_id, location, False)
        self.max_content = 2

    def process(self):
        assert len(self.content) <= self.max_content, "Too many Dynamic Objects placed into the Toaster"
        if self.content and self.toggle:
            for con in self.content:
                con.toast()

            if all([cont.toast_state == ToasterFoodStates.TOASTED for cont in self.content]):
                self.switch_toggle()

                self.status = ActionObjectState.NOT_USABLE

                # reset progress, to be prooessed again.. different counters for different tools actually?
                for cont in self.content:
                    cont.current_progress = cont.min_progress

    def accepts(self, dynamic_object) -> bool:

        added = len(self.content) + 1 <= self.max_content and \
                (not self.toggle) and \
                isinstance(dynamic_object, ToasterFood) and \
                dynamic_object.toast_state == ToasterFoodStates.READY and \
                all([c.toast_state == ToasterFoodStates.READY for c in self.content])
        return added

    def releases(self) -> bool:
        valid = not self.toggle
        if valid:
            # if last removed, not usable
            if len(self.content) - 1 == 0:
                self.status = ActionObjectState.NOT_USABLE
        return valid

    def add_content(self, content):
        if self.accepts(content):
            self.status = ActionObjectState.READY
            self.content.append(content)
        else:
            raise Exception(f"Tried to add invalid object {content.__name__} to Toaster")

    def action(self) -> Tuple[List, List, bool]:
        valid = self.status == ActionObjectState.READY
        if valid:
            self.switch_toggle()
        return [], [], valid

    def numeric_state_representation(self):
        return 1

    @staticmethod
    def state_length():
        return 1

    def file_name(self) -> str:
        return "toaster_on" if self.toggle else "toaster_off"

    def get_physical_state(self) -> dict:
        return {}


class Microwave(StaticObject, ProcessingObject, ContentObject, ToggleObject, ActionObject):

    def __init__(self, unique_id, location):
        super().__init__(unique_id, location, False)
        self.max_content = 1

    def process(self):
        assert len(self.content) <= self.max_content, "Too many Dynamic Objects placed into the Toaster"
        if self.content and self.toggle:
            for con in self.content:
                con.microwave()

            if all([cont.microwave_state == MicrowaveFoodStates.HOT for cont in self.content]):
                self.switch_toggle()

                self.status = ActionObjectState.NOT_USABLE

                for cont in self.content:
                    cont.current_progress = cont.min_progress

    def accepts(self, dynamic_object) -> bool:
        return len(self.content) + 1 <= self.max_content and (not self.toggle) and \
               isinstance(dynamic_object, MicrowaveFood) and dynamic_object.microwave_state == MicrowaveFoodStates.READY

    def releases(self) -> bool:
        valid = not self.toggle
        if valid:
            # if last removed, not usable
            if len(self.content) - 1 == 0:
                self.status = ActionObjectState.NOT_USABLE
        return valid

    def add_content(self, content):
        if self.accepts(content):
            self.status = ActionObjectState.READY
            self.content.append(content)
        else:
            raise Exception(f"Tried to add invalid object {content.__name__} to Toaster")

    def action(self) -> Tuple[List, List, bool]:
        valid = self.status == ActionObjectState.READY
        if valid:
            self.switch_toggle()
        return [], [], valid

    def numeric_state_representation(self):
        return 1

    @staticmethod
    def state_length():
        return 1

    def file_name(self) -> str:
        return "Microwave_on" if self.toggle else "Microwave"

    def get_physical_state(self) -> dict:
        return {}


class Pot(StaticObject, ProcessingObject, ContentObject, ToggleObject, ActionObject):

    def __init__(self, unique_id, location):
        super().__init__(unique_id, location, False)
        self.max_content = 1

    def process(self):
        assert len(self.content) <= self.max_content, "Too many Dynamic Objects placed into the Pot"
        if self.content and self.toggle:
            for con in self.content:
                con.boil()

            if all([cont.boil_state == PotFoodStates.COOKED for cont in self.content]):
                self.switch_toggle()

                self.status = ActionObjectState.NOT_USABLE

                for cont in self.content:
                    cont.current_progress = cont.min_progress

    def accepts(self, dynamic_object) -> bool:
        return len(self.content) < self.max_content and (not self.toggle) and \
               isinstance(dynamic_object, PotFood) and dynamic_object.boil_state == PotFoodStates.READY

    def releases(self) -> bool:
        valid = not self.toggle
        if valid:
            # if last removed, not usable
            if len(self.content) - 1 == 0:
                self.status = ActionObjectState.NOT_USABLE
        return valid

    def add_content(self, content):
        if self.accepts(content):
            self.status = ActionObjectState.READY
            self.content.append(content)
        else:
            raise Exception(f"Tried to add invalid object {content.__name__} to Pot")

    def action(self) -> Tuple[List, List, bool]:
        valid = self.status == ActionObjectState.READY
        if valid:
            self.switch_toggle()
        return [], [], valid


    def numeric_state_representation(self):
        return 1

    @staticmethod
    def state_length():
        return 1

    def file_name(self) -> str:
        return "Pot_on" if self.toggle else "Pot"

    def get_physical_state(self) -> dict:
        return {}


class Plate(DynamicObject, ContentObject):

    def __init__(self, unique_id, location):
        super().__init__(unique_id, location)
        self.max_content = 64

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
        return isinstance(dynamic_object, Food) and dynamic_object.done() and len(self.content) < self.max_content

    def numeric_state_representation(self):
        return 1

    @staticmethod
    def state_length():
        return 1

    def file_name(self) -> str:
        return "Plate"

    def get_physical_state(self) -> dict:
        return {}


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

    def get_physical_state(self) -> dict:
        return {}


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

    def get_physical_state(self) -> dict:
        return {}


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

    def get_physical_state(self) -> dict:
        return {}


class Carrot(BlenderFood, ChopFood):

    def __init__(self, unique_id, location):
        super().__init__(unique_id, location)

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

    def get_physical_state(self) -> dict:
        return {}


class Bread(ChopFood, ToasterFood):

    def __init__(self, unique_id, location):
        super().__init__(unique_id, location)
        self.slices = 5
        self.chop_state = ChopFoodStates.FRESH
        self.toast_state = ToasterFoodStates.FRESH

    def done(self):
        return self.chop_state == ChopFoodStates.CHOPPED

    def chop(self):
        if self.slices > 1:
            # new_slice = BreadSlice(unique_id=-1, location=self.location)
            new_bread = Bread(unique_id=-1, location=self.location)
            new_bread.slices = 1
            new_bread.chop_state = ChopFoodStates.CHOPPED
            new_bread.toast_state = ToasterFoodStates.READY

            self.slices -= 1
            if self.slices == 1:
                self.chop_state = ChopFoodStates.CHOPPED
                self.toast_state = ToasterFoodStates.READY
            return [new_bread], [], True
        else:
            return [], [], False

    def numeric_state_representation(self):
        return 1, 0, 0

    @staticmethod
    def state_length():
        return 3

    def file_name(self) -> str:
        if self.toast_state == ToasterFoodStates.TOASTED:
            return "ChoppedToastedBread"
        elif self.chop_state == ChopFoodStates.CHOPPED:
            return "ChoppedFreshBread"
        else:
            return "Bread"

    def get_physical_state(self) -> dict:
        return {}


# class BreadSlice(ToasterFood):
#
#     def __init__(self, unique_id, location):
#         super().__init__(unique_id, location)
#         self.toast_state = ToasterFoodStates.READY
#
#     def done(self):
#         return self.toast_state == ToasterFoodStates.TOASTED
#
#     def toast(self):
#         if self.toast_state == ToasterFoodStates.READY or self.toast_state == ToasterFoodStates.IN_PROGRESS:
#             self.current_progress -= 1
#             self.toast_state = ToasterFoodStates.IN_PROGRESS if self.current_progress < self.max_progress \
#                 else ToasterFoodStates.TOASTED
#             return True
#         return False
#
#     def numeric_state_representation(self):
#         return 1, 0, 0
#
#     @staticmethod
#     def state_length():
#         return 3
#
#     def file_name(self) -> str:
#         if self.toast_state == ToasterFoodStates.TOASTED:
#             return "ChoppedToastedBread"
#         else:
#             return "ChoppedFreshBread"
#
# def get_physical_state(self) -> dict:
#     return {}


class Spaghetti(MicrowaveFood, PotFood):

    def __init__(self, unique_id, location):
        super().__init__(unique_id, location)

        start_state = np.random.randint(0, 2)
        if start_state == 0:
            self.microwave_state = MicrowaveFoodStates.FRESH
            self.boil_state = PotFoodStates.READY
        else:
            self.microwave_state = MicrowaveFoodStates.READY
            self.boil_state = PotFoodStates.COOKED

    # only used for determing if food can be on plate
    def done(self):
        return True

    def numeric_state_representation(self):
        return 1, 1, 1

    @staticmethod
    def state_length():
        return 3

    def file_name(self) -> str:
        if self.microwave_state == MicrowaveFoodStates.READY or self.microwave_state == MicrowaveFoodStates.IN_PROGRESS:
            return "SpaghettiCookedCold"
        elif self.microwave_state == MicrowaveFoodStates.HOT or self.boil_state == PotFoodStates.COOKED:
            return "SpaghettiCooked"
        else:
            return "SpaghettiRaw"

    def get_physical_state(self) -> dict:
        return {}


class Penne(MicrowaveFood, PotFood):

    def __init__(self, unique_id, location):
        super().__init__(unique_id, location)

        start_state = np.random.randint(0, 2)
        if start_state == 0:
            self.microwave_state = MicrowaveFoodStates.FRESH
            self.boil_state = PotFoodStates.READY
        else:
            self.microwave_state = MicrowaveFoodStates.READY
            self.boil_state = PotFoodStates.COOKED

    # only used for determing if food can be on plate
    def done(self):
        return True

    def numeric_state_representation(self):
        return 1, 1, 1

    @staticmethod
    def state_length():
        return 3

    def file_name(self) -> str:
        if self.microwave_state == MicrowaveFoodStates.READY or self.microwave_state == MicrowaveFoodStates.IN_PROGRESS:
            return "PenneCookedCold"
        elif self.microwave_state == MicrowaveFoodStates.HOT or self.boil_state == PotFoodStates.COOKED:
            return "PenneCooked"
        else:
            return "PenneRaw"

    def get_physical_state(self) -> dict:
        return {}


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

    def get_physical_state(self) -> dict:
        return {}


GAME_CLASSES = [m[1] for m in inspect.getmembers(sys.modules[__name__], inspect.isclass) if m[1].__module__ == __name__]

StringToClass = {game_cls.__name__: game_cls for game_cls in GAME_CLASSES}
ClassToString = {game_cls: game_cls.__name__ for game_cls in GAME_CLASSES}


