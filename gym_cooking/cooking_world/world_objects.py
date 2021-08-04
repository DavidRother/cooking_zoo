from gym_cooking.cooking_world.constants import *


class Object:

    def __init__(self, location, movable, walkable):
        self.location = location
        self.movable = movable  # you can pick this one up
        self.walkable = walkable  # you can walk on it

    def name(self) -> str:
        return type(self).__name__


class StaticObject(Object):

    def __init__(self, location, walkable):
        super().__init__(location, False, walkable)


class DynamicObject(Object):

    def __init__(self, location):
        super().__init__(location, True, False)


class Counter(StaticObject):

    def __init__(self, location):
        super().__init__(location, False)


class DeliverSquare(StaticObject):

    def __init__(self, location):
        super().__init__(location, False)


class CutBoard(StaticObject):

    def __init__(self, location):
        super().__init__(location, True)


class Container(DynamicObject):

    def __init__(self, location, content=None):
        super().__init__(location)
        self.content = content or []


class Food(DynamicObject):

    def __init__(self, location, food_state, chop_allowed):
        super().__init__(location)
        self.state = food_state
        self.chop_allowed = chop_allowed


class Onion(Food):

    def __init__(self, location):
        super().__init__(location, ONION_INIT_STATE, True)


class Tomato(Food):

    def __init__(self, location):
        super().__init__(location, TOMATO_INIT_STATE, True)


class Lettuce(Food):

    def __init__(self, location):
        super().__init__(location, LETTUCE_INIT_STATE, True)








