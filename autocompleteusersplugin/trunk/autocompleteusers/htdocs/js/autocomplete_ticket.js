jQuery(function ($) {
  var path = newticket ? "subjects" : "../subjects"

  $("#field-owner, input:text#field-reporter, #action input:text[id$=_reassign_owner], .trac-autocomplete").autocomplete(path, {
    formatItem: formatItem
  });

  $("#field-cc, .trac-autocomplete-multi").autocomplete(path, {
    multiple: true,
    formatItem: formatItem,
    delay: 100
  });

  for (var i = 0; i < autocomplete_fields.length; i++) {
    $("#field-" + autocomplete_fields[i]).autocomplete(path, {
      formatItem: formatItem
    });
  }
  for (var i = 0; i < autocomplete_fields_multi.length; i++) {
    $("#field-" + autocomplete_fields_multi[i]).autocomplete(path, {
      multiple: true,
      formatItem: formatItem,
      delay: 100
    });
  }
});
