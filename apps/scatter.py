from core import asmodeus


class AsmodeusScatter(asmodeus.AsmodeusAnalyze):
    name = 'scatter'

    def prepareDataset(self):
        super().prepareDataset()
        self.protectOverwrite('analyses', 'scatters')

    def runAnalysis(self, observer):
        observer.makeScatters()
