jQuery(document).ready(function($) {
    function escape_newvalue(value) {
        return value.replace(/\$/g, '$$$$');
    }

    function search(strategy) {
        return function (term, callback) {
            var data = {q: term};
            if (strategy === 'attachment') {
                data.realm = wikiautocomplete.realm;
                data.id = wikiautocomplete.id;
            }
            $.getJSON(wikiautocomplete.url + '/' + strategy, data)
                .done(function (resp) { callback(resp); })
                .fail(function () { callback([]); });
        };
    }

    $('textarea.wikitext').textcomplete([
        { // Attachment
            match: /\b((?:raw-)?attachment):(\S*)$/,
            search: search('attachment'),
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
            search: search('linkresolvers'),
            index: 2,
            replace: function (resolver) {
                return ['$1[' + escape_newvalue(resolver) + ':', ']'];
            },
            cache: true,
        },

        { // Tickets
            match: /(#|\bticket:)(\d*)$/,
            search: search('ticket'),
            index: 2,
            template: function (ticket) {
                return '#' + ticket.id + ' ' + ticket.summary;
            },
            replace: function (ticket) {
                return '$1' + ticket.id;
            },
            cache: true,
        },

        { // Wiki pages
            match: /\bwiki:([\w/]*)$/,
            search: search('wikipage'),
            index: 1,
            replace: function (wikipage) {
                return 'wiki:' + escape_newvalue(wikipage);
            },
            cache: true,
        },

        { // Macros
            match: /\[\[(\w*)(?:\(([^)]*))?$/,
            search: search('macro'),
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
            search: search('source'),
            index: 2,
            replace: function (path) {
                return '$1' + escape_newvalue(path);
            },
            cache: true,
        },

        { // Milestone
            match: /\bmilestone:(\S*)$/,
            search: search('milestone'),
            index: 1,
            replace: function (name) {
                if (/\s/.test(name))
                    name = '"' + name + '"';
                return 'milestone:' + escape_newvalue(name);
            },
            cache: true
        },

        { // Report - {\d+}
            match: /(^|[^{])\{(\d*)$/,
            search: search('report'),
            index: 2,
            template: function (report) {
                return '{' + report.id + '} ' + report.title;
            },
            replace: function (report) {
                return ['$1{' + report.id, '}'];
            },
            cache: true
        },

        { // Report - report:\d+
            match: /\breport:(\d*)$/,
            search: search('report'),
            index: 1,
            template: function (report) {
                return '{' + report.id + '} ' + report.title;
            },
            replace: function (report) {
                return 'report:' + report.id;
            },
            cache: true
        }

    ], {
        appendTo: $('body'),
        maxCount: 10000
    });
});
