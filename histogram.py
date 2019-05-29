#!/usr/bin/env python

from core               import asmodeus, logger
from utilities          import colour as c


class AsmodeusHistograms(asmodeus.AsmodeusAnalyze):
    name = 'histogram'

    def prepareDataset(self):
        super().prepareDataset()
        self.protectOverwrite('analyses', 'histograms')

    def runAnalysis(self, observer):
        observer.makeHistograms()


if __name__ == "__main__":
    log = logger.setupLog('root')
    AsmodeusHistograms().run()
