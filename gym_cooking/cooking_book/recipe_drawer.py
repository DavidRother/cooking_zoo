from gym_cooking.utils.core import *
from gym_cooking.cooking_book.recipe import Recipe, RecipeNode
from copy import deepcopy


def id_num_generator():
    num = 0
    while True:
        yield num
        num += 1


id_generator = id_num_generator()

#  Basic food Items
# root_type, id_num, parent=None, conditions=None, contains=None
ChoppedLettuce = RecipeNode(root_type=Lettuce, id_num=next(id_generator), conditions=[("state", FoodState.CHOPPED)])
ChoppedOnion = RecipeNode(root_type=Onion, id_num=next(id_generator), conditions=[("state", FoodState.CHOPPED)])
ChoppedTomato = RecipeNode(root_type=Tomato, id_num=next(id_generator), conditions=[("state", FoodState.CHOPPED)])

# Salad Plates
TomatoSaladPlate = RecipeNode(root_type=Plate, id_num=next(id_generator), conditions=None, contains=[ChoppedTomato])
TomatoLettucePlate = RecipeNode(root_type=Plate, id_num=next(id_generator), conditions=None,
                                contains=[ChoppedTomato, ChoppedLettuce])

# Delivered Salads
TomatoSalad = RecipeNode(root_type=Delivery, id_num=next(id_generator), conditions=None, contains=[TomatoSaladPlate])
TomatoLettuceSalad = RecipeNode(root_type=Delivery, id_num=next(id_generator), conditions=None,
                                contains=[TomatoLettucePlate])

# this one increments one further and is thus the amount of ids we have given since
# we started counting at zero.
NUM_GOALS = next(id_generator)

RECIPES = {"TomatoSalad": lambda: deepcopy(Recipe(TomatoSalad)),
           "TomatoLettuceSalad": lambda: deepcopy(Recipe(TomatoLettuceSalad))}
