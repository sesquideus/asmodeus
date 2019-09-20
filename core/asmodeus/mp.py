from .asmodeus import Asmodeus


class AsmodeusMultiprocessing(Asmodeus):
    def createArgparser(self):
        super().createArgparser()
        self.argparser.add_argument('-p', '--processes', type = int)
        self.argparser.add_argument('-t', '--period',           type = float)

    def overrideConfig(self):
        super().overrideConfig()

        self.config.mp.processes = 1
        if self.args.processes:
            self.overrideWarning('process count', self.config.mp.processes, self.args.processes)
            self.config.mp.processes = self.args.processes

        self.config.mp.report = 1.0
        if self.args.period:
            self.overrideWarning('reporting period', self.config.mp.report, self.args.period)
            self.config.mp.report = self.args.period

