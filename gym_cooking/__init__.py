from gym.envs.registration import register

register(id="cookingEnv-v0",
         entry_point="gym_cooking.environment:CookingEnvironment")
