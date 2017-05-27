jQuery(document).ready(function($) {
    /* auto preview */
    var args = {realm: "milestone", escape_newlines: 1};
    $("#description").autoPreview(ms_preview_renderer, args, function(textarea, text, rendered) {
        $("#mschange div.comment").html(rendered);
        if (rendered)
          $("#mschange").show();
        else if ($("#mschange ul.changes").length == 0)
          $("#mschange").hide();
    });
});