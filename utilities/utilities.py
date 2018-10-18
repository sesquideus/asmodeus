import argparse, os, jinja2, itertools
import namedtupled as nt
import numpy as np

from utilities import colour as c

class readableDir(argparse.Action):
    def __call__(self, parser, namespace, values, option_string = None):
        tryDir = values
        if not os.path.isdir(tryDir):
            raise argparse.ArgumentTypeError("readableDir: {0} is not a valid path".format(tryDir))
        if os.access(tryDir, os.R_OK):
            setattr(namespace, self.dest, tryDir)
        else:
            raise argparse.ArgumentTypeError("readableDir: {0} is not a readable directory".format(tryDir))

class writeableDir(argparse.Action):
    def __call__(self, parser, namespace, values, option_string = None):
        tryDir = values
        try:
            os.mkdir(tryDir)
        except FileExistsError as e:
            pass

        if not os.path.isdir(tryDir):
            raise argparse.ArgumentTypeError("writeableDir: {0} is not a valid path".format(tryDir))
        if os.access(tryDir, os.W_OK):
            setattr(namespace, self.dest, tryDir)
        else:
            raise argparse.ArgumentTypeError("writeableDir: {0} is not a writeable directory".format(tryDir))

def formatParameters(parameters):
    formatted = ["{} = {}".format(c.param(name), value) for name, value in parameters.items()]
    return ", ".join(formatted)

def jinjaEnv(directory):
    return jinja2.Environment(
        trim_blocks = True,
        autoescape = False,
        loader = jinja2.FileSystemLoader(directory),
    )

def linSpace(min, max, step):
    return np.linspace(min, max, int(round((max - min) / step)) + 1)

def filterVisible(sightings):
    return list(filter(lambda s: s.sighted, sightings))

def generateParameterSpace(**parameters):
    spaces = itertools.product(*[[{name: value} for value in linSpace(param.min, param.max, param.step)] for name, param in parameters.items()])
    
    output = []
    for space in spaces:
        r = {}
        for value in space:
            r.update(value)
        output.append(r)

    return output
