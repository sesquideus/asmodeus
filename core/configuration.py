import yaml
import dotmap
import logging

from core import exceptions
from utilities import colour as c

log = logging.getLogger('root')


def load(configFile):
    try:
        config = yaml.safe_load(configFile)
    except FileNotFoundError as e:
        log.error("Could not load configuration file {}: {}".format(configFile, e))
        raise exceptions.CommandLineError()

    return dotmap.DotMap(config, _dynamic = False)


def applyOverridesObserve(args, config):
    if (args.plot_sky):
        log.warning("Overriding plot-sky ({} to {})".format(c.over(config.plot.sky), c.over(args.plot_sky)))
        config.plot.sky = args.plot_sky

    return config
