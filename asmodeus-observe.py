#!/usr/bin/env python
"""
    Asmodeus, script 2: observe

    Computes apparent positions and magnitudes for all observers as defined in the configuration file,
    using generated meteors saved in specified dataset's `meteors` subdirectory
    Requires: meteors
    Outputs: sightings
"""

from apps.observe import AsmodeusObserve

if __name__ == "__main__":
    AsmodeusObserve().run()
