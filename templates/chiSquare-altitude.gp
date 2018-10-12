set terminal pdf size 18cm, 10cm font "Minion Pro, 20"
set title "χ^2 comparison of altitude distributions"
set xlabel "Exponent (parameter α)"
set grid
set key off

set style fill transparent solid 0.6 noborder

set output "datasets/{{ dataset }}/plots/chiSquare-altitude.pdf"
set xrange [{{ exponent.min - 2 * exponent.step }}:{{ exponent.max + 2 * exponent.step }}]
set yrange [0:]

plot 'datasets/{{ dataset }}/plots/chiSquare-altitude.tsv' using 1:2 title "Comparison" with boxes linecolor rgb '#00C000'
