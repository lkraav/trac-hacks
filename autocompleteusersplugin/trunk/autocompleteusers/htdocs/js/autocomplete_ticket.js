jQuery(function ($) {
  $("#field-owner, input:text#field-reporter, #action input:text[id$=_reassign_owner], .trac-autocomplete").autocomplete(subjects_href, {
    formatItem: formatItem
  });

  $("#field-cc, .trac-autocomplete-multi").autocomplete(subjects_href, {
    multiple: true,
    formatItem: formatItem,
    delay: 100
  });

  for (var i = 0; i < autocomplete_fields.length; i++) {
    $("#field-" + autocomplete_fields[i]).autocomplete(subjects_href, {
      formatItem: formatItem
    });
  }
  for (var i = 0; i < autocomplete_fields_multi.length; i++) {
    $("#field-" + autocomplete_fields_multi[i]).autocomplete(subjects_href, {
      multiple: true,
      formatItem: formatItem,
      delay: 100
    });
  }
});
