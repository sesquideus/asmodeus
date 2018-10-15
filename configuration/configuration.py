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

def applyOverrides(script, args):
    config = applyGenericOverrides(args)
    config = eval("applyOverrides{}".format(script.capitalize()))(args, config)
    return namedtupled.map(config.toDict())

def applyGenericOverrides(args):
    config = load(args.config)
    log.setLevel(logging.DEBUG if args.debug else logging.INFO)

    if args.debug:
        log.warning("Debug output {}".format(colour("active", 'over')))

    if args.logfile:
        log.addHandler(logging.FileHandler(args.logfile.name))
        log.warning("Added log output {}".format(colour(args.logfile.name, 'over')))

    if args.processes:
        log.warning("Overriding process count ({} to {})".format(colour(config.mp.processes, 'over'), colour(args.processes, 'over')))
        config.mp.processes = args.processes

    if args.dataset:
        log.warning("Overriding dataset ({} to {})".format(colour(config.dataset.name, 'over'), colour(args.dataset, 'over')))
        config.dataset.name = args.dataset
    
    config.dataset.path = os.path.join('datasets', config.dataset.name)
   
    return config

def applyOverridesGenerate(args, config):
    
    return config

def applyOverridesObserve(args, config):
    if (args.plot_sky):
        log.warning("Overriding plot-sky ({} to {})".format(colour(config.plot.sky, 'over'), colour(args.plot_sky, 'over')))
        config.plot.sky = args.plot_sky

    return config

def applyOverridesPlot(args, config):
    return config

def applyOverridesAnalyze(args, config):
    return config
