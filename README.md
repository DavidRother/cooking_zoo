# Code for CookingZoo

Contents:
- [Introduction](#introduction)
- [Installation](#installation)
- [Usage](#usage)
- [Extending The Environment](#extending-the-environment)

## Introduction

CookingZoo is a derived work, where we were inspired by this work and reuse the visualization.
It is a flexible cooking environment with a lot of different cooking tools and ingredients to test
generalization abilities. It offers multi-agent support with the PettingZoo library and single-agent support 
via the gym library. Furthermore, one agent may be controlled by a human, while the others can be controlled 
by a custom policy.

You can use this bibtex if you would like to cite the original paper this fork is derived from (Wu and Wang et al., 2021):
```
@article{wu_wang2021too,
  author = {Wu, Sarah A. and Wang, Rose E. and Evans, James A. and Tenenbaum, Joshua B. and Parkes, David C. and Kleiman-Weiner, Max},
  title = {Too many cooks: Coordinating multi-agent collaboration through inverse planning},
  journal = {Topics in Cognitive Science},
  year = {2021},
  volume = {n/a},
  number = {n/a},
  keywords = {Coordination, Social learning, Inverse planning, Bayesian inference, Multi-agent reinforcement learning},
  doi = {https://doi.org/10.1111/tops.12525},
  url = {https://onlinelibrary.wiley.com/doi/abs/10.1111/tops.12525},
}
```

## Installation

You can install the dependencies with `pip3`:
```
git clone https://github.com/DavidRother/gym-cooking.git
cd gym-cooking
pip3 install -e .
```

The environment is compatible with python 3.7 and higher.

## Usage 

The environment can be used as a gym environment and as a PettingZoo environment. PettingZoo is 
a multi-agent environment library and is compatible with big frameworks such as RLLib.

A single-agent usage example is shown in the main.py file.
To get a playable demo in a single agent environment view the demo_gameplay.py file
and for a playable multi-agent demo, where another agent is controlled by a random movement AI view 
the demo_multiplayer_gameplay.py file.

## Extending the environment

In this section it is described how to add additional objects and make changes 
to the code to fit the simulation to your needs.

### Adding Objects

Look up the file world_objects.py in the folder cooking_world.
In this file add a new class of your object and let it inherit from the desired class in abstract_classes.py.
To get specific implementation details you can look at another inherited object class. 

Then add a new entry to the StringToClass dictionary and the class to the GAME_CLASSES and the GAME_CLASSES_STATE_LENGTH 
list at the bottom of the world_objects.py file. The GAME_CLASSES_STATE_LENGTH List contains tuples with the class and 
the corresponding state length for the feature matrix representation.

### Recipes

A recipe is a graph in this game. Everything related to recipes is found in the folder cooking_book.
A recipe node describes a state in the world that is desired and is fulfilled when it is reached. 
More concrete a node takes as input an object type, the conditions for the attributes of that object and
what should be on/in the object (if applicable). If an object of the correct object type then fulfills all 
specified conditions and holds all specified objects (described as nodes), then the node is considered done.

By chaining different nodes now in the contains section you get a graph that the game can check if it is fulfilled 
or not and hand out rewards for each node.

To add a new recipe add the node with the desired name in the recipe_drawer.py file in the RECIPES dictionary
as is done for the other recipes.



