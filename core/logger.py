import logging
import time
from utilities import colour as c


class AsmodeusFormatter(logging.Formatter):
    def __init__(self):
        super().__init__('{asctime} [{levelname}] {message}', "%H:%M:%S", '{')

    def format(self, record):
        record.levelname = {
            'DEBUG':    c.debug,
            'INFO':     c.none,
            'WARNING':  c.warn,
            'ERROR':    c.err,
            'CRITICAL': c.critical,
        }[record.levelname](record.levelname[:3])

        return super().format(record)

    def formatTime(self, record, format):
        ct = self.converter(record.created)
        return f"{time.strftime('%H:%M:%S', ct)}.{int(record.msecs):03d}"


def setupLog(name, **kwargs):
    formatter = AsmodeusFormatter()

    output = kwargs.get('output', None)
    if type(output) == str:
        handler = logging.FileHandler(output)
    else:
        handler = logging.StreamHandler()
    handler.setFormatter(formatter)

    log = logging.getLogger(name)
    log.setLevel(logging.DEBUG)
    log.addHandler(handler)

    return log
