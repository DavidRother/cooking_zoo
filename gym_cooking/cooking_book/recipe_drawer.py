from gym_cooking.utils.core import *
from gym_cooking.cooking_book.recipe import Recipe, RecipeNode


def id_num_generator():
    num = 0
    while True:
        yield num
        num += 1


id_generator = id_num_generator()

#  Basic food Items

ChoppedLettuce = RecipeNode(root=Lettuce, id_num=next(id_generator), conditions=[("state", FoodState.CHOPPED)])
ChoppedOnion = RecipeNode(root=Onion, id_num=next(id_generator), conditions=[("state", FoodState.CHOPPED)])
ChoppedTomato = RecipeNode(root=Tomato, id_num=next(id_generator), conditions=[("state", FoodState.CHOPPED)])

# Salad Plates
TomatoSaladPlate = RecipeNode(root=Plate, id_num=next(id_generator), conditions=None, contains=[ChoppedTomato])
TomatoLettucePlate = RecipeNode(root=Plate, id_num=next(id_generator), conditions=None,
                                contains=[ChoppedTomato, ChoppedLettuce])

# Delivered Salads
TomatoSalad = RecipeNode(root=Delivery, id_num=next(id_generator), conditions=None, contains=[TomatoSaladPlate])
TomatoLettuceSalad = RecipeNode(root=Delivery, id_num=next(id_generator), conditions=None,
                                contains=[TomatoLettucePlate])

# this one increments one further and is thus the amount of ids we have given since
# we started counting at zero.
num_ids = next(id_generator)

recipes = {"TomatoSalad": Recipe(TomatoSalad), "TomatoLettuceSalad": Recipe(TomatoLettuceSalad)}
