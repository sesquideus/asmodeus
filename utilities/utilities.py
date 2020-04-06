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
        try_dir = values
        if not os.path.isdir(try_dir):
            raise argparse.ArgumentTypeError(f"readable_dir: {try_dir} is not a valid path")
        if os.access(try_dir, os.R_OK):
            setattr(namespace, self.dest, try_dir)
        else:
            raise argparse.ArgumentTypeError(f"readable_dir: {try_dir} is not a readable directory")


class writeable_dir(argparse.Action):
    def __call__(self, parser, namespace, values, option_string = None):
        try_dir = values
        os.mkdir(try_dir, exist_ok = True)

        if not os.path.isdir(try_dir):
            raise argparse.ArgumentTypeError(f"writeable_dir: {try_dir} is not a valid path")
        if os.access(try_dir, os.W_OK):
            setattr(namespace, self.dest, try_dir)
        else:
            raise argparse.ArgumentTypeError(f"writeable_dir: {try_dir} is not a writeable directory")


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
