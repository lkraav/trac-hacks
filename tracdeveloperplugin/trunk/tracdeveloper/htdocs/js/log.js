jQuery(function ($) {
  var $metanav = $('#metanav li');
  var $last = $metanav.eq($metanav.length - 1);
  $last.removeClass('last');
  $last.after('<li class="last"><a href="#" id="tracdeveloper-logbutton">Log</a></li>');
  $('#tracdeveloper-logbutton').click(function () {
    $('#tracdeveloper-log').toggle();
    return false;
  });

  $('body').append('<div id="tracdeveloper-log">' +
                   '<table class="listing">' +
                   '<thead><tr>' +
                   '<th>Time</th><th>Module</th><th>Level</th><th>Message</th>' +
                   '</tr></thead>' +
                   '<tbody></tbody>' +
                   '</table></div>');
  var $tbody = $("#tracdeveloper-log tbody");
  log_data.forEach(function(row_data, i) {
    var row = $.htmlFormat('<tr class="$1"><td>$2</td><td>$3</td><td>$4</td><td>$5</td></tr>',
        i % 2 ? 'even' : 'odd', row_data[0], row_data[1], row_data[2], row_data[3]);
    $tbody.append(row);
  });

  $('#tracdeveloper-log').hide();
});
