jQuery(function ($) {
  var path = newticket ? "subjects" : "../subjects"

  $("#field-owner, input:text#field-reporter, #action input:text[id$=_reassign_owner]").autocomplete(path, {
    formatItem: formatItem
  });

  $("#field-cc").autocomplete(path, {
    multiple: true,
    formatItem: formatItem,
    delay: 100
  });

  for (var i = 0; i < autocomplete_fields.length; i++) {
    $("#field-" + autocomplete_fields[i]).autocomplete(path, {
      formatItem: formatItem
    });
  }
});
