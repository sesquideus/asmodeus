reset
unset key
unset border

set angles degrees
set polar
set samples 360

unset xtics 
unset ytics
unset colorbox
unset raxis

set terminal pngcairo enhanced font "Tex Gyre Pagella,10" fontscale 1.0 size {{ pixels }}, {{ pixels }} background rgb '{% if dark %}black{% else %}white{% endif %}'
set style line 1 lc rgb '#{% if dark %}404040{% else %}C0C0C0{% endif %}' lt 1 lw ({{ pixels }} / 1600) pt 7

set rtics 15 scale 0
set format r ''

set cbrange [{{ cblow }}:{{ cbhigh }}]
set palette defined ({% for node in palette %}{{ node[0] }} "{{ node[1] }}"{% if not loop.last %},{% endif %}{% endfor %})

set grid polar 15 ls 1

set size square
set rrange[0:90]
set trange[0:360]

set output "datasets/{{ dataset }}/plots/{{ observer }}/{{ quantity }}.png"
plot 'datasets/{{ dataset }}/plots/{{ observer }}/sky.tsv' using ($5<270 ? $5+90 : $5-270) : (90-$4) : \
    ({{ pixels }} / 40000.0 * (log10($12*1e10 + 1)**2) * 6) : \
    ({% if log %}log10{% endif %}(${{ column }})) with points pt 7 ps var palette
