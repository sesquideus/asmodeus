import logging
from colorama import Fore, Style

def setupLog(name, **kwargs):
    colour = {
        'DEBUG': Fore.GREEN,
        'INFO': Fore.GREEN,
        'WARNING': Fore.YELLOW,
        'ERROR': Fore.RED
    }
    formatter = logging.Formatter('{}%(asctime)s.%(msecs)03d [%(levelname)s]{}: %(message)s'.format(colour['DEBUG'], Style.RESET_ALL), "%H:%M:%S")

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
