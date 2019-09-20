import math
import sys
import logging
import datetime
import numpy as np
import matplotlib.pyplot as pp

log = logging.getLogger('root')


class Histogram:
    def __init__(self, lower, upper, *, name = '<unnamed>'):
        self.name       = name
        self.lower      = lower
        self.upper      = upper
        self.totalCount = 0
        self.bins       = [0 for x in np.arange(self.lower, self.upper, self.binWidth)]
        self.binCount   = len(self.bins)

    def bin(self, value):
        b = int(math.floor(self.binCount * (value - self.lower) / (self.upper - self.lower)))
        if b < 0 or b >= self.binCount:
            raise KeyError("Value {value} outside permissible range ({lower} - {upper})".format(
                value   = value,
                lower   = self.lower,
                upper   = self.upper,
            ))
        else:
            return b

    def key(self, bin):
        return (self.lower + bin * self.binWidth)

    @classmethod
    def formatKey(cls, key):
        raise NotImplementedError("No formatter defined")

    @classmethod
    def formatValue(cls, value):
        return "{:16.6f}".format(value)

    def add(self, value):
        self.bins[self.bin(value)] += 1
        self.totalCount += 1

    def normalize(self):
        if self.totalCount > 0:
            for bin in self.bins:
                bin /= self.totalCount
            self.totalCount = 1

        return self

    def print(self, file = sys.stdout):
        print("# Histogram \"{}\" ({} to {}, bin width {})".format(self.name, self.lower, self.upper, self.binWidth), file = file)
        for bin, count in enumerate(self.bins):
            print("{key}\t{value}".format(
                key         = self.formatKey(self.key(bin)),
                value       = self.formatValue(count),
            ), file = file)

    def render(self, file):
        figure = pp.figure(figsize = (6, 4), dpi = 300)
        figure.suptitle(self.name, fontname = 'Cabin')

        axes = figure.add_subplot(1, 1, 1)

        #axes.set_ylim(bottom = 0, top = None)
        axes.bar(np.arange(self.lower, self.upper, self.binWidth), self.bins, self.binWidth, align = 'edge')
        pp.grid(True, 'both', linestyle = ':', linewidth = 0.25)
        pp.savefig(file, bbox_inches = 'tight') 

    @staticmethod
    def processTSV(file, name, min, max, step, column):
        result = Histogram(name, min, max, step)

        for line in open(file, 'r'):
            if line[0] == '#':
                continue

            values = line.rstrip('\n').split()
            result.add(float(values[column]))

        return result

    def __matmul__(self, other):
        return self.chiSquare(other)

    def chiSquare(self, other):
        if self.lower != other.lower or self.upper != other.upper or self.binWidth != other.binWidth:
            raise TypeError("Incompatible histograms")

        if self.totalCount == 0 or other.totalCount == 0:
            return 2

        chi2 = 0

        self.normalize()
        other.normalize()

        for bin, count in enumerate(self.bins):
            denom = count + other.bins[bin]
            if denom > 0:
                chi2 += (count - other.bins[bin])**2 / denom

        return chi2

    @staticmethod
    def merge(first, second):
        if first.binWidth != second.binWidth or type(first) is not type(second):
            raise TypeError("Incompatible histograms")


class TimeHistogram(Histogram):
    def __init__(self, lower, upper, binWidth = datetime.timedelta(seconds = 1), *, name = '<unnamed>'):
        self.binWidth   = datetime.timedelta(seconds = binWidth)
        super().__init__(lower, upper, name = name)

    def __str__(self, file = sys.stdout):
        print("# Histogram \"{}\" ({} to {}, bin width {})".format(self.name, self.lower, self.upper, self.binWidth), file = file)
        for bin, count in enumerate(self.bins):
            print("{key}\t{value:16.6f}".format(
                key         = self.key(bin).isoformat(),
                value       = count,
            ), file = file)

    @classmethod
    def formatKey(cls, key):
        return key.isoformat()


class FloatHistogram(Histogram):
    def __init__(self, lower, upper, binWidth = 1, *, name = '<unnamed>'):
        self.binWidth   = binWidth
        super().__init__(lower, upper, name = name)

    @classmethod
    def formatKey(cls, key):
        return "{key:12.6f}".format(key = key)
