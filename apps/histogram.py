from core import asmodeus, logger

log = logger.setupLog('root')


class AsmodeusHistogram(asmodeus.AsmodeusAnalyze):
    name = 'histogram'

    def prepare_dataset(self):
        super().prepare_dataset()
        self.protect_overwrite('analyses', 'histograms')

    def run_analysis(self, observer):
        observer.make_histograms()
