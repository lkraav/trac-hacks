jQuery(document).ready(function ($) {
  $("#field-owner").autocomplete("subjects", {
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
});
