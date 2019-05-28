#!/usr/bin/env python

from core               import asmodeus, logger
from utilities          import colour as c


class AsmodeusSky(asmodeus.AsmodeusAnalyze):
    name = 'sky'

    def prepareDataset(self):
        super().prepareDataset()
        self.protectOverwrite('plots', 'sky')

    def runAnalysis(self, observer):
        observer.plotSky()


if __name__ == "__main__":
    log = logger.setupLog('root')
    AsmodeusSky().run()
