jQuery(document).ready(function($) {
    function escape_newvalue(value) {
        return value.replace(/\$/g, '$$$$');
    }

    $('textarea.wikitext').textcomplete([
        { // Attachment
            match: /\b((?:raw-)?attachment):(\S*)$/,
            search: function (term, callback) {
                $.getJSON(wikiautocomplete.url + '/attachment',
                          { q: term, realm: wikiautocomplete.realm,
                            id: wikiautocomplete.id })
                    .done(function (resp) { callback(resp); })
                    .fail(function () { callback([]); });
            },
            index: 2,
            replace: function (name) {
                if (/\s/.test(name))
                    name = '"' + name + '"';
                return '$1:' + escape_newvalue(name);
            },
            cache: true
        },

        { // TracLinks
            match: /(^|[^[])\[(\w*)$/,
            search: function (term, callback) {
                $.getJSON(wikiautocomplete.url + '/linkresolvers', { q: term })
                    .done(function (resp) { callback(resp); })
                    .fail(function () { callback([]); });
            },
            index: 2,
            replace: function (resolver) {
                return ['$1[' + escape_newvalue(resolver) + ':', ']'];
            },
            cache: true,
        },

        { // Tickets
            match: /#(\d*)$/,
            search: function (term, callback) {
                $.getJSON(wikiautocomplete.url + '/ticket', { q: term })
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
                $.getJSON(wikiautocomplete.url + '/wikipage', { q: term })
                    .done(function (resp) { callback(resp); })
                    .fail(function () { callback([]); });
            },
            index: 1,
            replace: function (wikipage) {
                return 'wiki:' + escape_newvalue(wikipage);
            },
            cache: true,
        },

        { // Macros
            match: /\[\[(\w*)(?:\(([^)]*))?$/,
            search: function (term, callback) {
                $.getJSON(wikiautocomplete.url + '/macro', { q: term })
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
                $.getJSON(wikiautocomplete.url + '/source', { q: term })
                    .done(function (resp) { callback(resp); })
                    .fail(function () { callback([]); });
            },
            index: 2,
            replace: function (path) {
                return '$1' + escape_newvalue(path);
            },
            cache: true,
        },

    ], {
        appendTo: $('body'),
        maxCount: 10000
    });
});
