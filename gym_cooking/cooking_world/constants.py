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

class SpaghettiStates(Enum):
    RAW = "Raw"
    COOKED = "Cooked"


ONION_INIT_STATE = ChopFoodStates.FRESH
TOMATO_INIT_STATE = ChopFoodStates.FRESH
LETTUCE_INIT_STATE = ChopFoodStates.FRESH


class Temperature(Enum):
    FREEZING = -10
    COLD = 0
    MILD = 21
    BOILING = 100
    HOT = 200





