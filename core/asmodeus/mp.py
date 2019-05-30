from .asmodeus import Asmodeus


class AsmodeusMultiprocessing(Asmodeus):
    def createArgparser(self):
        super().createArgparser()
        self.argparser.add_argument('-p', '--processes', type = int)

    def overrideConfig(self):
        super().overrideConfig()

        if self.args.processes:
            self.overrideWarning('process count', self.config.mp.processes, self.args.processes)
            self.config.mp.processes = self.args.processes
