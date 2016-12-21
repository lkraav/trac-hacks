(function($){

    $(window).load(function() {
        $('.trac-timetracking-chart').each(function (index) {
            var chart_data = window['timetracking_chart_' + this.id.slice(-12)];

            var $canvas = $("<canvas/><canvas>")
            var canvas = $canvas.get(0);
            $canvas.attr('width', chart_data.width);
            $canvas.attr('height', chart_data.height);
            
            var chart_div = $(this).empty().removeClass('system-message');
            chart_div.append(canvas);
            
            var chart = new Chart(canvas.getContext("2d"));
            chart.Line(chart_data.data, chart_data.options);

        });
    });
 })(jQuery);
