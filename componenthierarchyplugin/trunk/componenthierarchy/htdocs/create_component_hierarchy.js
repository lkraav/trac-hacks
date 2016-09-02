function ch_updateComponentOptions()
{
    var options = $('#field-component option');
    var handled = [];
    var alle = [];

    options.each(function() {
        var jThis = $(this);
        var opt_text = jThis.text();
        var opt_val  = jThis.val();

        alle.push(opt_val);

        var thisLevel = jThis.attr('level');
        if (!thisLevel) {
            thisLevel = 1;
            jThis.attr('class', 'indention_level_1');
        }

        if ($.inArray(opt_val, handled) == -1 && component_children[opt_val]) {
            thisLevel++;

            var nbsp = "";
            if ($.browser.msie) {
                // The IE does not support css styling for option tags
                for (var i = 1; i < thisLevel; i++) {
                    nbsp = nbsp + "    ";
                }
            }
            $.each(component_children[opt_val].reverse(), function(idx, value) {
                var jChildOpt = $('#field-component option[value="' + value + '"]');
                jChildOpt.attr('level', thisLevel);
                jChildOpt.attr('class', 'indention_level_' + thisLevel);
                if ($.browser.msie) {
                    jChildOpt.text(nbsp + value);
                }
                jChildOpt.insertAfter(jThis);
            });
        
            handled.push(opt_val);
        }
    });
}

jQuery(document).ready(function($) {
    $('#field-component').bind("onUpdate", function() {
        // works with a custom event triggered from SimpleMultiProjectPlugin
        ch_updateComponentOptions();
    });
    // immediate update (not completely sure if this works)
    ch_updateComponentOptions();
});
