#!/bin/bash
./asmodeus-generate.py $1.yaml -p 4 && ./asmodeus-observe.py $1.yaml && ./asmodeus-multifit.py $1.yaml && ./asmodeus-analyze.py $1.yaml && ./asmodeus-plot.py $1.yaml
