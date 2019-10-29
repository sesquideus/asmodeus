from core import asmodeus, logger

log = logger.setupLog('root')


class AsmodeusScatter(asmodeus.AsmodeusAnalyze):
    name = 'scatter'

    def prepare_dataset(self):
        self.dataset.reset_scatters()

    def run_specific(self):
        super().run_specific()
        self.campaign.make_scatters()
