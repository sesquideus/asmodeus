import argparse
import os
import sys
import jinja2
import itertools
import numpy as np
import dotmap

from utilities import colour as c


class readable_dir(argparse.Action):
    def __call__(self, parser, namespace, values, option_string = None):
        tryDir = values
        if not os.path.isdir(tryDir):
            raise argparse.ArgumentTypeError("readableDir: {0} is not a valid path".format(tryDir))
        if os.access(tryDir, os.R_OK):
            setattr(namespace, self.dest, tryDir)
        else:
            raise argparse.ArgumentTypeError("readableDir: {0} is not a readable directory".format(tryDir))


class writeable_dir(argparse.Action):
    def __call__(self, parser, namespace, values, option_string = None):
        tryDir = values
        os.mkdir(tryDir, exist_ok = True)

        if not os.path.isdir(tryDir):
            raise argparse.ArgumentTypeError("writeableDir: {0} is not a valid path".format(tryDir))
        if os.access(tryDir, os.W_OK):
            setattr(namespace, self.dest, tryDir)
        else:
            raise argparse.ArgumentTypeError("writeableDir: {0} is not a writeable directory".format(tryDir))


def format_list(items):
    return ", ".join(["{}".format(c.param(item)) for item in items])


def format_parameters(parameters):
    return ", ".join(["{} = {}".format(c.param(name), value) for name, value in parameters.items()])


def jinja_environment(directory):
    return jinja2.Environment(
        trim_blocks = True,
        autoescape = False,
        undefined = jinja2.StrictUndefined,
        loader = jinja2.FileSystemLoader(directory),
    )


def render_template(template, context, output_directory = None):
    print(
        jinjaEnvironment('templates').get_template(template).render(context),
        file = sys.stdout if output_directory is None else open(os.path.join(output_directory, template), 'w')
    )


def lin_space(min, max, step):
    return np.linspace(min, max, int(round((max - min) / step)) + 1)


def filter_visible(sightings):
    return list(filter(lambda s: s.sighted, sightings))


def generate_parameter_space(**parameters):
    spaces = itertools.product(*[[{name: value} for value in lin_space(param.min, param.max, param.step)] for name, param in parameters.items()])

    output = []
    for space in spaces:
        r = {}
        for value in space:
            r.update(value)
        output.append(r)

    return output


def dict_product(**kwargs):
    keys = kwargs.keys()
    
    for instance in itertools.product(*kwargs.values()):
        yield dict(zip(keys, instance))
