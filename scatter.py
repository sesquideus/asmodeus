#!/usr/bin/env python

from core               import asmodeus, logger
from utilities          import colour as c


class AsmodeusScatter(asmodeus.AsmodeusAnalyze):
    name = 'scatter'

    def prepareDataset(self):
        super().prepareDataset()
        self.protectOverwrite('analyses', 'scatters')

    def runAnalysis(self, observer):
        observer.makeScatters()


if __name__ == "__main__":
    log = logger.setupLog('root')
    AsmodeusScatter().run()
