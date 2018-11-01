import logging


def setupLog(name, **kwargs):
    formatter = logging.Formatter('%(asctime)s.%(msecs)03d [%(levelname)s]: %(message)s', "%H:%M:%S")

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
