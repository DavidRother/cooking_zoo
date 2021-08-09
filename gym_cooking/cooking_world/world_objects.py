from gym_cooking.cooking_world.AbstractClasses import *
from gym_cooking.cooking_world.constants import *
from typing import List


class Floor(StaticObject):

    def __init__(self, location):
        super().__init__(location, True)


class Counter(StaticObject):

    def __init__(self, location):
        super().__init__(location, False)


class DeliverSquare(StaticObject):

    def __init__(self, location):
        super().__init__(location, False)


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


class Blender(StaticObject, ProgressingObject):

    def __init__(self, location):
        super().__init__(location, False)
        self.countdown = -1
        self.content = None

    def progress(self):
        if not self.content or self.content.done() or self.countdown <= 0:
            return
        self.countdown -= 1
        if self.countdown == 0:
            self.content.chop()

    def place(self, obj):
        self.content = obj
        self.countdown = 10

    def take(self):
        self.countdown = -1
        tmp = self.content
        self.content = None
        return tmp


class Plate(Container):

    def __init__(self, location):
        super().__init__(location)

    def add_content(self, content):
        if not isinstance(content, Food):
            raise TypeError(f"Only Food can be added to a plate! Tried to add {content.name()}")
        if not content.state == ChopFoodStates.CHOPPED:
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
    "Blender": Blender
}



