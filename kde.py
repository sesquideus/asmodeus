#!/usr/bin/env python

from core               import asmodeus, logger
from utilities          import colour as c


class AsmodeusKDE(asmodeus.AsmodeusAnalyze):
    name = 'kde'

    def prepareDataset(self):
        super().prepareDataset()
        self.protectOverwrite('analyses', 'kde')

    def runAnalysis(self, observer):
        observer.makeKDEs()


if __name__ == "__main__":
    log = logger.setupLog('root')
    AsmodeusKDE().run()
