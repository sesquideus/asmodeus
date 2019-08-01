import dotmap
import yaml
import logging

from core import exceptions
from utilities import colour as c

log = logging.getLogger('root')


def loadYAML(fileObject):
    try:
        log.debug(f"Loading YAML file {c.path(fileObject.name)}")
        config = yaml.safe_load(fileObject)
    except yaml.composer.ComposerError as e:
        log.error(f"YAML composer error")
        raise exceptions.ConfigurationError(e) from e

    return dotmap.DotMap(config, _dynamic = False)

