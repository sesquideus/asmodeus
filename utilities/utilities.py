import argparse
import os
import sys
import jinja2
import itertools
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
        os.mkdir(tryDir, exist_ok = True)

        if not os.path.isdir(tryDir):
            raise argparse.ArgumentTypeError("writeableDir: {0} is not a valid path".format(tryDir))
        if os.access(tryDir, os.W_OK):
            setattr(namespace, self.dest, tryDir)
        else:
            raise argparse.ArgumentTypeError("writeableDir: {0} is not a writeable directory".format(tryDir))


def formatList(items):
    return ", ".join(["{}".format(c.param(item)) for item in items])


def formatParameters(parameters):
    return ", ".join(["{} = {}".format(c.param(name), value) for name, value in parameters.items()])


def jinjaEnvironment(directory):
    return jinja2.Environment(
        trim_blocks = True,
        autoescape = False,
        undefined = jinja2.StrictUndefined,
        loader = jinja2.FileSystemLoader(directory),
    )


def renderTemplate(template, context, outputDirectory = None):
    print(
        jinjaEnvironment('templates').get_template(template).render(context),
        file = sys.stdout if outputDirectory is None else open(os.path.join(outputDirectory, template), 'w')
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
