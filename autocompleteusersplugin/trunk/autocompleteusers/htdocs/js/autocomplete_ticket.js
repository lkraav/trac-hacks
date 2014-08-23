jQuery(document).ready(function ($) {
  $("[id$=reassign_owner]").autocomplete("../subjects", {
    formatItem: formatItem
  });

  $("#field-cc").autocomplete("../subjects", {
    multiple: true,
    formatItem: formatItem
  });

  $("input:text#field-reporter").autocomplete("../subjects", {
    formatItem: formatItem
  });
});
