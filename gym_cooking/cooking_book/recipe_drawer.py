from gym_cooking.cooking_world.world_objects import *
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
ChoppedLettuce = RecipeNode(root_type=Lettuce, id_num=next(id_generator), name="Lettuce",
                            conditions=[("state", ChopFoodStates.CHOPPED)])
ChoppedOnion = RecipeNode(root_type=Onion, id_num=next(id_generator), name="Onion",
                          conditions=[("state", ChopFoodStates.CHOPPED)])
ChoppedTomato = RecipeNode(root_type=Tomato, id_num=next(id_generator), name="Tomato",
                           conditions=[("state", ChopFoodStates.CHOPPED)])
MashedCarrot = RecipeNode(root_type=Carrot, id_num=next(id_generator), name="Carrot",
                           conditions=[("state", BlenderFoodStates.MASHED)])

# Salad Plates
TomatoSaladPlate = RecipeNode(root_type=Plate, id_num=next(id_generator), name="Plate", conditions=None,
                              contains=[ChoppedTomato])
TomatoLettucePlate = RecipeNode(root_type=Plate, id_num=next(id_generator), name="Plate", conditions=None,
                                contains=[ChoppedTomato, ChoppedLettuce])
CarrotPlate = RecipeNode(root_type=Plate, id_num=next(id_generator), name="Plate", conditions=None,
                         contains=[MashedCarrot])

# Delivered Salads
TomatoSalad = RecipeNode(root_type=DeliverSquare, id_num=next(id_generator), name="DeliverSquare", conditions=None,
                         contains=[TomatoSaladPlate])
TomatoLettuceSalad = RecipeNode(root_type=DeliverSquare, id_num=next(id_generator), name="DeliverSquare",
                                conditions=None, contains=[TomatoLettucePlate])
MashedCarrot = RecipeNode(root_type=DeliverSquare, id_num=next(id_generator), name="DeliverSquare",
                          conditions=None, contains=[CarrotPlate])

# this one increments one further and is thus the amount of ids we have given since
# we started counting at zero.
NUM_GOALS = next(id_generator)

RECIPES = {"TomatoSalad": lambda: deepcopy(Recipe(TomatoSalad)),
           "TomatoLettuceSalad": lambda: deepcopy(Recipe(TomatoLettuceSalad)),
           "MashedCarrot": lambda: deepcopy(Recipe(MashedCarrot))}
