import dotmap
import yaml
import logging

from core import exceptions
from utilities import colour as c

log = logging.getLogger('root')


def loadYAML(fileObject):
    try:
        config = yaml.safe_load(fileObject)
    except yaml.composer.ComposerError as e:
        log.error(f"YAML composer error {e}")
        raise exceptions.ConfigurationError(e) from e
    except yaml.scanner.ScannerError as e:
        log.error(f"YAML scanner error {e}")
        raise exceptions.ConfigurationError(e) from e

    return dotmap.DotMap(config)


def makeStatic(config):
    for k in config._map:
        if isinstance(config[k], dotmap.DotMap):
            makeStatic(config[k])
        if isinstance(config[k], list):
            for item in config[k]:
                makeStatic(item)
        config._dynamic = False
