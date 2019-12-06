#!/usr/bin/env python

"""
setup.py file for SWIG example
"""

from distutils.core import setup, Extension

wgs84_module = Extension('_wgs84',
    sources=['wgs84_wrap.c', 'wgs84.c'],
)

setup(name='wgs84',
    version='0.1',
    author="Kvík",
    description="""WGS84 utilities for ASMODEUS""",
    ext_modules=[wgs84_module],
    py_modules=["wgs84"],
)
