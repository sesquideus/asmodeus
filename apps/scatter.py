from core import asmodeus, logger

log = logger.setupLog('root')


class AsmodeusScatter(asmodeus.AsmodeusAnalyze):
    name = 'scatter'

    def prepareDataset(self):
        self.dataset.resetScatters()

    def runAnalysis(self, observer):
        observer.makeScatters()
