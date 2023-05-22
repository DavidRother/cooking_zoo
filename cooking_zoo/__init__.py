from gymnasium.envs.registration import register

register(id="cookingEnv-v1",
         entry_point="cooking_zoo.environment:GymCookingEnvironment")
register(id="cookingEnvMA-v1",
         entry_point="cooking_zoo.environment:GymCookingEnvironmentMA")
register(id="cookingZooEnv-v0",
         entry_point="cooking_zoo.environment:CookingZooEnvironment")
