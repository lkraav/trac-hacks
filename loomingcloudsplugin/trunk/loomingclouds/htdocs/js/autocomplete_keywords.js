jQuery(function($) {
  function formatTags(row) {
    return row[0] + " (" + row[1] + ")"
  }
  $("#field-keywords").autocomplete('tags', {
    extraParams: {format: 'txt'},
    multiple: true,
    formatItem: formatTags
  });
});
