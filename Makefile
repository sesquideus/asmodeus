MAKEFLAGS += --no-builtin-rules

.SECONDEXPANSION:

datasets/%/meteors:
	./asmodeus-generate.py config/$*.yaml

datasets/%/sightings: \
	datasets/$$*/meteors
	./asmodeus-observe.py config/$*.yaml
