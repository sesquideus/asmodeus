import yaml
import dotmap
import logging

from utilities import colour as c

log = logging.getLogger('root')


def load(configFile):
    try:
        config = yaml.load(configFile)
    except FileNotFoundError as e:
        log.error("Could not load configuration file {}: {}".format(configFile, e))
    return dotmap.DotMap(config)


def applyOverridesObserve(args, config):
    if (args.plot_sky):
        log.warning("Overriding plot-sky ({} to {})".format(c.over(config.plot.sky), c.over(args.plot_sky)))
        config.plot.sky = args.plot_sky

    return config
