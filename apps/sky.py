from core import asmodeus, logger

log = logger.setupLog('root')


class AsmodeusSky(asmodeus.AsmodeusAnalyze):
    name = 'sky'

    def prepareDataset(self):
        super().prepareDataset()
        self.protectOverwrite('plots')

    def runAnalysis(self, observer):
        observer.plotSky()
