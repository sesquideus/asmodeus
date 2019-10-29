from core import asmodeus, logger

log = logger.setupLog('root')


class AsmodeusKDE(asmodeus.AsmodeusAnalyze):
    name = 'kde'

    def prepare_dataset(self):
        super().prepare_dataset()
        self.protect_overwrite('analyses', 'kde')

    def run_analysis(self, observer):
        observer.make_KDEs()
