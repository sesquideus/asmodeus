import pandas
import numpy as np
import scipy.stats as ss
from matplotlib import pyplot as plt

data = pandas.read_csv('datasets/perseids/sightings/teplicne/sky.tsv', sep = '\t')

def analyze(prop, min, max, binc = 48):
    bins, edges = np.histogram(prop, range = (min, max), bins = binc)
    print(bins, edges)
    ok = np.nonzero(bins)
    bins = bins[ok]
    bins = np.log10(bins)

    edges = edges[:-1]
    edges = edges[ok]

    edges = edges[:24]
    bins = bins[:24]

    wcoefs = fit(edges, bins, weights = bins)
    coefs = fit(edges, bins)


    plt.bar(edges, bins, align = 'edge', width = (max - min) / binc, color = 'orange')

    x = np.linspace(min, max, 1000)

    plt.plot(x, coefs[0] * x + coefs[1])
    plt.plot(x, wcoefs[0] * x + wcoefs[1], color = 'green')
    plt.show()

def fit(edges, values, *, weights = None):
    coefs, r, _, _, _ = np.polyfit(edges, values, 1, full = True)
    print(f"Coefficients are {coefs}", r)

    expected = coefs[0] * edges + coefs[1]

    chisq, p = ss.chisquare(values, expected, 50)
    print(f"chisq = {chisq}, p = {p}")
    
    return coefs

#fit(data.appMag, -12, 12)
#fit(data.absMag, -12, 12)

analyze(np.log10(data.initMass), -5.3, 0, 53)
