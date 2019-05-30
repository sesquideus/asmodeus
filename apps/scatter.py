from core import asmodeus, logger

log = logger.setupLog('root')


class AsmodeusScatter(asmodeus.AsmodeusAnalyze):
    name = 'scatter'

    def prepareDataset(self):
        super().prepareDataset()
        self.protectOverwrite('analyses', 'scatters')

    def runAnalysis(self, observer):
        observer.makeScatters()
