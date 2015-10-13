jQuery(document).ready(function($) {
  // "convert" prefs text inputs (if any) to a select dropdown
  var $filters = $('#reportfilters');
  for (var field in dynvars) {
    var options = dynvars[field];
    if (options.length != 0) {
      var $input = $('input[name="' + field + '"]', $filters);
      if ($input.length != 0) {
          var $select = $('<select>').insertAfter($input);
          $(options).each(function() {
            $select.append($('<option>').attr('value', this).text(this));
          });
          $input.hide();
          alert($input.val());
          $select.val($input.val()).change(function() {
            var $select = $(this);
            var $input = $select.prev('input');
            $input.val($select.val()); // set hidden text input
            $input.closest('form').submit();
          });
      }
    }
  }
});
