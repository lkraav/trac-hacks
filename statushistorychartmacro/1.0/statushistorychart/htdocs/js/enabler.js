/*
 * Copyright (C) 2013, 2015 MATOBA Akihiro <matobaa+trac-hacks@gmail.com>
 * All rights reserved.
 * 
 * This software is licensed as described in the file COPYING, which
 * you should have received as part of this distribution.
 */

(function($) {
  $(document).ready(function() {
    base = document.location.href.slice(0,
        -document.location.pathname.length
        - document.location.search.length)
        + $('link[rel="search"]').attr('href').slice(0, -7);
    $(".statushistorychart").each(function(index) {
    	statushistorychart_data = eval(this.id + "_data");
    	statushistorychart_yaxis = eval(this.id + "_yaxis");
	    $.plot($(this), statushistorychart_data, {
	      legend:{ show: false },
	      grid : { hoverable : true,
	               clickable : true},
	      xaxis :{mode : "time"},
	      yaxis :{max : statushistorychart_yaxis.length - 1,
	              tickFormatter : function(i, o) {return statushistorychart_yaxis[i]},
	              minTickSize : 1},
	    });  // end of plot
	    $(this).bind("plothover", function(event, pos, item) {
	      if (item) { // hover
	        item.series.lines.lineWidth = 4;
	        $(this).data('plot').draw();
	        $(this).data('item', item);
	        $("#statushistorychart_tooltip").remove();
	        series = item.series;
	        xaxis = series.xaxis;
	        yaxis = series.yaxis;
	        $('<div id="statushistorychart_tooltip">#' + series.label
	        		+ '(' + yaxis.ticks[item.datapoint[1]].label
	        		+ ' on ' + xaxis.tickFormatter(item.datapoint[0],xaxis) + ')'
	        		+'</div>').css({
	          position : 'absolute',
	          top : item.pageY - 30,
	          left : item.pageX + 5,
	          border : '1px solid #fdd',
	          padding : '2px',
	          'background-color' : '#fee',
	        }).appendTo("body")
	        .attr('item', item);
	      } else { // mouseout
	        item = $(this).data('item');
	        if(item) {
	          item.series.lines.lineWidth = 2;
	          $(this).data('plot').draw();
	        }
	        $("#statushistorychart_tooltip").remove();
	      }
	    });  // end of plothover
	    $(this).bind("plotclick", function(event, pos, item) {
	      if (item) {
	        location.href = base + "/ticket/" + item.series.label + "#" + item.series.data[item.dataIndex][2]
	      }
	    });  // end of plotclick
    });  // end of each
  }); // end of document.ready
})(jQuery);