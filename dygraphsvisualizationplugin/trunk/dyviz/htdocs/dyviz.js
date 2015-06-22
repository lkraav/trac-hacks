// Populate data with data from provided jQuery table selector.

var populate = function(table, labels, data){
    // Loop through column headers.
    table.find('thead th').each(function(i, column_header) {
        var th = jQuery(column_header);
        var a = th.find('a');
        if (a.length)
            var label = jQuery.trim(a.text());
        else
            var label = jQuery.trim(th.text());
        labels.push(label);
    });
    
    // Loop through rows;
    //  - i is row index, e is row element.
    table.find('tbody tr:has(td)').each(function(i, e) {
        var tr = jQuery(e);
        var row = [];

        // Loop through the cells of each row.
        //  - j is column index, f is cell element
        tr.find('td').each(function(j, f) {
            var td = jQuery(f);
            // Find the value.
            var a = td.find('a');
            if (a.length)
              var raw = jQuery.trim(a.text());
            else
              var raw = jQuery.trim(td.text());
            
            // Use heuristics to determine the data type.
            var value = null;
            var type = null;
            
            // Check for a date first.
            var ms = Date.parse(raw);
            if (isNaN(ms)) {
                // Try strict match on YYYY-MM-DD (or YYYY/MM/DD) format.
                var match =
                    /([0-9]{4,4})[-\/]([0-9]{2,2})[-\/]([0-9]{2,2})/.exec(raw);
                if (match) {
                    var year = parseInt(match[1]);
                    var month = parseInt(match[2]) - 1;
                    var day = parseInt(match[3]);
                    ms = new Date(year, month, day).getTime();
                }
            }
            if (!isNaN(ms) && /[-\/]/.test(raw)){
                // Adjust for client-side timezone.
                value = new Date(ms + new Date().getTimezoneOffset()*60000);
                type = 'date';
            } else {
                // Not a date; check for a number.
                if (raw[0] == '#')
                    raw = raw.substr(1);
                value = parseFloat(raw);
                type = 'number';
                if (isNaN(value)) {
                    // Not a number; assume a string.
                    value = raw;
                    type = 'string';
                }
            }
            
            row.push(value);
        });

        data.push(row);
    });
}

function darkenColor(colorStr) {
    // Defined in dygraph-utils.js.
    var color = Dygraph.toRGB_(colorStr);
    color.r = Math.floor((255 + color.r) / 2);
    color.g = Math.floor((255 + color.g) / 2);
    color.b = Math.floor((255 + color.b) / 2);
    return 'rgb(' + color.r + ',' + color.g + ',' + color.b + ')';
}

function barChartPlotter(e) {
    var ctx = e.drawingContext;
    var points = e.points;
    var y_bottom = e.dygraph.toDomYCoord(0);

    ctx.fillStyle = darkenColor(e.color);

    // Find the minimum separation between x-values.
    // This determines the bar width.
    var min_sep = Infinity;
    for (var i = 1; i < points.length; i++) {
      var sep = points[i].canvasx - points[i - 1].canvasx;
      if (sep < min_sep) min_sep = sep;
    }
    var bar_width = Math.floor(2.0 / 3 * min_sep);

    // Do the actual plotting.
    for (var i = 0; i < points.length; i++) {
      var p = points[i];
      var center_x = p.canvasx;

      ctx.fillRect(center_x - bar_width / 2, p.canvasy,
          bar_width, y_bottom - p.canvasy);

      ctx.strokeRect(center_x - bar_width / 2, p.canvasy,
          bar_width, y_bottom - p.canvasy);
    }
}

// Multiple column bar chart
function multiColumnBarPlotter(e) {
  // We need to handle all the series simultaneously.
  if (e.seriesIndex !== 0) return;

  var g = e.dygraph;
  var ctx = e.drawingContext;
  var sets = e.allSeriesPoints;
  var y_bottom = e.dygraph.toDomYCoord(0);

  // Find the minimum separation between x-values.
  // This determines the bar width.
  var min_sep = Infinity;
  for (var j = 0; j < sets.length; j++) {
    var points = sets[j];
    for (var i = 1; i < points.length; i++) {
      var sep = points[i].canvasx - points[i - 1].canvasx;
      if (sep < min_sep) min_sep = sep;
    }
  }
  var bar_width = Math.floor(2.0 / 3 * min_sep);

  var fillColors = [];
  var strokeColors = g.getColors();
  for (var i = 0; i < strokeColors.length; i++) {
    fillColors.push(darkenColor(strokeColors[i]));
  }

  for (var j = 0; j < sets.length; j++) {
    ctx.fillStyle = fillColors[j];
    ctx.strokeStyle = strokeColors[j];
    for (var i = 0; i < sets[j].length; i++) {
      var p = sets[j][i];
      var center_x = p.canvasx;
      var x_left = center_x - (bar_width / 2) * (1 - j/(sets.length-1));

      ctx.fillRect(x_left, p.canvasy,
          bar_width/sets.length, y_bottom - p.canvasy);

      ctx.strokeRect(x_left, p.canvasy,
          bar_width/sets.length, y_bottom - p.canvasy);
    }
  }
}

var draw = function(selector, labels, data, options) {
    var chart = new Dygraph(
        get_div(selector),
        data,
        options
    );
}

// Insert the graph just before the table; return the div element.
var get_div = function(table){
    // The 'dyviz_above' and 'dyviz_below' divs provide a placeholder for
    // use with the 'labelsDiv' option of dygraphs.
    table.before('<div id="dyviz_above"/>');
    table.before('<div id="dyviz"/>');
    table.before('<div id="dyviz_below"/>');
    return jQuery('#dyviz').get(0);
}
