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
        log.error(f"YAML composer error")
        raise exceptions.ConfigurationError(e) from e

    return dotmap.DotMap(config)

