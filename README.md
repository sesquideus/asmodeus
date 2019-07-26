# What is it?
ASMODEUS is an universal all-sky meteor simulator. 

Its original purpose was to determine and correct observation bias introduced by imperfections
of all-sky camera systems and to use the corrected data to estimate the total meteoroid flux.

# Installation
ASMODEUS requires GNU/Linux operating system and a Python interpreter `>3.7`.
We recommend using `pipenv` to manage a virtual environment. After cloning the repository
and installing `pipenv`, run

    > pipenv sync
  
to collect and install correct versions of dependencies from `Pipfile`.

# How to run
## Simulating meteors
First of all, you need to generate a population of virtual meteoroids. This is done by running

    > ./asmodeus-generate.py <dataset> <meteor config file>
    
Meteor files are saved in `datasets/<dataset name>/meteors` along with the metadata, such as meteoroid count,
timestamp and configuration options used to generate the population.

## Calculating sightings
Once atmospheric entry of each meteoroid is simulated, you need to compute the geometry and luminosity
data for ground-based observers. This is done by

    > ./asmodeus-observer.py <dataset> <observers config file>
    
using the same `<dataset>` as before. Sightings are stored in `datasets/<dataset>/sightings`
along with the used configuration parameters.

## Analyses
For basic analysis of a dataset use

    > ./asmodeus-histogram.py <dataset> <analysis config file>
    
to plot histograms of all pre-defined properties, or

    > ./asmodeus-scatter.py <dataset> <analysis config file>

to plot 2D scatter plots for tuples of properties. You may define properties to be displayed on
the `x` axis, `y` axis, colour and dot size.

## Plotting a sky map
Asmodeus includes a simple visualisation tool that plots the meteors as they would be observed in the sky.

    > ./asmodeus-sky.py <dataset> <sky config file>

If the observations were calculated with `streaks` option on, the sky map will contain entire meteors,
otherwise only the brightest frame of each meteor is shown.

# Thanks
Thanks belong to Juraj Tóth as the advisor of my master thesis, which required this program to be written,
and to Peter Vereš who suggested using a simulation to de-bias the observational data.
