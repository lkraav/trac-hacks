jQuery(function ($) {
  $("#field-owner, #action input:text[id$=_reassign_owner]").autocomplete("subjects", {
    formatItem: formatItem
  });

  $("#field-cc").autocomplete("subjects", {
    multiple: true,
    formatItem: formatItem,
    delay: 100
  });

  $("input:text#field-reporter").autocomplete("subjects", {
    formatItem: formatItem
  });

  for (var i = 0; i < autocomplete_fields.length; i++) {
    $("#field-" + autocomplete_fields[i]).autocomplete("subjects", {
      formatItem: formatItem
    });
  }
});
