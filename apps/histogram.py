from core import asmodeus


class AsmodeusHistogram(asmodeus.AsmodeusAnalyze):
    name = 'histogram'

    def prepareDataset(self):
        super().prepareDataset()
        self.protectOverwrite('analyses', 'histograms')

    def runAnalysis(self, observer):
        observer.makeHistograms()
