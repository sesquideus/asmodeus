#!/usr/bin/env python
"""
    Asmodeus, script 1: generate

    Generates a set of meteoroids and simulates their atmospheric entry.
    Requires: nothing
    Outputs: meteors
"""

from apps.generate import AsmodeusGenerate

if __name__ == "__main__":
    AsmodeusGenerate().run()
