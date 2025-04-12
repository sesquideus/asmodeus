MAKEFLAGS += --no-builtin-rules

.SECONDARY:
.SECONDEXPANSION:

datasets/%/meteors: datasets/%/meteors.yaml;

datasets/%/meteors.yaml:
	./asmodeus-generate.py config/$*.yaml

datasets/%/sightings: datasets/%/sightings.yaml;

datasets/%/sightings.yaml: \
	datasets/%/meteors.yaml
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

physics/wgs84.py: physics/wgs84.i
	cd physics
	swig -python $<

.PHONY:

physics/wgs84: physics/wgs84.py
	cd physics && python setup.py build_ext --inplace
