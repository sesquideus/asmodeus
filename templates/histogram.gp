set terminal pdf size 18cm,11cm font "Minion Pro, 20"
set ylabel "Relative frequency"
set grid
set key top right height 1 width 1 box lw 1

set style fill transparent solid 0.4 noborder

{% for observer in observers %}
    {% for name, histogram in histograms._asdict().items() %}
        set output "datasets/{{ dataset }}/histograms/{{ observer }}/{{ name }}.pdf"
        set title "AMOS {{ histogram.name }} distribution at {{ observer|upper }}"
        set xlabel "{{ histogram.name }} (bin width {{ histogram.bin }})"
        set xrange [{{ histogram.min }}:{{ histogram.max }}]
        set yrange [0:*] 
        set format x '%.0f{{ histogram.xunit }}'
        {% if histogram.log %}set logscale x{% endif %}
        plot 'datasets/{{ dataset }}/histograms/{{ observer }}/{{ name }}.tsv' using ($1 + {{ histogram.bin }} / 2.0):2 title "Simulation" with boxes linecolor rgb '#0020FF', \
            'datasets/{{ dataset }}/histograms/amos-{{ name }}.tsv' using ($1 + {{ histogram.bin }} / 2.0):2 title "AMOS" with boxes linecolor rgb '#FF0000'
    {% endfor %}
{% endfor %}
