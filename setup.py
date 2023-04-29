from setuptools import setup, find_packages

setup(name='cooking-gym',
      version='0.0.1',
      description='Cooking gym with graphics and ideas based on: "Too Many Cooks: Overcooked environment"',
      author='David Rother',
      email='david.rother@tu-darmstadt.de',
      packages=find_packages() + [""],
      python_requires='>3.7',
      install_requires=[
            'gym',
            'numpy',
            'pygame',
            'pettingzoo',
            'Pillow',
            'Gymnasium'
      ]
      )
