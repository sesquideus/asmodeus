./asmodeus-generate.py $1 config/meteors/$1.yaml -t 0.5
./asmodeus-observe.py $1 config/observers/tepličné.yaml -t 0.5
./asmodeus-sky.py $1 config/analyses/base.yaml -b
./asmodeus-scatter.py $1 config/analyses/base.yaml -b
