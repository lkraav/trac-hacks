jQuery(document).ready(function($) {
    if (Array.prototype.forEach === undefined)
        return;

    var cache = {};

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

    function search_cache(strategy, match) {
        return function(term, callback) {
            function invoke_callback(resp) {
                callback($.grep(resp, function(item) {
                    return match(item, term);
                }));
            }
            if (cache[strategy] !== undefined) {
                invoke_callback(cache[strategy]);
                return;
            }
            $.getJSON(wikiautocomplete.url + '/' + strategy)
                .done(function(resp) {
                    cache[strategy] = resp;
                    invoke_callback(resp);
                })
                .fail(function() { callback([]) });
        };
    }

    function search_macro(strategy) {
        return function(term, callback) {
            function invoke_callback(resp) {
                var resp = $.grep(resp, function(item) {
                    return match_string(item.name, term);
                });
                var key = resp.length === 1 ? 'html' : 'oneliner';
                callback($.map(resp, function(item) {
                    switch (item.type) {
                    case 'mimetype':
                        return {type: item.type, name: item.name};
                    case 'macro':
                        return {type: item.type, name: item.name,
                                description: item.description[key],
                                description_type: key};
                    }
                }));
            }
            if (cache[strategy] !== undefined) {
                invoke_callback(cache[strategy]);
            }
            else {
                var data = {
                    realm: wikiautocomplete.realm,
                    id: wikiautocomplete.id
                };
                $.getJSON(wikiautocomplete.url + '/' + strategy, data)
                    .done(function(resp) {
                        cache[strategy] = resp;
                        invoke_callback(resp);
                    })
                    .fail(function() { callback([]) });
            }
        };
    }

    function match_string(string, term) {
        return string.substr(0, term.length) === term;
    }

    function match_report(report, term) {
        return match_string(report.id.toString(), term);
    }

    function context(text) {
        return text.replace(/\{{3}(?:.|\n)*?(?:\}{3}|$)/g, '{{{}}}')
                   .replace(/`[^`\n]*(?:`|$)/gm, '``');
    }

    function template(text, term) {
        return $.htmlEscape(text);
    }

    function template_descr(value, descr, term) {
        var text = $.htmlEscape(value);
        if (descr && value !== descr)
            text += $.htmlFormat(
                '<span class="wikiautocomplete-menu-descr">$1</span>', descr);
        return text;
    }

    function template_report(report, term) {
        return template_descr('{' + report.id + '}', report.title, term);
    }

    var TextareaAdapter = $.fn.textcomplete.Textarea;
    function Adapter(element, completer, option) {
        this.initialize(element, completer, option);
    }
    $.extend(Adapter.prototype, TextareaAdapter.prototype, {
        _skipSearchOrig: TextareaAdapter.prototype._skipSearch,
        _skipSearch: function (clickEvent) {
            if (clickEvent.keyCode === 9)
                return;  // do not skip TAB key
            return this._skipSearchOrig(clickEvent);
        }
    });

    var strategies = [
        { // Processors
            match: /^(\s*\{{3}#!)(.*)(?!\n)$/m,
            search: search_macro('processor'),
            index: 2,
            template: function (processor) {
                var name = $.htmlEscape(processor.name);
                var descr = processor.description;
                if (processor.type === 'mimetype')
                    return name;
                if (!descr)
                    return name;
                var f =
                    processor.description_type === 'html' ? '$1<div>$2</div>' :
                    '$1<span class="wikiautocomplete-menu-descr">$2</span>';
                return $.format(f, name, descr);
            },
            replace: function (processor) {
                return '$1' + escape_newvalue(processor.name);
            },
            cache: true
        },

        { // Attachment
            match: /(\b(?:raw-)?attachment:|\[\[Image\()(\S*)$/,
            search: search('attachment'),
            index: 2,
            context: context,
            template: template,
            replace: function (name) {
                if (/\s/.test(name))
                    name = '"' + name + '"';
                return '$1' + escape_newvalue(name);
            },
            cache: true
        },

        { // TracLinks, InterTrac and InterWiki
            match: /(^|[^[])\[(\w*)$/,
            search: search_cache('linkresolvers', function(resolver, term) {
                return match_string(resolver.name, term);
            }),
            index: 2,
            context: context,
            template: function (resolver, term) {
                var descr = resolver.name !== resolver.title ?
                            resolver.title : resolver.url;
                return template_descr(resolver.name, descr, term);
            },
            replace: function (resolver) {
                return ['$1[' + escape_newvalue(resolver.name) + ':', ']'];
            },
            cache: true,
        },

        { // Tickets
            match: /((?:^|[^{])#|\bticket:|\bbug:|\bissue:)(\d*)$/,
            search: search('ticket'),
            index: 2,
            context: context,
            template: function (ticket, term) {
                return template_descr('#' + ticket.id, ticket.summary);
            },
            replace: function (ticket) {
                return '$1' + ticket.id;
            },
            cache: true,
        },

        { // Wiki pages
            match: /\bwiki:(\S*)$/,
            search: search_cache('wikipage', match_string),
            index: 1,
            context: context,
            template: template,
            replace: function (wikipage) {
                return 'wiki:' + escape_newvalue(wikipage);
            },
            cache: true,
        },

        { // Macros
            match: /\[\[(\w*)(?:\(([^)]*))?$/,
            search: search_macro('macro'),
            index: 1,
            context: context,
            template: function (macro) {
                var name = $.htmlEscape(macro.name);
                var descr = macro.description;
                if (!descr)
                    return name;
                var f =
                    macro.description_type === 'html' ? '$1<div>$2</div>' :
                    '$1<span class="wikiautocomplete-menu-descr">$2</span>';
                return $.format(f, name, descr);
            },
            replace: function (macro) {
                return ['[[' + macro.name + '($2',')]]'];
            },
            cache: true,
        },

        { // Source
            match: /\b(source:|browser:|repos:|log:)([^@\s]*(?:@\S*)?)$/,
            search: search('source'),
            index: 2,
            context: context,
            template: template,
            replace: function (path) {
                return '$1' + escape_newvalue(path);
            },
            cache: true,
        },

        { // Milestone
            match: /\bmilestone:(\S*)$/,
            search: search_cache('milestone', match_string),
            index: 1,
            context: context,
            template: template,
            replace: function (name) {
                if (/\s/.test(name))
                    name = '"' + name + '"';
                return 'milestone:' + escape_newvalue(name);
            },
            cache: true
        },

        { // Report - {\d+}
            match: /(^|[^{])\{(\d*)$/,
            search: search_cache('report', match_report),
            index: 2,
            context: context,
            template: template_report,
            replace: function (report) {
                return ['$1{' + report.id, '}'];
            },
            cache: true
        },

        { // Report - report:\d+
            match: /\breport:(\d*)$/,
            search: search_cache('report', match_report),
            index: 1,
            context: context,
            template: template_report,
            replace: function (report) {
                return 'report:' + report.id;
            },
            cache: true
        }

    ];
    var options = {
        appendTo: $('body'),
        adapter: Adapter,
        maxCount: 10000
    };
    $('textarea.wikitext').textcomplete(strategies, options);
    $('input[type="text"].wikitext').textcomplete(strategies, options);

    if (/^1\.[78]\./.test($.fn.jquery) && $.browser.mozilla &&
        navigator.userAgent.indexOf('like Gecko') === -1 /* is not IE 11 */)
    {
        var margin = $('body').css('margin-top');
        if (margin && margin !== '0px') {
            if (!/px$/.test(margin))
                margin += 'px';
            $('<style type="text/css">.dropdown-menu { margin-top: ' +
              margin + ' !important }</style>').appendTo('head');
        }
    }
});
