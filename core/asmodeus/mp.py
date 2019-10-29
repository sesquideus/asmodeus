from .asmodeus import Asmodeus


class AsmodeusMultiprocessing(Asmodeus):
    def create_argparser(self):
        super().create_argparser()
        self.argparser.add_argument('-p', '--processes', type=int, help="run with N processes")
        self.argparser.add_argument('-t', '--period', type=float, help="override report period when running on multiple cores [seconds]")

    def override_config(self):
        super().override_config()

        self.config.mp.processes = 1
        if self.args.processes:
            self.override_warning('process count', self.config.mp.processes, self.args.processes)
            self.config.mp.processes = self.args.processes

        self.config.mp.report = 1.0
        if self.args.period:
            self.override_warning('reporting period', self.config.mp.report, self.args.period)
            self.config.mp.report = self.args.period

