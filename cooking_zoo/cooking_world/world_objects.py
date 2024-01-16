from cooking_zoo.cooking_world.abstract_classes import *
from cooking_zoo.cooking_world.constants import *
import inspect
import sys
from typing import List
import itertools


world_id_counter = itertools.count(start=0, step=1)


def reset_world_counter():
    global world_id_counter
    world_id_counter = itertools.count(start=0, step=1)


class Floor(StaticObject, ContentObject):

    def __init__(self, location):
        unique_id = next(world_id_counter)
        super().__init__(unique_id, location, True)

    def accepts(self, dynamic_object) -> bool:
        return False

    def releases(self) -> bool:
        return True

    def add_content(self, content):
        assert isinstance(content, Agent), f"Floors can only hold Agents as content! not {content}"
        self.content.append(content)

    def numeric_state_representation(self):
        return 1,

    def feature_vector_representation(self):
        return []

    @classmethod
    def state_length(cls):
        return 1

    @classmethod
    def feature_vector_length(cls):
        return 0

    def file_name(self) -> str:
        return "Floor"

    def icons(self) -> List[str]:
        return []

    def display_text(self) -> str:
        return ""


class Counter(StaticObject, ContentObject):

    def __init__(self, location):
        unique_id = next(world_id_counter)
        super().__init__(unique_id, location, False)
        self.max_content = 1

    def accepts(self, dynamic_object) -> bool:
        # return not bool(self.content)
        return len(self.content) < self.max_content

    def releases(self) -> bool:
        return True

    def add_content(self, content):
        self.content.append(content)
        for c in self.content:
            c.free = False
        self.content[-1].free = True

    def numeric_state_representation(self):
        return 1,

    def feature_vector_representation(self):
        return list(self.location) + [1]

    @classmethod
    def state_length(cls):
        return 1

    @classmethod
    def feature_vector_length(cls):
        return 3

    def file_name(self) -> str:
        return "Counter"

    def icons(self) -> List[str]:
        return []

    def display_text(self) -> str:
        return ""


class Deliversquare(StaticObject, ContentObject):

    def __init__(self, location):
        unique_id = next(world_id_counter)
        super().__init__(unique_id, location, False)

    def accepts(self, dynamic_object) -> bool:
        return len(self.content) < self.max_content

    def add_content(self, content):
        if self.accepts(content):
            self.content.append(content)
            for c in self.content:
                c.free = False
            self.content[-1].free = True

    def releases(self) -> bool:
        return False

    def numeric_state_representation(self):
        return 1,

    def feature_vector_representation(self):
        return list(self.location) + [1]

    @classmethod
    def feature_vector_length(cls):
        return 3

    @classmethod
    def state_length(cls):
        return 1

    def file_name(self) -> str:
        return "DeliverySquare"

    def icons(self) -> List[str]:
        return []

    def display_text(self) -> str:
        return ""


class Switch(StaticObject, ContentObject, LinkedObject):

    def __init__(self, location):
        unique_id = next(world_id_counter)
        super().__init__(unique_id, location, True)
        self.max_content = 1
        self.switch_active = False
        self.button_pressed = False

    def accepts(self, dynamic_object) -> bool:
        return False

    def releases(self) -> bool:
        return True

    def add_content(self, content):
        assert isinstance(content, Agent), f"Floors can only hold Agents as content! not {content}"
        self.content.append(content)
        self.switch_active = not self.switch_active
        self.button_pressed = True

    def process_linked_objects(self):
        if self.button_pressed:
            for obj in self.linked_objects:
                obj.switch_state()
        self.button_pressed = False

    def numeric_state_representation(self):
        return 1,

    def feature_vector_representation(self):
        return list(self.location) + [self.switch_active, 1]

    @classmethod
    def state_length(cls):
        return 1

    @classmethod
    def feature_vector_length(cls):
        return 4

    def file_name(self) -> str:
        return "SwitchOn" if self.switch_active else "SwitchOff"

    def icons(self) -> List[str]:
        return []

    def display_text(self) -> str:
        return ""


class Block(StaticObject, ContentObject, LinkedObject):

    def __init__(self, location):
        unique_id = next(world_id_counter)
        super().__init__(unique_id, location, False)
        self.max_content = 1

    def releases(self) -> bool:
        return True

    def process_linked_objects(self):
        pass

    def accepts(self, dynamic_objects) -> bool:
        return False

    def add_content(self, content):
        assert isinstance(content, Agent), f"Blocks can only hold Agents as content! not {content}"
        self.content.append(content)

    def switch_state(self):
        self.walkable = not self.walkable

    def numeric_state_representation(self):
        return 1,

    def feature_vector_representation(self):
        return list(self.location) + [int(self.walkable), 1]

    @classmethod
    def state_length(cls):
        return 1

    @classmethod
    def feature_vector_length(cls):
        return 4

    def file_name(self) -> str:
        return "Floor" if self.walkable else "BlockActive"

    def icons(self) -> List[str]:
        return []

    def display_text(self) -> str:
        return ""


class Cutboard(StaticObject, ActionObject, ContentObject):

    def __init__(self, location):
        unique_id = next(world_id_counter)
        super().__init__(unique_id, location, False)

        self.max_content = 1

    def action(self) -> Tuple[List, List, bool]:
        valid = self.status == ActionObjectState.READY
        if valid:
            for obj in self.content:
                if isinstance(obj, ChopFood):
                    new_obj_list, deleted_obj_list, action_executed = obj.chop()

                    if action_executed:
                        for del_obj in deleted_obj_list:
                            self.content.remove(del_obj)
                        for new_obj in new_obj_list:
                            self.content.append(new_obj)

                        self.status = ActionObjectState.NOT_USABLE

                        return new_obj_list, deleted_obj_list, action_executed
                else:
                    return [], [], False
        else:
            return [], [], False

    def accepts(self, dynamic_object) -> bool:
        return isinstance(dynamic_object, ChopFood) and len(self.content) < self.max_content and \
                dynamic_object.chop_state == ChopFoodStates.FRESH

    def releases(self) -> bool:
        if len(self.content) == 1:
            self.status = ActionObjectState.NOT_USABLE
        return True

    def add_content(self, content):
        if self.accepts(content):
            self.status = ActionObjectState.READY
            self.content.append(content)
            for c in self.content:
                c.free = False
            self.content[-1].free = True
        else:
            raise Exception(f"Tried to add invalid object {content.__name__} to CutBoard")

    def numeric_state_representation(self):
        return 1,

    def feature_vector_representation(self):
        return list(self.location) + [1]

    @classmethod
    def state_length(cls):
        return 1

    @classmethod
    def feature_vector_length(cls):
        return 3

    def file_name(self) -> str:
        return "cutboard"

    def icons(self) -> List[str]:
        return []

    def display_text(self) -> str:
        return ""


class Blender(StaticObject, ProcessingObject, ContentObject, ToggleObject, ActionObject):

    def __init__(self, location):
        unique_id = next(world_id_counter)
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
            for c in self.content:
                c.free = False
            self.content[-1].free = True

    def action(self) -> Tuple[List, List, bool]:
        valid = self.status == ActionObjectState.READY
        if valid:
            self.switch_toggle()
        return [], [], valid

    def numeric_state_representation(self):
        return 1,

    @classmethod
    def state_length(cls):
        return 1

    def feature_vector_representation(self):
        return list(self.location) + [1]

    @classmethod
    def feature_vector_length(cls):
        return 3

    def file_name(self) -> str:
        return "blender_on" if self.toggle else "blender3"

    def icons(self) -> List[str]:
        return []

    def display_text(self) -> str:
        return ""


class Plate(DynamicObject, ContentObject):

    def __init__(self, location):
        unique_id = next(world_id_counter)
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
        for c in self.content:
            c.free = False
        self.content[-1].free = True

    def accepts(self, dynamic_object):
        return isinstance(dynamic_object, Food) and dynamic_object.done() and len(self.content) < self.max_content

    def numeric_state_representation(self):
        return 1,

    def feature_vector_representation(self):
        return list(self.location) + [1]

    @classmethod
    def state_length(cls):
        return 1

    @classmethod
    def feature_vector_length(cls):
        return 3

    def file_name(self) -> str:
        return "Plate"

    def icons(self) -> List[str]:
        return []

    def display_text(self) -> str:
        return ""


class Onion(ChopFood):

    def __init__(self, location):
        unique_id = next(world_id_counter)
        super().__init__(unique_id, location)

    def done(self):
        return self.chop_state == ChopFoodStates.CHOPPED

    def numeric_state_representation(self):
        return 1, int(self.chop_state == ChopFoodStates.CHOPPED)

    def feature_vector_representation(self):
        return list(self.location) + [int(not self.done()), int(self.done())] + [1]

    @classmethod
    def state_length(cls):
        return 2

    @classmethod
    def feature_vector_length(cls):
        return 5

    def file_name(self) -> str:
        if self.done():
            return "ChoppedOnion"
        else:
            return "FreshOnion"

    def icons(self) -> List[str]:
        return []

    def display_text(self) -> str:
        return ""


class Tomato(ChopFood):

    def __init__(self, location):
        unique_id = next(world_id_counter)
        super().__init__(unique_id, location)

    def done(self):
        return self.chop_state == ChopFoodStates.CHOPPED

    def numeric_state_representation(self):
        return 1, int(self.chop_state == ChopFoodStates.CHOPPED)

    def feature_vector_representation(self):
        return list(self.location) + [int(not self.done()), int(self.done())] + [1]

    @classmethod
    def state_length(cls):
        return 2

    @classmethod
    def feature_vector_length(cls):
        return 5

    def file_name(self) -> str:
        if self.done():
            return "ChoppedTomato"
        else:
            return "FreshTomato"

    def icons(self) -> List[str]:
        return []

    def display_text(self) -> str:
        return ""


class Lettuce(ChopFood):

    def __init__(self, location):
        unique_id = next(world_id_counter)
        super().__init__(unique_id, location)

    def done(self):
        return self.chop_state == ChopFoodStates.CHOPPED

    def numeric_state_representation(self):
        return 1, int(self.chop_state == ChopFoodStates.CHOPPED)

    def feature_vector_representation(self):
        return list(self.location) + [int(not self.done()), int(self.done())] + [1]

    @classmethod
    def state_length(cls):
        return 2

    @classmethod
    def feature_vector_length(cls):
        return 5

    def file_name(self) -> str:
        if self.done():
            return "ChoppedLettuce"
        else:
            return "FreshLettuce"

    def icons(self) -> List[str]:
        return []

    def display_text(self) -> str:
        return ""


class Carrot(BlenderFood, ChopFood):

    def __init__(self, location):
        unique_id = next(world_id_counter)
        super().__init__(unique_id, location)

    def done(self):
        return self.chop_state == ChopFoodStates.CHOPPED or self.blend_state == BlenderFoodStates.MASHED

    def numeric_state_representation(self):
        return 1, int(self.chop_state == ChopFoodStates.CHOPPED)

    def feature_vector_representation(self):
        return list(self.location) + [int(not self.done()), int(self.chop_state == ChopFoodStates.CHOPPED),
                                      int(self.blend_state == BlenderFoodStates.MASHED)] + [1]

    @classmethod
    def state_length(cls):
        return 2

    @classmethod
    def feature_vector_length(cls):
        return 6

    def file_name(self) -> str:
        if self.done():
            if self.chop_state == ChopFoodStates.CHOPPED:
                return "ChoppedCarrot"
            elif self.blend_state == BlenderFoodStates.MASHED:
                return "CarrotMashed"
        else:
            return "FreshCarrot"

    def icons(self) -> List[str]:
        return []

    def display_text(self) -> str:
        return ""


class Cucumber(ChopFood):

    def __init__(self, location):
        unique_id = next(world_id_counter)
        super().__init__(unique_id, location)

    def done(self):
        return self.chop_state == ChopFoodStates.CHOPPED

    def numeric_state_representation(self):
        return 1, int(self.chop_state == ChopFoodStates.CHOPPED)

    def feature_vector_representation(self):
        return list(self.location) + [int(not self.done()), int(self.done())] + [1]

    @classmethod
    def state_length(cls):
        return 2

    @classmethod
    def feature_vector_length(cls):
        return 5

    def file_name(self) -> str:
        return "Cucumber"

    def icons(self) -> List[str]:
        return []

    def display_text(self) -> str:
        return ""


class Banana(BlenderFood, ChopFood):

    def __init__(self, location):
        unique_id = next(world_id_counter)
        super().__init__(unique_id, location)

    def done(self):
        return self.chop_state == ChopFoodStates.CHOPPED or self.blend_state == BlenderFoodStates.MASHED

    def numeric_state_representation(self):
        return 1, int(self.chop_state == ChopFoodStates.CHOPPED)

    def feature_vector_representation(self):
        return list(self.location) + [int(not self.done()), int(self.chop_state == ChopFoodStates.CHOPPED),
                                      int(self.blend_state == BlenderFoodStates.MASHED)] + [1]

    @classmethod
    def state_length(cls):
        return 2

    @classmethod
    def feature_vector_length(cls):
        return 6

    def file_name(self) -> str:
        if self.done():
            if self.chop_state == ChopFoodStates.CHOPPED:
                return "ChoppedBanana"
            elif self.blend_state == BlenderFoodStates.MASHED:
                return "ChoppedBanana"
        else:
            return "FreshBanana"

    def icons(self) -> List[str]:
        return []

    def display_text(self) -> str:
        return ""


class Apple(ChopFood):

    def __init__(self, location):
        unique_id = next(world_id_counter)
        super().__init__(unique_id, location)

    def done(self):
        return self.chop_state == ChopFoodStates.CHOPPED

    def numeric_state_representation(self):
        return 1, int(self.chop_state == ChopFoodStates.CHOPPED)

    def feature_vector_representation(self):
        return list(self.location) + [int(not self.done()), int(self.chop_state == ChopFoodStates.CHOPPED)] + [1]

    @classmethod
    def state_length(cls):
        return 2

    @classmethod
    def feature_vector_length(cls):
        return 5

    def file_name(self) -> str:
        if self.chop_state == ChopFoodStates.CHOPPED:
            return "ChoppedApple"
        else:
            return "FreshApple"

    def icons(self) -> List[str]:
        return []

    def display_text(self) -> str:
        return f""


class Watermelon(ChopFood):

    def __init__(self, location):
        unique_id = next(world_id_counter)
        super().__init__(unique_id, location)

    def done(self):
        return self.chop_state == ChopFoodStates.CHOPPED

    def numeric_state_representation(self):
        return 1, int(self.chop_state == ChopFoodStates.CHOPPED)

    def feature_vector_representation(self):
        return list(self.location) + [int(not self.done()), int(self.done())] + [1]

    @classmethod
    def state_length(cls):
        return 2

    @classmethod
    def feature_vector_length(cls):
        return 5

    def file_name(self) -> str:
        if self.chop_state == ChopFoodStates.CHOPPED:
            return "ChoppedWatermelon"
        else:
            return "FreshWatermelon"

    def icons(self) -> List[str]:
        return []

    def display_text(self) -> str:
        return f""


class Bread(ChopFood):

    def __init__(self, location):
        unique_id = next(world_id_counter)
        super().__init__(unique_id, location)
        self.chop_state = ChopFoodStates.FRESH

    def done(self):
        return self.chop_state == ChopFoodStates.CHOPPED

    def chop(self):
        if self.chop_state == ChopFoodStates.FRESH:
            self.chop_state = ChopFoodStates.CHOPPED
            new_chopped_bread = Bread(self.location)
            new_chopped_bread.chop_state = ChopFoodStates.CHOPPED
            return [new_chopped_bread], [], True
        else:
            return [], [], False

    def numeric_state_representation(self):
        return 1, 0, 0

    @classmethod
    def state_length(cls):
        return 3

    def feature_vector_representation(self):
        return list(self.location) + [int(not self.done()), int(self.done())] + [1]

    @classmethod
    def feature_vector_length(cls):
        return 5

    def file_name(self) -> str:
        if self.chop_state == ChopFoodStates.CHOPPED:
            return "ChoppedFreshBread"
        else:
            return "Bread"

    def icons(self) -> List[str]:
        return []

    def display_text(self) -> str:
        return f""


class Agent(Object):

    def __init__(self, location, color, name):
        unique_id = next(world_id_counter)
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

    def feature_vector_representation(self):
        return list(self.location) + [int(self.orientation == 1), int(self.orientation == 2),
                                      int(self.orientation == 3), int(self.orientation == 4)] + [1]

    @classmethod
    def state_length(cls):
        return 5

    @classmethod
    def feature_vector_length(cls):
        return 7

    def file_name(self) -> str:
        pass

    def icons(self) -> List[str]:
        return []

    def display_text(self) -> str:
        return ""


GAME_CLASSES = [m[1] for m in inspect.getmembers(sys.modules[__name__], inspect.isclass) if m[1].__module__ == __name__]

StringToClass = {game_cls.__name__: game_cls for game_cls in GAME_CLASSES}
ClassToString = {game_cls: game_cls.__name__ for game_cls in GAME_CLASSES}


