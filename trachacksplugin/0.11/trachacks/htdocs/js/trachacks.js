jQuery(document).ready(function($) {
    var split_tags = function(text) {
        return $.grep(text.split(/ +/g), function(v) { return !!v });
    };

    /* Highlight tags from the mini-cloud that are in the tags field. */
    var highlight_tags = function() {
        var tags = split_tags($('#tags').val());

        $('#cloud a').each(function() {
            var anchor = $(this);
            var color = $.inArray(anchor.text(), tags) !== -1 ?
                        'yellow' : 'transparent';
            anchor.css('background-color', color);
        });
    };

    // This can be removed in Trac 1.0.2 since it is provided in layout.html
    $(".trac-target-new").attr("target", "_blank");

    // Move the label for each field into the hint block.
    $('.hint').each(function() {
        var hint = this;
        var fieldid = this.id.slice(0, -4);
    });

    // Handle focus/blur of input fields
    $.fn.handleInfo = function(hint, label) {
        return this.each(function() {
            var hintid = $(!hint ? '#' + this.id + 'hint' : hint);

            $(this).focus(function() { hintid.show() });
            $(this).blur(function() { hintid.hide() });

            if (hintid.attr('copied_label') == undefined) {
                var title = label;
                hintid.attr('copied_label', true);
                if (title == undefined) {
                    $('label[for="' + this.id + '"]').each(function() {
                        title = $(this).text();
                    });
                }
                hintid.prepend('<strong>' + title + '</strong>' +
                               '<span class="hint-pointer">&nbsp;</span>');
            }
        });
    }

    // Add hints to controls.
    $('#name, #title, #description, #installation, #tags').handleInfo();
    $('#cloud a').handleInfo('#tagshint');
    $('input[name="type"]').handleInfo('#typehint', 'Type');
    $('input[name="release"]').handleInfo('#releasehint', 'Compatibility');

    // Focus first error control. If none, focus #name.
    $('input[class="error"], textarea[class="error"], #name').filter(':first')
                                                             .focus();

    $('#tags').bind('keyup change', highlight_tags);

    $('#cloud a').click(function() {
        var anchor = $(this);
        var tag = anchor.text();
        var input = $('#tags');
        var tags = split_tags(input.val());
        var color;
        if ($.inArray(tag, tags) !== -1) {
            color = 'transparent';
            tags = $.grep(tags, function(v) { return v !== tag });
        } else {
            color = 'yellow';
            tags.push(tag);
        }
        anchor.css('background-color', color);
        input.val(tags.sort().join(' ') + ' ').focus().trigger('focus');
        return false;
    });

    highlight_tags();
});
