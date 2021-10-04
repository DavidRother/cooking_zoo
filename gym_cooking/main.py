import gym

level = "open_room_blender"
seed = 1
record = False
max_steps = 100
recipe = "MashedCarrot"

env = gym.envs.make("gym_cooking:cookingEnv-v1", level=level, record=record, max_steps=max_steps, recipe=recipe)

obs = env.reset()

action_space = env.action_space

done = False

while not done:

    action = action_space.sample()
    observation, reward, done, info = env.step(action)

print('done')
