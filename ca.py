import pandas as pd
import numpy as np

df = pd.read_csv('amos.tsv', sep = '\t')

df['elevation'] = 100000
df['initMass'] = 0.001
df['fluxDensity'] = np.power(10, (-20.9 - df.appMag) / 2.5)
df['absMag'] = 0

print(df)

df.to_csv('datasets/amos/sightings/teplicne/sky.tsv', sep = '\t')
