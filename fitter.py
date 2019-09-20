import argparse
import pandas
import numpy as np
import scipy.stats as ss
from matplotlib import pyplot as plt

parser = argparse.ArgumentParser(description = "All-Sky Meteor Observation and Detection Efficiency Simulator")
parser.add_argument('dataset',                  type = str)
args = parser.parse_args()

data = pandas.read_csv(f'datasets/{args.dataset}/sightings/teplicne/sky.tsv', sep = '\t')

def clamp(values, edges, low, high):
    ok = (edges >= low) & (edges < high)
    return values[ok], edges[ok]


def fitData(values, edges, low, high):
    return clamp(*allData(values, edges), low, high)


def allData(values, edges):
    ok = np.nonzero(values)
    return np.log10(values[ok]), edges[ok]


def analyze(prop, min, max, *, rmin = -np.inf, rmax = np.inf, binc = 48):
    bins, edges = np.histogram(prop, range = (min, max), bins = binc)
    edges = edges[:-1]
    centres = edges + (max - min) / binc / 2

    fitValues, fitCentres = fitData(bins, centres, rmin, rmax)
    allValues, allCentres = allData(bins, centres)

    wa, wb = fit(fitCentres, fitValues, weights = True)
    #ua, ub = fit(fitCentres, fitValues)

    plt.bar(fitCentres, fitValues, align = 'center', width = (max - min) / binc, alpha = 1, color = 'orange')
    plt.bar(allCentres, allValues, align = 'center', width = (max - min) / binc, alpha = 0.3, color = 'orange')

    x = np.linspace(min, max, 1000)
    #plt.plot(x, ua * x + ub, color = 'yellow')
    plt.plot(x, wa * x + wb, color = 'green')
    
    return wa, wb

def analyzeInitMass():
    slope, shift = analyze(np.log10(data.initMass), -7, 0, rmin = -5.3, rmax = 0, binc = 70)
    return 1 - slope

def analyzeAbsMag():
    slope, shift = analyze(data.absMag, -12, 12, rmin = -8, rmax = 0, binc = 96)
    return np.power(10, slope)

def analyzeAppMag():
    slope, shift = analyze(data.appMag, -12, 12, rmin = -8, rmax = 0, binc = 96)
    return np.power(10, slope)

def fit(edges, values, *, weights = None):
    coefs, r, _, _, _ = np.polyfit(edges, values, 1, full = True, w = np.power(10, values / 2) if weights else None)
    expected = coefs[0] * edges + coefs[1]
    chisq, p = ss.chisquare(values, expected, 50)
    
    return coefs[0], coefs[1]

#s = analyzeInitMass()
#rv = analyzeAppMag()
ra = analyzeAbsMag()

#print(f"s = {s:1.6f}")
print(f"ra = {ra:1.6f}")
#print(f"rv = {rv:1.6f}")
#print(f"1 + 2.5 log r_v = {1 + 2.5 * np.log10(rv)}")
print(f"1 + 2.5 log r_a = {1 + 2.5 * np.log10(ra)}")

plt.show()
    
