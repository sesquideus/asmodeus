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

    > ./asmodeus-generate.py <dataset> <meteor config file>
    
Meteor files are saved in `datasets/<dataset name>/meteors`.

## Calculating sightings
In the next step ASMODEUS computes the sightings.

    > ./asmodeus-observer.py <dataset> <observer config file>
    
using the same `<dataset>` as before. Sightings are stored in `datasets/<dataset>/sightings`.

## Analyses
For basic analysis of a dataset use

    > ./asmodeus-histogram.py <dataset> <analysis config file>
    
to plot histograms of all pre-defined properties, or

    > ./asmodeus-scatter.py <dataset> <analysis config file>

to plot 2D scatter plots of pairs of properties.

## Plotting a sky map
Asmodeus includes a simple visualisation tool that plots the meteors as they would be observed in the sky.

    > ./asmodeus-sky.py <dataset> <sky config file>

If the observations were calculated with `streaks` option on, the sky map will contain entire meteors,
otherwise only the brightest frame of each meteor is shown.
