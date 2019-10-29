from core import asmodeus, logger

log = logger.setupLog('root')


class AsmodeusSky(asmodeus.AsmodeusAnalyze):
    name = 'sky'

    def prepare_dataset(self):
        self.dataset.reset_sky_plots()

    def run_specific(self):
        super().run_specific()
        self.campaign.make_sky_plots(dark=False)
