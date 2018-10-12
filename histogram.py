import math, numbers, sys, logging
import numpy as np

log = logging.getLogger('root')

class Histogram: 
    def __init__(self, name, lower, upper, binWidth = 1):
        self.name       = name
        self.lower      = lower
        self.upper      = upper
        self.binWidth   = binWidth
        self.keys       = [x for x in np.arange(lower, upper, binWidth)]
        self.counts     = [0 for x in np.arange(lower, upper, binWidth)]
        self.binCount   = (self.upper - self.lower) / self.binWidth
        self.count      = 0

    def key(self, value):
        key = int(math.floor(self.binCount * (value - self.lower) / (self.upper - self.lower)))

        if key < 0 or key >= len(self.keys):
            raise KeyError()

        return key

    def __getitem__(self, key):
        return self.counts[self.key(key)]

    def __setitem__(self, key, value):
        try:
            self.counts[self.key(key)] = value
        except KeyError:
            pass

    def add(self, value):
        try:
            self[value] += 1
            self.count += 1
        except KeyError:
            log.warning("Could not get item {}".format(value))

    def normalize(self):
        if self.count > 0:
            for key in self.keys:
                self[key] /= self.count        
            self.count = 1

        return self

    def tsv(self, file = sys.stdout, **kwargs):        
        normalize = kwargs.get('normalize', False)

        print("# histogram {} ({} to {}, bin width {})".format(self.name, self.lower, self.upper, self.binWidth), file = file)
        for key in self.keys:
            print("{key:12.6f}\t{value:10.6f}".format(
                key         = key,
                value       = self.counts[self.key(key)],
            ), file = file)

    @staticmethod
    def load(file, name, min, max, step, column):
        result = Histogram(name, min, max, step)

        for line in open(file, 'r'):
            if line[0] == '#':
                continue

            values = line.rstrip('\n').split()
            result.add(float(values[column]))

        return result

    def __matmul__(self, other):
        if self.lower != other.lower or self.upper != other.upper or self.binWidth != other.binWidth:
            raise Exception("Incompatible histograms")

        if self.count == 0 or other.count == 0:
            return 2
    
        sum = 0

        self.normalize()
        other.normalize()

        for key in self.keys:  
            denom = self[key] + other[key]
            if denom > 0:
                sum += (self[key] - other[key])**2 / denom

        return sum

