jQuery(function($) {
  $(".ticketstats-chart").each(function () {
    var rid = $(this).attr('id').split('-')[2];
    Plotly.newPlot($(this)[0], window['chart_' + rid]['ticket_data'], {barmode: 'group'});
  });
});
