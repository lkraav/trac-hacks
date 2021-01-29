jQuery(function($) {

  field_id = document.getElementById('tags') ? "tags" : "field-keywords";

  // Remove or add a keyword tag to the field.
  function addRemoveKeyword(w) {
    var el = document.getElementById(field_id);
    var orig = el.value;
    // Remove keyword including white spaces and separator, match case-insensitive
    var filter = function(v) {
      return v.length !== w.length || v.toLowerCase() !== w.toLowerCase();
    };
    var orig_split = orig.split(/[;,\s]+/).filter(function(value, index, arr) {
      return value != '';
    });
    var newval;
    var link = document.getElementById('trac-keyword-' + w);
    if (orig_split.includes(w)) { // remove keyword
        newval = $.grep(orig_split, filter);
        if(link) link.className = '';
    } else { // add keyword
        newval = orig_split;
        newval.push(w);
        if(link) link.className = 'trac-keyword';
    }
    // Strip leading and trailing white spaces and separator.
    el.value = newval.join(' ').replace(/^[;,\s]+|[;,\s]+$/, '');
    // trigger change event on the edit field in order to evoke ticket preview
    el.dispatchEvent(new Event('change'));

  }

  // Avoid duplicate insertion of keyword section.
  if ($('#trac-keywords').length > 0) return;
  var $fieldset = $('<fieldset id="trac-keywords" />');
  $fieldset.append('<legend>Add Keywords</legend>')
  $ul = $('<ul></ul>');
  $fieldset.append($ul)
  // Case-insensitive: compare to lower case.
  var field = document.getElementById(field_id).value.toLowerCase();
  // Regex splits the content of the field at separator characters.
  var resource_keywords = field.split(/[;,\s]+/);
  // Iterate over each keyword defined in the Trac ini-file.
  $.each(trac_keywords, function(i, item) {
    $ul.append($('<li><a href="#">' + item[0] + '</a></li> ')
      .attr({
        'title': item[1],
        'id': 'trac-keyword-' + item[0],
        'class': $.inArray(item[0].toLowerCase(), resource_keywords) != -1 ? 'trac-keyword' : '',
      })
      .on('click', function() {
        addRemoveKeyword($(this).text());
        return false;
      }));
  })

  $("div.ticket #properties").after($fieldset);
  $("div.wiki #changeinfo").after($fieldset);

})
