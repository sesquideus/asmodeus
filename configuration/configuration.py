import yaml, namedtupled, dotmap, logging, os
from colorama import Fore, Style

from utils import colour

log = logging.getLogger('root')

def load(configFile):
    try:
        config = yaml.load(configFile)
    except FileNotFoundError as e:
        log.error("Could not load configuration file {}: {}".format(configFile, e))
    return dotmap.DotMap(config)

def applyOverridesObserve(args, config):
    if (args.plot_sky):
        log.warning("Overriding plot-sky ({} to {})".format(colour(config.plot.sky, 'over'), colour(args.plot_sky, 'over')))
        config.plot.sky = args.plot_sky

    return config
