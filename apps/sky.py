from core import asmodeus, logger

log = logger.setupLog('root')


class AsmodeusSky(asmodeus.AsmodeusAnalyze):
    name = 'sky'

    def prepareDataset(self):
        self.dataset.resetSkyPlots()

    def runSpecific(self):
        super().runSpecific()
        self.campaign.makeSkyPlots(dark = False)
