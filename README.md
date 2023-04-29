# Code for CookingZoo

Contents:
- [Introduction](#introduction)
- [Installation](#installation)
- [Usage](#usage)
- [Extending The Environment](#extending-the-environment)

## Introduction

CookingZoo is a derived work and reuse part of the visual assets.
It is a flexible cooking environment with a lot of different cooking tools and ingredients to test
generalization abilities. It offers multi-agent support with the PettingZoo library and the gymnasium library. 
Furthermore, one agent may be controlled by a human.

The advantages of using this environment are listed below:

```
- Extensive Library of existing recipes and room with extensibility to add more
- Different Observation spaces (Feature Vector, symbolic)
- Customizable Level design
- Observation spaces can be same size for different levels with fixed object location
- Variable number of agents
- Cover Competing, Collaborating and Coexisting Environments
- Multi-agent support with PettingZoo and gymnasium latest versions
- Human controllable agent
```
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
Another citation for the original paper will follow shortly here, 
which should please be cited after publication.

```
```

## Installation

```
git clone https://github.com/DavidRother/cooking_zoo.git
cd cooking_zoo
pip3 install -e .
```

The environment is compatible with python 3.7 and higher.

## Usage 

```python
# Example Parameters for two agents
num_agents = 2
max_steps = 400
render = True
obs_spaces = ["feature_vector", "feature_vector"]
action_scheme = "scheme3"
meta_file = "example"
level = "coop_test"
recipes = ["TomatoLettuceSalad", "CarrotBanana"]
end_condition_all_dishes = True
agent_visualization = ["human", "robot"]
reward_scheme = {"recipe_reward": 20, "max_time_penalty": -5, "recipe_penalty": -40, "recipe_node_reward": 0}


# Single Agent gym environment
env = gym.envs.make("cooking_zoo:cookingEnvMA-v1", level=level, meta_file=meta_file, num_agents=num_agents,
                    max_steps=max_steps, recipes=recipes, agent_visualization=agent_visualization,
                    obs_spaces=obs_spaces, end_condition_all_dishes=end_condition_all_dishes,
                    action_scheme=action_scheme, render=render, reward_scheme=reward_scheme)

# Multi Agent gym environment
env = gym.envs.make("cooking_zoo:cookingEnv-v1", level=level, meta_file=meta_file,
                    max_steps=max_steps, recipes=recipes, agent_visualization=agent_visualization,
                    obs_spaces=obs_spaces, end_condition_all_dishes=end_condition_all_dishes,
                    action_scheme=action_scheme, render=render, reward_scheme=reward_scheme)

# Multi Agent PettingZoo environment
env = parallel_env(level=level, meta_file=meta_file, num_agents=num_agents, max_steps=max_steps, recipes=recipes,
                   agent_visualization=agent_visualization, obs_spaces=obs_spaces,
                   end_condition_all_dishes=end_condition_all_dishes, action_scheme=action_scheme, render=render,
                   reward_scheme=reward_scheme)
```

The environment can be used as a gym environment and as a PettingZoo environment. PettingZoo is 
a multi-agent environment library and is compatible with big frameworks such as 
[RLLib](https://docs.ray.io/en/latest/rllib/index.html), [StableBaselines3](https://stable-baselines3.readthedocs.io/en/master/),
[PettingZoo](https://www.pettingzoo.ml/), [EPyMARL](https://github.com/uoe-agents/epymarl), 
[MushroomRL](https://github.com/MushroomRL/mushroom-rl), and others that support the gym single-agent interface, 
the gym multi-agent convention as found in EPyMARL or the more general PettingZoo interface.

Please note that we use the updated gym conventions of version 0.26.1 and upwards, where done is replaced with 
termination and truncation variables. During test a small wrapper was necessary with EPyMARL for 
compatibility reasons.

A single-agent usage example is shown in the main.py file.
To get a playable demo in a single agent environment view the demo_gameplay.py file
and for a playable multi-agent demo, where another agent is controlled by a random movement AI view 
the demo_multiplayer_gameplay.py file.

## Observation Spaces

# Feature Vector
a numpy vector containing a feature representation of all objects in the world

# Symbolic
A copy of all objects in the world for reasoning purposes

## Extending the environment

In this section it is described how to add additional objects and make changes 
to the code to fit the simulation to your needs.

### Adding Objects

Look up the file world_objects.py in the folder cooking_world.
In this file add a new class of your object and let it inherit from the desired classes in abstract_classes.py.
To get specific implementation details you can look at another inherited objects. 


### Recipes

A recipe is a graph in this game. Everything related to recipes is found in the folder cooking_book.
A recipe node describes a state in the world that is desired and is fulfilled when it is reached. 
More concrete a node takes as input an object type, the conditions for the attributes of that object and
what should be on/in the object (if applicable). If an object of the correct object type then fulfills all 
specified conditions and holds all specified objects (described as nodes), then the node is considered done.

By chaining different nodes now in the contains section you get a graph that the game can check if it is fulfilled 
or not and hand out rewards for each node.

To add a new recipe add the node call the register_recipe function in the recipe_book.py file.
If you want to add to the default recipe book directly add the recipe in the files.



