from core import asmodeus, logger

log = logger.setupLog('root')


class AsmodeusHistogram(asmodeus.AsmodeusAnalyze):
    name = 'histogram'

    def prepare_dataset(self):
        self.dataset.reset_histograms()

    def run_specific(self):
        super().run_specific()
        self.campaign.make_histograms()
