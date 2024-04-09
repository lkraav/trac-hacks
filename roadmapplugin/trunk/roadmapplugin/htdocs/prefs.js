if (window.roadmapplugin) {
    jQuery(function($) {
        var fragment = $('<div></div>').html(window.roadmapplugin);
        var buttons = $('form#prefs div.buttons');
        buttons.before(fragment.contents());
    });
}
