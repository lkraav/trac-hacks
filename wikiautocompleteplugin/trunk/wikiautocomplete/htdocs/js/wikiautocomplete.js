jQuery(document).ready(function($) {
    $('textarea.wikitext').textcomplete([
        { // TracLinks
            match: /(^|[^[])\[(\w*)$/,
            search: function (term, callback) {
                $.getJSON(wikiautocomplete_url + '/linkresolvers', { q: term })
                    .done(function (resp) { callback(resp); })
                    .fail(function () { callback([]); });
            },
            index: 2,
            replace: function (resolver) {
                return ['$1[' + resolver + ':', ']'];
            },
            cache: true,
        },

        { // Tickets
            match: /#(\d*)$/,
            search: function (term, callback) {
                $.getJSON(wikiautocomplete_url + '/ticket', { q: term })
                    .done(function (resp) { callback(resp); })
                    .fail(function () { callback([]); });
            },
            index: 1,
            template: function (ticket) {
                return '#' + ticket.id + ' ' + ticket.summary;
            },
            replace: function (ticket) {
                return '#' + ticket.id;
            },
            cache: true,
        },

        { // Wiki pages
            match: /\bwiki:([\w/]*)$/,
            search: function (term, callback) {
                $.getJSON(wikiautocomplete_url + '/wikipage', { q: term })
                    .done(function (resp) { callback(resp); })
                    .fail(function () { callback([]); });
            },
            index: 1,
            replace: function (wikipage) {
                return 'wiki:' + wikipage;
            },
            cache: true,
        },

        { // Macros
            match: /\[\[(\w*)(?:\(([^)]*))?$/,
            search: function (term, callback) {
                $.getJSON(wikiautocomplete_url + '/macro', { q: term })
                    .done(function (resp) { callback(resp); })
                    .fail(function () { callback([]); });
            },
            index: 1,
            template: function (macro) {
                return macro.name + ' ' + macro.description;
            },
            replace: function (macro) {
                return ['[[' + macro.name + '($2',')]]'];
            },
            cache: true,
        },

        { // Source
            match: /\b(source:|log:)([\w/.]*(?:@\w*)?)$/,
            search: function (term, callback) {
                $.getJSON(wikiautocomplete_url + '/source', { q: term })
                    .done(function (resp) { callback(resp); })
                    .fail(function () { callback([]); });
            },
            index: 2,
            replace: function (path) {
                return '$1' + path;
            },
            cache: true,
        },

    ], {
        appendTo: $('body'),
        maxCount: 10000
    });
});
