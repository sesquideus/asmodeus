# What is it?

## Installation
ASMODEUS requires GNU/Linux operating system and a Python interpreter `>3.7`.
We recommend using `pipenv` to manage a virtual environment. After cloning the repository
and installing `pipenv`, run

    > pipenv sync
  
to collect and install correct versions of dependencies from `Pipfile`.

# How to run
## Simulating meteors
First of all, you need to generate a population of virtual meteoroids. This is done by running

    > ./asmodeus-generate.py <dataset name> <meteor config file>
    
Meteor files are saved in `datasets/<dataset name>/meteors`.

## Calculating sightings
In the next step ASMODEUS computes the sightings.

    > ./asmodeus-observer.py <dataset name> <observer config file>
    
using the same `<dataset name>` as before. Sightings are stored in `datasets/<dataset name>/sightings`

## Analyses
