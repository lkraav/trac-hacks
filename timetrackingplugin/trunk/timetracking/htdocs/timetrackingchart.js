(function($){

    $(window).load(function() {
        $('.trac-timetracking-chart').each(function (index) {
            var chart_data = window['timetracking_chart_' + this.id.slice(-12)];
            var $chart_div = $(this).empty().removeClass('system-message');
            var chart_div = $chart_div.get(0);
            Plotly.newPlot(chart_div, [chart_data.data], chart_data.layout, chart_data.options);
        });
    });
 })(jQuery);
