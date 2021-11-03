from setuptools import setup, find_packages

setup(name='cooking-gym',
      version='0.0.1',
      description='Cooking gym with graphics and ideas based on: "Too Many Cooks: Overcooked environment"',
      author='David Rother, Rose E. Wang',
      email='david@edv-drucksysteme.de',
      packages=find_packages() + [""],
      install_requires=[
            'gym==0.19.0',
            'numpy>=1.21.2',
            'pygame==2.0.1',
            'pettingzoo==1.11.2'
      ]
      )
