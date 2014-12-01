jQuery(document).ready(function($) {
    if ($.fn.disableOnSubmit) {
        return;  // #10138 has been fixed
    }
    $("#content form[method=post]").find(":submit").click(function() {
        var form = $(this).closest("form");
        if (form.hasClass("trac-submit-is-disabled")) {
            form.bind("submit.prevent-submit", function() { return false });
            $(window).bind("unload", function() {
                form.unbind("submit.prevent-submit");
            });
        }
        else {
            form.addClass("trac-submit-is-disabled");
            $(window).bind("unload", function() {
                form.removeClass("trac-submit-is-disabled");
            })
        }
    });
});
