jQuery(document).ready(function ($) {
  var get_url = function () {
    return $('link[rel="search"]').attr('href').replace(/\/search/, '');
  };

  var decode = function (encoded) {
    return encoded.replace(/&lt;/g, "<").replace(/&gt;/g, ">");
  };

  var href = function (text) {
    return '<a href="#codereview" title="View/edit code review">'
      + text + '</a>';
  };

  function scrollIntoView (eleID) {
     var e = document.getElementById(eleID);
     if (!!e && e.scrollIntoView) {
         e.scrollIntoView();
     }
  }

  // add a "warning" to the page
  var html = '<div class="codereviewstatus" id="message">'
    + '<div class="system-message ' + review.encoded_status.toLowerCase() + '" id="message">'
    + 'Code review status is <strong>' + href(review.status) + '</strong>. '
    + 'Update status and view/add a summary ' + href("below") + '.'
    + '</div>'
    + '</div>';
  $('#ctxtnav').after(html);

  // begin review status form
  html = '<form id="codereviewform" action="' + window.location.href + '" method="POST">'
    + '<h1 id="codereview">Code Review</h1>'
    + '<dl id="review">'
    + '  <dt class="property">Review summary:</dt>';

  // add past summaries
  $(review.summaries).each(function (i, summary) {
    html += '<dd><h3 class="summary">' + summary.reviewer;
    if (summary.status.length)
      html += ' set to ' + summary.status;
    else
      html += ' commented';
    html += ' on ' + summary.pretty_when + ' (' + summary.pretty_timedelta + ' ago)</h3>' + decode(summary.html_summary) + '<br/></dd>';
  });

  // link to tickets if just saved comments
  if (tickets.length) {
    var s = tickets.length == 1 ? '' : 's';
    html += '<dd><div id="status-saved" class="system-message notice">' +
            '<a class="trac-close-msg" href="#" title="Hide this notice">' +
            '<span>close</span></a>' +
            'Status saved. See ticket' + s + ' ';
    $(tickets).each(function (i, ticket) {
      html += '<a href="' + get_url() + '/ticket/' + ticket + '">#' + ticket + '</a>';
      if (i < tickets.length - 1)
        html += ', ';
    });
    html += '.</div></dd>';
  }

  // add new summary fields and finish form
  html += '  <dd><textarea id="review-summary" name="summary" rows="10" cols="78"/></dd>'
    + '  <dt class="property">Review status:</dt>'
    + '  <dd><select id="review-status" name="status">';
  $(statuses).each(function (i, choice) {
    html += '<option';
    if (choice == review.status)
      html += ' selected="selected"';
    html += ' value="' + choice + '">' + choice + '</option>';
  });
  html += '  </select>'
    + '  <input type="submit" id="reviewbutton" name="reviewbutton" value="Submit review"/></dd>'
    + '  <input type="hidden" name="__FORM_TOKEN" value="'
    + form_token + '"/></dd>'
    + '</dl>'
    + '</form>';
  $('#content').append(html);
  $('#codereviewform').after($('#help')); // move help after form
  scrollIntoView('status-saved');
});
