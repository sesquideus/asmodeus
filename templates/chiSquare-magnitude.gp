set terminal pdf size 18cm, 10cm font "Minion Pro, 20"
set title "χ^2 comparison of magnitude distributions"
set xlabel "Limiting magnitude (m_0)"
set ylabel "Falloff rate (ω)"
set grid
set key off

sizeratio = {{ (omega.max / (limmag.max - limmag.min)) / ((omega.step) / (limmag.step)) }}
pointssize = {{ limmag.step * 30 }}
set size ratio sizeratio

set style fill transparent solid 1 border -1

set palette defined (0 "#000000", 0.25 "#4000C0", 0.5 "#ff0000", 1.0 "#ffff00", 2.0 "#ffffff")
set output "datasets/{{ dataset }}/plots/chiSquare-magnitude.pdf"
set xrange [{{ limmag.min - limmag.step }}:{{ limmag.max + limmag.step }}]
set yrange [0:{{ omega.max + omega.step }}] 

plot 'datasets/{{ dataset }}/plots/chiSquare-magnitude.tsv' using 1:2:(pointssize):3 title "Comparison" with points pt 5 ps variable lc palette 
