MAKEFLAGS += --no-builtin-rules

.SECONDEXPANSION:

datasets/%/meteors:
	./asmodeus-generate.py config/$*.yaml

datasets/%/sightings: \
	datasets/$$*/meteors
	./asmodeus-observe.py config/$*.yaml

datasets/%/histograms: \
	datasets/$$*/sightings
	./asmodeus-analyze.py config/$*.yaml

datasets/%/sky: \
	datasets/$$*/sightings
	./asmodeus-analyze.py config/$*.yaml

datasets/%/plot-histograms: \
	datasets/$$*/histograms
	./asmodeus-plot.py config/$*.yaml

datasets/%/plot-sky: \
	datasets/$$*/sightings \
	datasets/$$*/sky
	./asmodeus-plot.py config/$*.yaml
