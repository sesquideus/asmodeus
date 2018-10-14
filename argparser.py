import argparse

class AsmodeusParser(argparse.ArgumentParser):
    def __init__(self):
        super().__init__(description = "All-Sky Meteor Orbit and Detection Efficiency Simulator")
        self.add_argument('config',               type = argparse.FileType('r'))
        self.add_argument('-d', '--debug',        action = 'store_true')
        self.add_argument('-p', '--processes',    type = int)
        self.add_argument('-s', '--dataset',      type = str)
        self.add_argument('-l', '--logfile',      type = argparse.FileType('w'))

class AsmodeusParserGenerate(AsmodeusParser):
    def __init__(self):
        super().__init__()    
        self.add_argument('-c', '--count', type = int)

class AsmodeusParserObserve(AsmodeusParser):
    def __init__(self):
        super().__init__()
        self.add_argument('--plot-sky', action = 'store_true')


