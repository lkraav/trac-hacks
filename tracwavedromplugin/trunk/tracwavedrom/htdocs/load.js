/*
 * Copyright (C) 2013-2023 Jun Omae
 * All rights reserved.
 *
 * This software is licensed as described in the file COPYING, which
 * you should have received as part of this distribution.
 */
jQuery(function($) {
    var loaded = 0;
    var process = function() {
        WaveDrom.ProcessAll();
        $(document).ajaxComplete(function(event, xhr, settings) {
            if ($('script[type=WaveDrom]').length !== 0) {
                WaveDrom.ProcessAll();
            }
        });
    };
    var onload = function() {
        loaded++;
        if (loaded === 2)
            process();
    };
    var add_script = function(src) {
        var script = document.createElement('script');
        script.onload = onload;
        script.type = 'text/javascript';
        script.async = true;
        script.src = src;
        document.head.appendChild(script);
    };
    var url = tracwavedrom['location'];
    if (!url.endsWith('/'))
        url += '/';
    add_script(url + 'skins/' + tracwavedrom.skin + '.js');
    add_script(url + 'wavedrom.min.js');
});
