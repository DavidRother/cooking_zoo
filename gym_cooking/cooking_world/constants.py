from enum import Enum


class ChopFoodStates(Enum):
    FRESH = "Fresh"
    CHOPPED = "Chopped"


class BlenderFoodStates(Enum):
    FRESH = "Fresh"
    IN_PROGRESS = "InProgress"
    MASHED = "Mashed"


class ToasterFoodStates(Enum):
    FRESH = "Fresh"
    READY = "Ready"
    IN_PROGRESS = "InProgress"
    TOASTED = "Toasted"


class MicrowaveFoodStates(Enum):
    FRESH = "Fresh"
    READY = "Ready"
    IN_PROGRESS = "InProgress"
    HOT = "Hot"


class PotFoodStates(Enum):
    FRESH = "Fresh"
    READY = "Ready"
    IN_PROGRESS = "InProgress"
    COOKED = "Cooked"


# add foodstates, tempstates, and more?, basic attributes to all foods automatically?
class FoodStates(Enum):
    RAW = "Raw"
    FRESH = "Fresh"
    COOKED = "Cooked"
    ROTTEN = "Rotten"


# status of action objects, if they can be used
class ActionObjectState(Enum):
    READY = "Ready"
    NOT_USABLE = "NotUsable"


class Temperature(Enum):
    FREEZING = -10
    COLD = 0
    MILD = 21
    EATABLE = 60
    BOILING = 100
    HOT = 200


ONION_INIT_STATE = ChopFoodStates.FRESH
TOMATO_INIT_STATE = ChopFoodStates.FRESH
LETTUCE_INIT_STATE = ChopFoodStates.FRESH




