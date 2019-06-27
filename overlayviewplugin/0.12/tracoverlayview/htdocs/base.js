jQuery(document).ready(function($) {
    if (!window.overlayview)
        return;

    var colorbox = 'colorbox';

    function loadStyleSheet(href, type) {
        var link;
        var re = /(?:[?#].*)?$/;
        var tmp = href.replace(re, '');
        $('link[rel="stylesheet"]').each(function() {
            var val = this.getAttribute('href');
            val = (val || '').replace(re, '');
            if (val === tmp) {
                link = this;
                return false;
            }
        });
        if (!link) {
            $.loadStyleSheet(href, type);
        }
        else if (link.getAttribute('disabled')) {
            link.removeAttribute('disabled');
        }
    }

    function colorbox_on_load() {
        var videos = [];
        $.each(videos_map, function(src, video) {
            video.pause();
            videos.push(video);
        });
        if (videos.length !== 0) {
            $(videos).unbind();
        }
        var options = $(this).data(colorbox);
        if (options.inline) {
            var href = $(options.href);
            if (href.is('video') && !href[0].src) {
                href[0].src = href.attr('data-src');
                return;
            }
        }
    }

    function colorbox_on_complete() {
        var element = $(this);
        var loaded = $('#cboxLoadedContent');
        var target;
        target = loaded.children('video');
        if (target.length === 1) {
            var events = {mouseenter: video_controls_show,
                          mouseleave: video_controls_hide};
            var video = target[0];
            if (video.readyState !== 0) {
                fit_video(video);
            }
            else {
                events.loadedmetadata = video_loadedmetadata;
            }
            video.controls = true;
            target.bind(events);
            return;
        }
        target = loaded.children('div.overlayview-no-preview');
        if (target.length === 1) {
            $.colorbox.resize({innerWidth: target.width()});
            return;
        }
        target = loaded.children('div.image-file').children('img');
        if (target.length === 1) {
            target.each(function() {
                var url = target.attr('src');
                var options = $.extend({}, basic_options, {
                    title: element.attr('data-colorbox-title'),
                    width: false,
                    href: url,
                    photo: true,
                    open: true
                });
                element.colorbox(options);
            });
            return;
        }
        target = loaded.find('table.code thead tr th.lineno');
        if (target.length === 1) {
            target.each(function() {
                var url = element.attr('href');
                var change = function() {
                    var anchor = $(this).attr('href');
                    if (anchor.substring(0, 2) === '#L') {
                        $(this).attr('href', url + anchor);
                    }
                };
                loaded.find('table.code tbody tr th[id]').each(function() {
                    this.removeAttribute('id');
                    var anchor = $(this).children('a[href]');
                    if (anchor.length === 1) {
                        anchor.each(change);
                    }
                });
            });
            return;
        }
    }

    function colorbox_on_closed() {
        var loaded = $('#cboxLoadedContent');
        var video = loaded.children('video');
        if (video.length !== 0) {
            video[0].pause();
        }
    }

    function escape_regexp(text) {
        return text.replace(/[^-A-Za-z0-9_]/g, '\\$&');
    }

    function build_exts_re(exts) {
        if (exts.length === 0)
            return {test: function() { return false }};
        var pattern = '\\.(?:' + $.map(exts, escape_regexp).join('|')
                    + ')(?:$|[#?])';
        return new RegExp(pattern, 'i');
    }

    function get_size(size, dimension) {
        if (/%/.test(size)) {
            var distance = dimension === 'w' ? w.width() : w.height();
            return (parseInt(size, 10) / 100.0 * distance) | 0;
        }
        else {
            return parseInt(size, 10);
        }
    }

    function fit_video(video) {
        var videoWidth = video.videoWidth;
        if (!videoWidth)
            return;
        var videoHeight = video.videoHeight;
        var maxWidth = get_size(basic_options.maxWidth, 'w');
        var maxHeight = get_size(basic_options.maxHeight, 'h');
        var width, height;
        if (videoWidth / maxWidth > height / maxHeight) {
            width = Math.min(videoWidth, maxWidth);
            height = (videoHeight * (1.0 * width / videoWidth)) | 0;
        }
        else {
            height = Math.min(videoHeight, maxHeight);
            width = (videoWidth * (1.0 * height / videoHeight)) | 0;
        }
        video.width = width;
        video.height = height;
        $.colorbox.resize({innerWidth: width, innerHeight: height});
    }

    function video_loadedmetadata() {
        fit_video(this);
    }

    function video_controls_show() {
        this.controls = true;
    }

    function video_controls_hide() {
        this.controls = false;
    }

    var w = $(window);
    window.overlayview.loadStyleSheet = loadStyleSheet;
    var script_data = window.overlayview;
    var baseurl = script_data.baseurl;
    var attachment_url = baseurl + 'attachment/';
    var raw_attachment_url = baseurl + 'raw-attachment/';
    var basic_options = {
        opacity: false, transition: 'none', speed: 200, width: '96%',
        maxWidth: '96%', maxHeight: '92%', preloading: false,
        onLoad: colorbox_on_load, onComplete: colorbox_on_complete,
        onClosed: colorbox_on_closed};
    var attachments = $('div#content > div#attachments');
    var image_re = build_exts_re(script_data.images);
    var video_re = build_exts_re(script_data.videos);
    var videos_map = {};

    function build_colorbox_options(href, title) {
        var options = $.extend({}, basic_options);
        if (image_re.test(href)) {
            href = raw_attachment_url +
                   href.substring(attachment_url.length);
            options.transition = 'elastic';
            options.photo = true;
            options.width = false;
        }
        else if (video_re.test(href)) {
            var src = raw_attachment_url +
                      href.substring(attachment_url.length);
            var video;
            if (src in videos_map) {
                video = videos_map[src];
                href = $(video);
            }
            else {
                href = $('<video />').attr('data-src', src);
                video = href[0];
                video.controls = true;
                video.muted = true;
                videos_map[src] = video;
            }
            options.inline = true;
            options.transition = 'elastic';
            options.width = false;
        }
        else {
            href = baseurl + 'overlayview/' +
                   href.substring(baseurl.length)
                       .replace(/\.([A-Za-z0-9]+)$/, '%2e$1');
        }
        options.href = href;
        options.title = title;
        return options;
    }

    function rawlink() {
        var self = $(this);
        var href = self.attr('href');
        var anchor = self.prev('a');
        if (anchor.length === 0) {
            anchor = self.parent('.noprint').prev('a.attachment');
        }
        if (anchor.length === 0) {
            return;
        }
        if (attachments.length !== 0 && $.contains(attachments[0], this)) {
            anchor.attr('rel', 'colorbox-attachments');
        }
        var href = anchor.attr('href');
        if (href.indexOf(attachment_url) === 0) {
            if (href.slice(-1) === '/') {
                // workaround for an attachment started with a hash character
                var match = /^attachment:#(.*)$/.exec(anchor.text());
                if (match) {
                    href += '%23' + match[1];
                }
            }
            var title = anchor.clone();
            title.children('em').contents().appendTo(title);
            title.remove('em');
            title = $('<span/>').append(title, self.clone()).html();
            var options = build_colorbox_options(href, title);
            anchor.attr('data-colorbox-title', title);
            anchor.colorbox(options);
        }
    }

    function timeline() {
        var anchor = $(this);
        var href = anchor.attr('href');
        if (href.indexOf(attachment_url) === 0) {
            var em = anchor.children('em');
            var parent_href = baseurl + href.substring(attachment_url.length)
                                            .replace(/\/[^\/]*$/, '');
            var parent = $('<a/>').attr('href', parent_href)
                                  .text($(em[1]).text());
            var filename = $('<a/>').attr('href', href)
                                    .text($(em[0]).text());
            var rawlink = raw_attachment_url +
                          href.substring(attachment_url.length);
            rawlink = $('<a/>').addClass('overlayview-rawlink')
                               .attr('href', rawlink)
                               .text('\u200b');
            var title = $('<span/>').append(parent, ': ', filename, rawlink)
                                    .html();
            var options = build_colorbox_options(href, title);
            anchor.attr('data-colorbox-title', title);
            anchor.colorbox(options);
        }
    }

    function imageMacro() {
        var options = $.extend({}, basic_options);
        var image = $(this);
        var href = image.attr('src');
        options.href = href;
        options.transition = 'elastic';
        options.initialWidth = this.width;
        options.initialHeight = this.height;
        options.photo = true;
        options.width = false;
        var filename = href.substring(href.lastIndexOf('/') + 1);
        filename = decodeURIComponent(filename);
        var anchor = $('<a />').attr('href', image.parent().attr('href'))
                               .text(filename);
        if (href.substring(0, raw_attachment_url.length)
            === raw_attachment_url)
        {
            anchor.append($('<a/>').addClass('overlayview-rawlink')
                                   .attr('href', href)
                                   .text('\u200b'));
        }
        options.title = $('<span />').append(anchor).html();
        image.attr('data-colorbox-title', options.title);
        image.colorbox(options);
    }

    $('div#content a.trac-rawlink').each(rawlink);
    $('div.timeline#content dt.attachment a').each(timeline);
    $('div#content .searchable a > img')
        .filter(function() {
            return $(this).parent(':not(.trac-rawlink)').length !== 0;
        })
        .each(imageMacro);

    attachments.delegate(
        'div > dl.attachments > dt > a, ul > li > a',
        'click',
        function() {
            var self = $(this);
            if (self.hasClass('trac-rawlink') ||
                self.attr('data-colorbox-title'))
            {
                return;
            }
            var anchor = self.prev('a.trac-rawlink');
            if (anchor.length === 0) {
                anchor = self.next('a.trac-rawlink');
            }
            attachments.find('a.trac-rawlink')
                       .filter(':not([data-colorbox-title])')
                       .each(rawlink);
        });
});
