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
                            conditions=[("chop_state", ChopFoodStates.CHOPPED)])
ChoppedOnion = RecipeNode(root_type=Onion, id_num=next(id_generator), name="Onion",
                          conditions=[("chop_state", ChopFoodStates.CHOPPED)])
ChoppedTomato = RecipeNode(root_type=Tomato, id_num=next(id_generator), name="Tomato",
                           conditions=[("chop_state", ChopFoodStates.CHOPPED)])
MashedCarrot = RecipeNode(root_type=Carrot, id_num=next(id_generator), name="Carrot",
                          conditions=[("blend_state", BlenderFoodStates.MASHED)])

# Salad Plates
TomatoSaladPlate = RecipeNode(root_type=Plate, id_num=next(id_generator), name="Plate", conditions=None,
                              contains=[ChoppedTomato])
TomatoLettucePlate = RecipeNode(root_type=Plate, id_num=next(id_generator), name="Plate", conditions=None,
                                contains=[ChoppedTomato, ChoppedLettuce])
TomatoLettuceOnionPlate = RecipeNode(root_type=Plate, id_num=next(id_generator), name="Plate", conditions=None,
                                     contains=[ChoppedTomato, ChoppedLettuce, ChoppedOnion])
CarrotPlate = RecipeNode(root_type=Plate, id_num=next(id_generator), name="Plate", conditions=None,
                         contains=[MashedCarrot])

# Delivered Salads
TomatoSalad = RecipeNode(root_type=Deliversquare, id_num=next(id_generator), name="Deliversquare", conditions=None,
                         contains=[TomatoSaladPlate])
TomatoLettuceSalad = RecipeNode(root_type=Deliversquare, id_num=next(id_generator), name="Deliversquare",
                                conditions=None, contains=[TomatoLettucePlate])
TomatoLettuceOnionSalad = RecipeNode(root_type=Deliversquare, id_num=next(id_generator), name="Deliversquare",
                                     conditions=None, contains=[TomatoLettuceOnionPlate])
MashedCarrot = RecipeNode(root_type=Deliversquare, id_num=next(id_generator), name="Deliversquare",
                          conditions=None, contains=[CarrotPlate])

floor = RecipeNode(root_type=Floor, id_num=next(id_generator), name="Floor", conditions=None, contains=[])
no_recipe_node = RecipeNode(root_type=Deliversquare, id_num=next(id_generator), name='Deliversquare', conditions=None, contains=[floor])

# this one increments one further and is thus the amount of ids we have given since
# we started counting at zero.
NUM_GOALS = next(id_generator)

RECIPES = {"TomatoSalad": lambda: deepcopy(Recipe(TomatoSalad)),
           "TomatoLettuceSalad": lambda: deepcopy(Recipe(TomatoLettuceSalad)),
           "TomatoLettuceOnionSalad": lambda: deepcopy(Recipe(TomatoLettuceOnionSalad)),
           "MashedCarrot": lambda: deepcopy(Recipe(MashedCarrot)),
           "no_recipe": lambda: deepcopy(Recipe(no_recipe_node))
           }
