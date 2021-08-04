# Other core modules
from gym_cooking.utils.interact import interact
from gym_cooking.utils.world import World
from gym_cooking.utils.core import *
from gym_cooking.utils.agent import SimAgent
from gym_cooking.misc.game.gameimage import GameImage
from gym_cooking.utils.agent import COLORS
from gym_cooking.cooking_book.recipe_drawer import RECIPES, NUM_GOALS

import copy
import numpy as np
from pathlib import Path
import os.path
from itertools import combinations, product
from collections import namedtuple

import gym


CollisionRepr = namedtuple("CollisionRepr", "time agent_names agent_locations")


class OvercookedEnvironment(gym.Env):
    """Environment object for Overcooked."""

    def __init__(self, level, num_agents, seed, playable, record, max_num_timesteps, recipes):
        self.level = level
        self.num_agents = num_agents
        self.seed = seed
        self.playable = playable
        self.record = record
        self.max_num_timesteps = max_num_timesteps
        self.t = 0
        self.filename = ""
        self.set_filename()
        self.world = None
        self.recipes = recipes
        self.sim_agents = []
        self.agent_actions = {}
        self.game = None
        self.distances = {}
        self.recipe_graphs = [RECIPES[recipe]() for recipe in recipes]

        # For visualizing episode.
        self.rep = []

        # For tracking data during an episode.
        self.collisions = []
        self.termination_info = ""
        self.successful = False
        self.verbose = False
        self.graph_representation_length = sum([len(tup[1]) if tup[1] else 1 for tup in GAME_OBJECTS_STATEFUL])

    def __str__(self):
        # Print the world and agents.
        _display = list(map(lambda x: ''.join(map(lambda y: y + ' ', x)), self.rep))
        return '\n'.join(_display)

    def __copy__(self):
        new_env = OvercookedEnvironment(self.level, self.num_agents, self.seed, self.playable, self.record,
                                        self.max_num_timesteps, self.recipes)
        new_env.__dict__ = self.__dict__.copy()
        new_env.world = copy.copy(self.world)
        new_env.sim_agents = [copy.copy(a) for a in self.sim_agents]
        new_env.distances = self.distances

        # Make sure new objects and new agents' holdings have the right pointers.
        for a in new_env.sim_agents:
            if a.holding is not None:
                a.holding = new_env.world.get_object_at(
                        location=a.location,
                        desired_obj=None,
                        find_held_objects=True)
        return new_env

    def set_filename(self):
        self.filename = f"{self.level}_agents{self.num_agents}_seed{self.seed}"

    def load_level(self, level, num_agents):
        x = 0
        y = 0
        my_path = os.path.realpath(__file__)
        dir_name = os.path.dirname(my_path)
        path = Path(dir_name)
        parent = path.parent / f"utils/levels/{level}.txt"
        # print(parent)
        with parent.open("r") as file:
            # Mark the phases of reading.
            phase = 1
            for line in file:
                line = line.strip('\n')
                if line == '':
                    phase += 1

                # Phase 1: Read in kitchen map.
                elif phase == 1:
                    for x, rep in enumerate(line):
                        # Object, i.e. Tomato, Lettuce, Onion, or Plate.
                        if rep in 'tlop':
                            counter = Counter(location=(x, y))
                            obj = RepToClass[rep](location=(x, y), contents=[])
                            counter.acquire(obj=obj)
                            self.world.insert(obj=counter)
                            self.world.insert(obj=obj)
                        # GridSquare, i.e. Floor, Counter, Cutboard, Delivery.
                        elif rep in RepToClass:
                            newobj = RepToClass[rep](location=(x, y))
                            self.world.insert(obj=newobj)
                        else:
                            # Empty. Set a Floor tile.
                            floor = Floor(location=(x, y))
                            self.world.insert(obj=floor)
                    y += 1
                # Phase 2: Read in recipe list.
                elif phase == 2:
                    # self.recipes.append(RecipeStore[line]())
                    pass

                # Phase 3: Read in agent locations (up to num_agents).
                elif phase == 3:
                    if len(self.sim_agents) < num_agents:
                        loc = line.split(' ')
                        sim_agent = SimAgent(
                                name='agent-'+str(len(self.sim_agents)+1),
                                id_color=COLORS[len(self.sim_agents)],
                                location=(int(loc[0]), int(loc[1])))
                        self.sim_agents.append(sim_agent)

        self.distances = {}
        self.world.width = x+1
        self.world.height = y
        self.world.perimeter = 2*(self.world.width + self.world.height)

    def reset(self):
        self.world = World(self.playable)
        self.sim_agents = []
        self.agent_actions = {}
        self.t = 0

        # For visualizing episode.
        self.rep = []

        # For tracking data during an episode.
        self.collisions = []
        self.termination_info = ""
        self.successful = False

        # Load world & distances.
        self.load_level(
                level=self.level,
                num_agents=self.num_agents)
        self.world.make_loc_to_gridsquare()

        # if self.arglist.record or self.arglist.with_image_obs:
        self.game = GameImage(
                filename=self.filename,
                world=self.world,
                sim_agents=self.sim_agents,
                record=self.record)
        self.game.on_init()
        if self.record:
            self.game.save_image_obs(self.t)

        # Get an image observation
        # image_obs = self.game.get_image_obs()
        tensor_obs = self.get_tensor_representation()

        # new_obs = copy.copy(self)
        done, rewards, goals = self.compute_rewards()
        info = {"t": self.t, "agent_locations": [agent.location for agent in self.sim_agents],
                "tensor_obs": tensor_obs,
                "done": done, "termination_info": self.termination_info, "rewards": rewards, "goals": goals}

        return copy.copy(self), info

    def close(self):
        return

    def step(self, action_dict):
        # Track internal environment info.
        self.t += 1
        if self.verbose:
            print("===============================")
            print("[environment.step] @ TIMESTEP {}".format(self.t))
            print("===============================")

        # Get actions.
        for sim_agent in self.sim_agents:
            sim_agent.action = action_dict[sim_agent.name]

        # Check collisions.
        self.check_collisions()

        # Execute.
        self.execute_navigation()

        # Visualize.
        self.display()
        self.game.on_render()
        if self.verbose:
            self.print_agents()
        if self.record:
            self.game.save_image_obs(self.t)

        # Get an image observation
        # image_obs = self.game.get_image_obs()
        tensor_obs = self.get_tensor_representation()

        done, rewards, goals = self.compute_rewards()
        info = {"t": self.t, "agent_locations": [agent.location for agent in self.sim_agents],
                "tensor_obs": tensor_obs,
                "done": done, "termination_info": self.termination_info, "rewards": rewards, "goals": goals}
        return tensor_obs, sum(rewards), done, info

    def compute_rewards(self):
        done = False
        rewards = [0] * len(self.recipes)
        open_goals = [[0]] * len(self.recipes)
        # Done if the episode maxes out
        if self.t >= self.max_num_timesteps and self.max_num_timesteps:
            self.termination_info = f"Terminating because passed {self.max_num_timesteps} timesteps"
            self.successful = False
            done = True

        for idx, recipe in enumerate(self.recipe_graphs):
            goals_before = recipe.goals_completed(NUM_GOALS)
            recipe.update_recipe_state(self.world)
            open_goals[idx] = recipe.goals_completed(NUM_GOALS)
            bonus = recipe.completed() * 10
            rewards[idx] = sum(goals_before) - sum(open_goals[idx]) + bonus

        if all((recipe.completed() for recipe in self.recipe_graphs)):
            self.termination_info = "Terminating because all deliveries were completed"
            self.successful = True
            done = True
        return done, rewards, open_goals

    def get_tensor_representation(self):
        tensor = np.zeros((self.world.width, self.world.height, self.graph_representation_length))
        objects = {"Player": self.sim_agents}
        objects.update(self.world.objects)
        # for idx, (name, states) in enumerate(GAME_OBJECTS_STATEFUL):
        #     try:
        #         object_types_to_search = [key_type for key_type in self.world.objects.keys() if name in key_type]
        #         for obj_type in object_types_to_search:
        #             for obj in self.world.objects[obj_type]:
        #                 if not states:
        #                     x, y = obj.location
        #                     tensor[x, y, idx] += 1
        #                 else:
        #                     for state in states:
        #                         search_object = next(
        #                             (value for value in world_object.contents if isinstance(value, node.root_type)))
        #     except KeyError:
        #         continue
        return tensor

    def print_agents(self):
        for sim_agent in self.sim_agents:
            sim_agent.print_status()

    def display(self):
        self.update_display()

        if self.verbose:
            print(str(self))

    def update_display(self):
        self.rep = self.world.update_display()
        for agent in self.sim_agents:
            x, y = agent.location
            self.rep[y][x] = str(agent)

    def get_agent_names(self):
        return [agent.name for agent in self.sim_agents]

    def is_collision(self, agent1_loc, agent2_loc, agent1_action, agent2_action):
        """Returns whether agents are colliding.

        Collisions happens if agent collide amongst themselves or with world objects."""
        # Tracks whether agents can execute their action.
        execute = [True, True]

        # Collision between agents and world objects.
        agent1_next_loc = tuple(np.asarray(agent1_loc) + np.asarray(agent1_action))
        if self.world.get_gridsquare_at(location=agent1_next_loc).collidable:
            # Revert back because agent collided.
            agent1_next_loc = agent1_loc

        agent2_next_loc = tuple(np.asarray(agent2_loc) + np.asarray(agent2_action))
        if self.world.get_gridsquare_at(location=agent2_next_loc).collidable:
            # Revert back because agent collided.
            agent2_next_loc = agent2_loc

        # Inter-agent collision.
        if agent1_next_loc == agent2_next_loc:
            if agent1_next_loc == agent1_loc and agent1_action != (0, 0):
                execute[1] = False
            elif agent2_next_loc == agent2_loc and agent2_action != (0, 0):
                execute[0] = False
            else:
                execute[0] = False
                execute[1] = False

        # Prevent agents from swapping places.
        elif ((agent1_loc == agent2_next_loc) and
                (agent2_loc == agent1_next_loc)):
            execute[0] = False
            execute[1] = False
        return execute

    def check_collisions(self):
        """Checks for collisions and corrects agents' executable actions.

        Collisions can either happen amongst agents or between agents and world objects."""
        execute = [True] * len(self.sim_agents)

        # Check each pairwise collision between agents.
        for i, j in combinations(range(len(self.sim_agents)), 2):
            agent_i, agent_j = self.sim_agents[i], self.sim_agents[j]
            exec_ = self.is_collision(
                    agent1_loc=agent_i.location,
                    agent2_loc=agent_j.location,
                    agent1_action=agent_i.action,
                    agent2_action=agent_j.action)

            # Update exec array and set path to do nothing.
            execute[i] = exec_[0]
            execute[j] = exec_[1]

            # Track collisions.
            if not all(exec_):
                collision = CollisionRepr(
                        time=self.t,
                        agent_names=[agent_i.name, agent_j.name],
                        agent_locations=[agent_i.location, agent_j.location])
                self.collisions.append(collision)

        if self.verbose:
            print('\nexecute array is:', execute)

        # Update agents' actions if collision was detected.
        for i, agent in enumerate(self.sim_agents):
            if not execute[i]:
                agent.action = (0, 0)

            if self.verbose:
                print(f"{color(agent.name, agent.color)} has action {agent.action}")

    def execute_navigation(self):
        for agent in self.sim_agents:
            interact(agent=agent, world=self.world)
            self.agent_actions[agent.name] = agent.action

    def render(self, mode='human'):
        pass

