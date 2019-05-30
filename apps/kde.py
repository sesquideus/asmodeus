from core import asmodeus

log = logger.setupLog('root')


class AsmodeusKDE(asmodeus.AsmodeusAnalyze):
    name = 'kde'

    def prepareDataset(self):
        super().prepareDataset()
        self.protectOverwrite('analyses', 'kde')

    def runAnalysis(self, observer):
        observer.makeKDEs()
