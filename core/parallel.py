import logging
import time
import multiprocessing as mp

from utilities          import colour as c

log = logging.getLogger('root')


def parallel(function, args, *, processes = 1, action = "<default action>", period = 1):
    pool = mp.Pool(processes = processes)
    manager = mp.Manager()
    queue = manager.Queue()
    total = len(args)

    results = pool.map_async(function, [(queue, *x) for x in args], 50)

    while not results.ready():
        log.info("{action}: {count} of {total} ({perc})".format(
            action      = action,
            count       = c.num(f"{queue.qsize():6d}"),
            total       = c.num(f"{total:6d}"),
            perc        = c.num(f"{queue.qsize() / total * 100:6.2f}%"),
        ))
        time.sleep(period)

    return results.get()
