from gym_cooking.cooking_world.abstract_classes import *
from gym_cooking.cooking_world.constants import *
from typing import List


class Floor(StaticObject):

    def __init__(self, location):
        super().__init__(location, True)

    def accepts(self, dynamic_objects) -> bool:
        return False


class Counter(StaticObject):

    def __init__(self, location):
        super().__init__(location, False)

    def accepts(self, dynamic_objects) -> bool:
        return True


class DeliverSquare(StaticObject):

    def __init__(self, location):
        super().__init__(location, False)

    def accepts(self, dynamic_objects) -> bool:
        return True


class CutBoard(StaticObject, ActionObject):

    def __init__(self, location):
        super().__init__(location, False)

    def action(self, dynamic_objects: List):
        if len(dynamic_objects) == 1:
            try:
                return dynamic_objects[0].chop()
            except AttributeError:
                return False
        return False

    def accepts(self, dynamic_objects) -> bool:
        return len(dynamic_objects) == 1 and isinstance(dynamic_objects[0], ChopFood)


class Blender(StaticObject, ProgressingObject):

    def __init__(self, location):
        super().__init__(location, False)
        self.content = None

    def progress(self, dynamic_objects):
        assert len(dynamic_objects) < 2, "Too many Dynamic Objects placed into the Blender"
        if not dynamic_objects:
            self.content = None
            return
        elif not self.content:
            self.content = dynamic_objects
        elif self.content:
            if self.content[0] == dynamic_objects[0]:
                self.content[0].blend()
            else:
                self.content = dynamic_objects

    def accepts(self, dynamic_objects) -> bool:
        return len(dynamic_objects) == 1 and isinstance(dynamic_objects[0], BlenderFood)


class Plate(Container):

    def __init__(self, location):
        super().__init__(location)

    def add_content(self, content):
        if not isinstance(content, Food):
            raise TypeError(f"Only Food can be added to a plate! Tried to add {content.name()}")
        if not content.done():
            raise Exception(f"Can't add food in unprepared state.")
        self.content.append(content)


class Onion(ChopFood):

    def __init__(self, location):
        super().__init__(location, ONION_INIT_STATE)


class Tomato(ChopFood):

    def __init__(self, location):
        super().__init__(location, TOMATO_INIT_STATE)


class Lettuce(ChopFood):

    def __init__(self, location):
        super().__init__(location, LETTUCE_INIT_STATE)


class Carrot(BlenderFood):

    def __init__(self, location):
        super().__init__(location, BlenderFoodStates.FRESH)


class Agent(Object):

    def __init__(self, location, color, name):
        super().__init__(location, False, False)
        self.holding = None
        self.color = color
        self.name = name

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


StringToClass = {
    "Floor": Floor,
    "Counter": Counter,
    "CutBoard": CutBoard,
    "DeliverSquare": DeliverSquare,
    "Tomato": Tomato,
    "Lettuce": Lettuce,
    "Onion": Onion,
    "Plate": Plate,
    "Agent": Agent,
    "Blender": Blender,
    "Carrot": Carrot
}

GAME_CLASSES = [Floor, Counter, CutBoard, DeliverSquare, Tomato, Lettuce, Onion, Plate, Agent, Blender]

