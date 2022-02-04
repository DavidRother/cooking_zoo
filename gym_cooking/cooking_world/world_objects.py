from gym_cooking.cooking_world.abstract_classes import *
from gym_cooking.cooking_world.constants import *
from typing import List


class Floor(StaticObject, ContentObject):

    def __init__(self, unique_id, location):
        super().__init__(unique_id, location, True)

    def accepts(self, dynamic_objects) -> bool:
        return False

    def releases(self) -> bool:
        return True

    def add_content(self, content):
        assert isinstance(content, Agent), f"Floors can only hold Agents as content! not {content}"
        self.content.append(content)

    def file_name(self) -> str:
        return "floor"


class Counter(StaticObject, ContentObject):

    def __init__(self, unique_id, location):
        super().__init__(unique_id, location, False)

    def accepts(self, dynamic_objects) -> bool:
        return True

    def releases(self) -> bool:
        return True

    def add_content(self, content):
        self.content.append(content)

    def file_name(self) -> str:
        return "counter"


class DeliverSquare(StaticObject, ContentObject):

    def __init__(self, unique_id, location):
        super().__init__(unique_id, location, False)

    def accepts(self, dynamic_objects) -> bool:
        return True

    def add_content(self, content):
        self.content.append(content)

    def releases(self) -> bool:
        return True

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

    def accepts(self, dynamic_objects) -> bool:
        return len(dynamic_objects) == 1 and isinstance(dynamic_objects[0], ChopFood)

    def releases(self) -> bool:
        return True

    def add_content(self, content):
        self.content.append(content)

    def file_name(self) -> str:
        return "cutboard"


class Blender(StaticObject, ProgressingObject, ContentObject, ToggleObject, ActionObject):

    def __init__(self, unique_id, location):
        super().__init__(unique_id, location, False)

    def progress(self):
        assert len(self.content) < 2, "Too many Dynamic Objects placed into the Blender"
        if self.content and self.toggle:
            self.content[0].blend()

    def accepts(self, dynamic_objects) -> bool:
        return len(dynamic_objects) == 1 and isinstance(dynamic_objects[0], BlenderFood) and (not self.toggle)

    def releases(self) -> bool:
        return not self.toggle

    def add_content(self, content):
        self.content.append(content)

    def action(self) -> bool:
        self.switch_toggle()
        return True

    def file_name(self) -> str:
        return "blender_on" if self.toggle else "blender3"


class Plate(Container):

    def __init__(self, unique_id, location):
        super().__init__(unique_id, location)

    def add_content(self, content):
        if not isinstance(content, Food):
            raise TypeError(f"Only Food can be added to a plate! Tried to add {content.name()}")
        if not content.done():
            raise Exception(f"Can't add food in unprepared state.")
        self.content.append(content)

    def accepts(self, dynamic_objects) -> bool:
        try:
            return isinstance(dynamic_objects, Food) and dynamic_objects.done()
        except:
            return False

    def releases(self) -> bool:
        return True

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

    def file_name(self) -> str:
        if self.done():
            return "ChoppedOnion"
        else:
            return "FreshOnion"
        

class Tomato(ChopFood):

    def __init__(self, unique_id, location):
        super().__init__(unique_id, location)

    def done(self):
        if self.chop_state == ChopFoodStates.CHOPPED:
            return True
        else:
            return False

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

    def file_name(self) -> str:
        if self.done():
            return "ChoppedLettuce"
        else:
            return "FreshLettuce"


class Carrot(BlenderFood, ChopFood):

    def __init__(self, unique_id, location):
        super().__init__(unique_id, location)

    def done(self):
        if self.chop_state == ChopFoodStates.CHOPPED or self.blend_state == BlenderFoodStates.MASHED:
            return True
        else:
            return False

    def file_name(self) -> str:
        if self.done():
            return "ChoppedCarrot"
        else:
            return "FreshCarrot"


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

    def file_name(self) -> str:
        pass


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

ClassToString = {
    Floor: "Floor",
    Counter: "Counter",
    CutBoard: "CutBoard",
    DeliverSquare: "DeliverSquare",
    Tomato: 'Tomato',
    Lettuce: "Lettuce",
    Onion: "Onion",
    Plate: "Plate",
    Agent: "Agent",
    Blender: "Blender",
    Carrot: "Carrot"
}

GAME_CLASSES = [Floor, Counter, CutBoard, DeliverSquare, Tomato, Lettuce, Onion, Plate, Agent, Blender, Carrot]
GAME_CLASSES_STATE_LENGTH = [(Floor, 1), (Counter, 1), (CutBoard, 1), (DeliverSquare, 1), (Tomato, 2),
                             (Lettuce, 2), (Onion, 2), (Plate, 1), (Agent, 5), (Blender, 1), (Carrot, 3)]


