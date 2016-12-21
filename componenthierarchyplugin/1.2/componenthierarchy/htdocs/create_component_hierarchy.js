function ch_updateComponentOptions($) {
  var options = $('#field-component').find('option');
  var handled = [];
  var alle = [];

  options.each(function () {
    var jThis = $(this);
    var opt_val = jThis.val();

    alle.push(opt_val);

    var thisLevel = jThis.attr('level');
    if (!thisLevel) {
      thisLevel = 1;
      jThis.attr('class', 'indention_level_1');
    }

    if ($.inArray(opt_val, handled) == -1 && component_children[opt_val]) {
      thisLevel++;

      $.each(component_children[opt_val].reverse(), function (idx, value) {
        var jChildOpt = $('#field-component').find('option[value="' + value + '"]');
        jChildOpt.attr('level', thisLevel);
        jChildOpt.attr('class', 'indention_level_' + thisLevel);
        jChildOpt.insertAfter(jThis);
      });

      handled.push(opt_val);
    }
  });
}

jQuery(document).ready(function ($) {
  $('#field-component').bind("onUpdate", function () {
    // works with a custom event triggered from SimpleMultiProjectPlugin
    ch_updateComponentOptions($);
  });
  // immediate update (not completely sure if this works)
  ch_updateComponentOptions($);
});
