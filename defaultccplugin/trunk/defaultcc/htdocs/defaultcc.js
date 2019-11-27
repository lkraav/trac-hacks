jQuery(function ($) {
  if (typeof component_cc != 'undefined') {
    // Component detail page
    var $div = $('form.mod fieldset div.field').last();
    var $new_div = $('<div class="field" />');
    var $new_label = $('<label>Default CC:<br /></label>');
    var $new_input = $('<input type="text" name="defaultcc" />');
    $div.before($new_div);
    $new_div.append($new_label);
    $new_label.append($new_input);
    if (component_cc) {
      $new_input.val(component_cc);
    }
  } else if (typeof component_ccs != 'undefined') {
    // Component listing page
    var $buttons = $('#addcomponent fieldset div.buttons');
    $buttons.before('<div class="field"><label>Default CC: ' +
                    '<input type="text" name="defaultcc" /></label></div>');
    var $table = $('#complist');
    $table.find('thead tr th:eq(2)').after($('<th>Default CC</th>'));
    $table.find('tbody tr td.owner').each(function (i, el) {
      $td_owner = $(el);
      var component = $td_owner.prev().find('a').text();
      var $defaultcc = $('<td class="defaultcc" />');
      if (component in component_ccs) {
        $defaultcc.text(component_ccs[component]);
      }
      $td_owner.after($defaultcc);
    });
  }
});
