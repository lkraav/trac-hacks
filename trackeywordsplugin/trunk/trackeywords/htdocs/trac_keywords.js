jQuery(function($) {

  field_id = document.getElementById('tags') ? "tags" : "field-keywords";
  function addRemoveTag(w) {
    var el = document.getElementById(field_id);
    var orig = el.value;
    var newval = orig.replace(new RegExp('\\b' + w + '\\b'), '');
    var link = document.getElementById('trac-keyword-' + w);
    if (orig != newval) { // remove tag.
        if(link) link.className = '';
    } else {
        newval = orig + (orig ? ' ' : '') + w;
        if(link) link.className = 'trac-keyword';
    }
    el.value = newval.replace(/^\s+|\s+$/, '');
  }

  var $fieldset = $('<fieldset id="trac-keywords" />');
  $fieldset.append('<legend>Add Keywords</legend>')
  var resource_keywords = document.getElementById(field_id).value.split(' ');
  $.each(trac_keywords, function(i, item) {
    $fieldset.append($('<a href="#">' + item[0] + '</a> ')
      .attr({
        'title': item[1],
        'id': 'trac-keyword-' + item[0],
        'class': $.inArray(item[0], resource_keywords) != -1 ? 'trac-keyword': '',
      })
      .on('click', function() {
        addRemoveTag($(this).text());
        return false;
      }));
  })

  $("div.ticket #properties").after($fieldset);
  $("div.wiki #changeinfo").after($fieldset);

})
