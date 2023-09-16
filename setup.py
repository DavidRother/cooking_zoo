from setuptools import setup, find_packages

setup(name='cooking_zoo',
      version='1.0.1',
      description='Cooking gym with graphics and ideas based on: "Too Many Cooks: Overcooked environment"',
      author='David Rother',
      email='david.rother@tu-darmstadt.de',
      packages=find_packages() + [""],
      python_requires='>3.7',
      install_requires=[
            'numpy',
            'pygame',
            'pettingzoo>=1.24',
            'Pillow',
            'Gymnasium>=0.26'
      ]
      )
