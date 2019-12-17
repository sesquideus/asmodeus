all: wgs84.c wgs84.h wgs84.i
	swig -python wgs84.i
	python setup.py build_ext --inplace
