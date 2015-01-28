(function($) {
  // flip checkboxes named same as event source's id
  function flip(event) {
    var $filters = $("#filters");
    var name = this.id.slice(6);
    $filters.find('input[name="' + name + '"]')
            .filter(':checkbox')
            .each(function() { $(this).prop("checked", !this.checked) });
  }

  // enable only clicked checkbox and clear others
  function selectone(event) {
    var $filters = $("#filters");
    var that = (this.tagName == 'LABEL' ) ? $('#' + $(this).attr('for'))[0] : this;
    $('input[name="' + that.name + '"]', $filters).prop('checked', false);
    $(that).prop('checked', true);
  }

  // bind "selectone" above to checkboxes in page,
  // bind "flip" above to labels in page.
  function binder() {
    var $filters = $("#filters");
    $filters.on('dblclick', 'label', flip);
    $filters.on('dblclick', ':checkbox, :checkbox + label', selectone);
  }

  $(document).ready(function() { binder() })
})(jQuery);
