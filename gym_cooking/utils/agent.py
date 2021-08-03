# Recipe planning
from gym_cooking.recipe_planner.stripsworld import STRIPSWorld
import gym_cooking.recipe_planner.utils as recipe_utils
from gym_cooking.recipe_planner.utils import *

# Other core modules
from gym_cooking.utils.core import Counter, Cutboard
from gym_cooking.utils.utils import agent_settings

import numpy as np
import copy
from termcolor import colored as color
from collections import namedtuple

AgentRepr = namedtuple("AgentRepr", "name location holding")

# Colors for agents.
COLORS = ['blue', 'magenta', 'yellow', 'green']


class RealAgent:
    """Real Agent object that performs task inference and plans."""

    def __init__(self, arglist, name, id_color, recipes):
        self.arglist = arglist
        self.name = name
        self.color = id_color
        self.recipes = recipes

        # Bayesian Delegation.
        self.new_subtask = None
        self.new_subtask_agent_names = []
        self.incomplete_subtasks = []
        self.signal_reset_delegator = False
        self.is_subtask_complete = lambda w: False
        self.beta = arglist.beta
        self.none_action_prob = 0.5

        self.model_type = agent_settings(arglist, name)
        if self.model_type == "up":
            self.priors = 'uniform'
        else:
            self.priors = 'spatial'

        # Navigation planner.
        self.planner = E2E_BRTDP(
                alpha=arglist.alpha,
                tau=arglist.tau,
                cap=arglist.cap,
                main_cap=arglist.main_cap)

    def __str__(self):
        return color(self.name[-1], self.color)


class SimAgent:
    """Simulation agent used in the environment object."""

    def __init__(self, name, id_color, location):
        self.name = name
        self.color = id_color
        self.location = location
        self.holding = None
        self.action = (0, 0)
        self.has_delivered = False

    def __str__(self):
        return color(self.name[-1], self.color)

    def __copy__(self):
        a = SimAgent(name=self.name, id_color=self.color, location=self.location)
        a.__dict__ = self.__dict__.copy()
        if self.holding is not None:
            a.holding = copy.copy(self.holding)
        return a

    def get_repr(self):
        return AgentRepr(name=self.name, location=self.location, holding=self.get_holding())

    def get_holding(self):
        if self.holding is None:
            return 'None'
        return self.holding.full_name

    def print_status(self):
        print("{} currently at {}, action {}, holding {}".format(
                color(self.name, self.color),
                self.location,
                self.action,
                self.get_holding()))

    def acquire(self, obj):
        if self.holding is None:
            self.holding = obj
            self.holding.is_held = True
            self.holding.location = self.location
        else:
            self.holding.merge(obj) # Obj(1) + Obj(2) => Obj(1+2)

    def release(self):
        self.holding.is_held = False
        self.holding = None

    def move_to(self, new_location):
        self.location = new_location
        if self.holding is not None:
            self.holding.location = new_location
