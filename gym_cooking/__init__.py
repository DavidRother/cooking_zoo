from gym.envs.registration import register

register(id="cookingEnv-v0",
         entry_point="gym_cooking.environment:CookingEnvironment")
register(id="cookingEnv-v1",
         entry_point="gym_cooking.environment:GymCookingEnvironment")
register(id="cookingZooEnv-v0",
         entry_point="gym_cooking.environment:CookingZooEnvironment")
