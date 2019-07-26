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

    > ./asmodeus-generate.py <dataset> <meteor-config-file>
    
Meteor files are saved in `datasets/<dataset>/meteors` along with the metadata, such as meteoroid count,
timestamp and configuration options used to generate the population.

## Calculating sightings
Once atmospheric entry of each meteoroid is simulated, you need to compute the geometry and luminosity
data for ground-based observers. This is done by

    > ./asmodeus-observer.py <dataset> <observers-config-file>
    
using the same `<dataset>` as before. Sightings are stored in `datasets/<dataset>/sightings`
along with the used configuration parameters.

## Analyses
For basic analysis of a dataset use

    > ./asmodeus-histogram.py <dataset> <analysis-config-file>
    
to plot histograms of selected pre-defined properties, or

    > ./asmodeus-scatter.py <dataset> <analysis-config-file>

to plot 2D scatter plots for tuples of properties. You may define properties to be displayed on
the `x` axis, `y` axis, colour and dot size.

Each analysis configuration file may contain a set of observational bias parameters, such as
the sensitivity of cameras to magnitude, altitude or angular speed of meteors.

## Plotting a sky map
Asmodeus includes a simple visualisation tool that plots the meteors as they would be observed in the sky.

    > ./asmodeus-sky.py <dataset> <sky-config-file>

If the observations were calculated with `streaks` option on, the sky map will contain entire meteors,
otherwise only the brightest frame of each meteor is shown. The sky maps are saved to
`datasets/<dataset>/sky/<observer>/sky.png`.

## Comparing two analyses and multiparametric fit
ASMODEUS can be used to fit the meteor distributions to another (observational) dataset with

    > ./asmodeus-multifit <dataset> <other-dataset> <multifit-config-file>

The program outputs the optimal values of parameters. Currently this is not implemented!

# Thanks
I would like to thank Juraj Tóth as the advisor of my master thesis, which required this program to be written,
and to Peter Vereš, who suggested using a simulation as a means of de-biasing the observational data.
