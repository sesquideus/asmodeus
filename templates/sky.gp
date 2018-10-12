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

set terminal pngcairo enhanced font "Tex Gyre Pagella,10" fontscale 1.0 size {{ pixels }},{{ pixels }} background rgb '{% if dark %}black{% else %}white{% endif %}'
set style line 1 lc rgb '#{% if dark %}404040{% else %}C0C0C0{% endif %}' lt 1 lw ({{ pixels }} / 1600) pt 7

set rtics 15 scale 0
set format r ''

{% for column, quantity in quantities.items() %}
    {% if quantity == 'angularSpeed' %}
        set cbrange [0:50]
        {% if dark %}
            set palette defined (0 "#000080", 15 "#00ff00", 25 "#ffff00", 35 "#ffffff", 40 "#ff00ff")
        {% else %}
            set palette defined (0 "#000040", 10 "#0040C0", 20 "#00E040", 25 "#FFC000", 35 "#C0C000", 40 "#ff00ff")
        {% endif %}
    {% endif %}
    
    {% if quantity == 'speed' %} 
        set cbrange [0:70000]
        {% if dark %}
            set palette defined (0 "#000000", 20000 "#0000ff", 30000 "#00ffff", 40000 "#00ff00", 50000 "#ffff00", 60000 "#ff0000", 70000 "#ff00ff")
        {% else %}
            set palette defined (0 "#000000", 20000 "#0000ff", 30000 "#00ffff", 40000 "#00ff00", 50000 "#ffff00", 60000 "#ff0000", 70000 "#ff00ff")
        {% endif %}
    {% endif %}
    
    {% if quantity == 'mass' %} 
        set cbrange [-6:3]
        {% if dark %}
            set palette defined (-6 "#0000ff", -4 "#00ffff", -3 "#00ff00", -2 "#ffff00", -1 "#ff0000", 0 "#ff00ff", 3 "#FFFFFF")
        {% else %}
            set palette defined (-6 "#0000C0", -4 "#00C0C0", -3 "#00C000", -2 "#FF7F00", -1 "#FF0000", 0 "#FF00FF", 3 "#FFFFFF")
        {% endif %}
    {% endif %}

    {% if quantity == 'distance' %} 
        set cbrange [0:500000]
        set palette defined (0 "#ffffff", 80000 "#ff00ff", 160000 "#ff0000", 240000 "#ffff00", 320000 "#00ff00", 560000 "#00ffff", 1000000 "#0000ff")
    {% endif %}

    {% if quantity == 'elevation' %} 
        set cbrange [0:150000]
        {% if dark %}
            set palette defined (0 "#ffffff", 50000 "#ff00ff", 70000 "#ff0000", 90000 "#ffff00", 110000 "#00ff00", 130000 "#00ffff", 150000 "#0000ff")
        {% else %}
            set palette defined (0 "#000000", 50000 "#202020", 70000 "#404040", 90000 "#808080", 110000 "#C0C0C0", 150000 "#FFFFFF")
        {% endif %}
    {% endif %}

    {% if quantity == 'length' %} 
        set cbrange [0:250000]
        set palette defined (0 "#0000ff", 50000 "#00ffff", 100000 "#00ff00", 150000 "#ffff00", 200000 "#ff0000", 500000 "#ffffff")
    {% endif %}

    {% if quantity == 'power' %} 
        set cbrange [0:8]
        set palette defined (0 "#000000", 2 "#000080", 4 "#ff0000", 6 "#ffff00", 8 "#FFFFFF")
    {% endif %}

    {% if quantity == 'sighted' %} 
        set cbrange [0:1]
        {% if dark %}
            set palette defined (0 "#C00000", 1 "#FFFF00")
        {% else %}
            set palette defined (0 "#C0C0FF", 1 "#FF0000")
        {% endif %}
    {% endif %}

    set grid polar 15 ls 1
    
    set size square
    set rrange[0:90]
    set trange[0:360]

    {% for observer in observers %}
        set output "datasets/{{ dataset }}/plots/{{ quantity }}-{{ observer }}.png"
        plot 'datasets/{{ dataset }}/plots/{{ observer }}.tsv' using ($5<270 ? $5+90 : $5-270) : (90-$4) : \
        ({{ pixels }} / 40000.0 * ((log10($12*1e10 + 1))**{% if streaks %}2 * 6{% else %}2 * 6{% endif %})): \
        ({% if quantity == 'power' or quantity == 'mass' %}log10{% endif %}(${{ column }})) with points pt 7 ps var palette
    {% endfor %}
{% endfor %}
