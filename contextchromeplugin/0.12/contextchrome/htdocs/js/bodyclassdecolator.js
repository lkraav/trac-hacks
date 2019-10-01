/*
 * Copyright (C) 2019 MATOBA Akihiro <matobaa+trac-hacks@gmail.com>
 * All rights reserved.
 *
 * This software is licensed as described in the file COPYING, which
 * you should have received as part of this distribution.
 */

 (function($) {
	$(function() {
        if(typeof(contextchrome_bodyclass) == 'string')
          $('body').addClass(contextchrome_bodyclass);
    })
})(jQuery);
