import logging
import time
import multiprocessing as mp

from utilities          import colour as c

log = logging.getLogger('root')


def parallel(function, args, *, initializer = None, initargs = (), processes = 1, action = "<default action>", period = 1):
    manager = mp.Manager()
    queue = manager.Queue()
    pool = mp.Pool(processes = processes, initializer = initializer, initargs = (queue, *initargs))
    total = len(args)
    chunksize = (total // processes)

    results = pool.map_async(function, args, chunksize)

    while not results.ready():
        size = queue.qsize()
        log.info("{action}: {count} of {total} ({perc})".format(
            action      = action,
            count       = c.num(f"{size:6d}"),
            total       = c.num(f"{total:6d}"),
            perc        = c.num(f"{size / total * 100:6.2f}%"),
        ))
        time.sleep(period)

    return results.get()
