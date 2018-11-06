jQuery(document).ready(function($) {
    if (Array.prototype.forEach === undefined)
        return;

    var cache = {};

    function escape_newvalue(value) {
        return value.replace(/\$/g, '$$$$');
    }

    function context(text) {
        return text.replace(/\{{3}(?:.|\n)*?(?:\}{3}|$)/g, '{{{}}}')
                   .replace(/`[^`\n]*(?:`|$)/gm, '``');
    }

    function search(strategy) {
        if (strategy.cache) {
            return function(term, callback) {
                function invoke_callback(resp) {
                    var matches = $.grep(resp, function(item) {
                        return item.value.toString().substr(0, term.length) === term;
                    });
                    if (matches.length === 1) {
                        matches[0].single_match = true;
                    }
                    callback(matches);
                }
                if (cache[strategy.name] !== undefined) {
                    invoke_callback(cache[strategy.name]);
                    return;
                }
                var data = {
                    realm: wikiautocomplete.realm,
                    id: wikiautocomplete.id
                };
                $.getJSON(wikiautocomplete.url + '/' + strategy.name, data)
                    .done(function(resp) {
                        cache[strategy] = resp;
                        invoke_callback(resp);
                    })
                    .fail(function() { callback([]) });
            };
        } else {
            return function (term, callback) {
                var data = {
                    q: term,
                    realm: wikiautocomplete.realm,
                    id: wikiautocomplete.id
                };
                $.getJSON(wikiautocomplete.url + '/' + strategy.name, data)
                    .done(function (resp) { callback(resp); })
                    .fail(function () { callback([]); });
            };
        }
    }

    function template(strategy) {
        var prefix = strategy.template_prefix || '';
        var suffix = strategy.template_suffix || '';
        return function (item) {
            var fmt = '<span class="wikiautocomplete-menu-descr">$1</span>';
            var value = prefix + item.value + suffix;
            var text = $.htmlEscape(value);
            if (item.single_match && item.details_html) {
                text += $.format('<div>$1</div>', item.details_html);
            }
            else if (item.title_html) {
                text += $.format(fmt, item.title_html);
            }
            else if (item.title && item.title !== value) {
                text += $.htmlFormat(fmt, item.title);
            }
            return text;
        };
    }

    function replace(strategy) {
        var prefix = strategy.replace_prefix || '';
        var suffix = strategy.replace_suffix || '';
        var end = strategy.replace_end;
        var quote = strategy.quote_whitespace;
        return function (item) {
            var value = item.value.toString();
            if (quote && /\s/.test(value))
                value = '"' + value + '"';
            value = escape_newvalue(value);
            value = prefix + value + suffix;
            if (end) return [value, end]; 
            else return value;
        };
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

    var strategies = wikiautocomplete.strategies.map(function (strategy) {
        var result = {
            match: new RegExp(strategy.match, strategy.match_flags),
            search: search(strategy),
            index: strategy.index,
            template: template(strategy),
            replace: replace(strategy),
            cache: true
        };
        if (strategy.name != 'processor') result.context = context;
        return result;
    });
    var options = {
        appendTo: $('body'),
        adapter: Adapter,
        maxCount: 10000
    };
    $('textarea.wikitext').attr("autocomplete", "off").textcomplete(strategies, options);
    $('input[type="text"].wikitext').attr("autocomplete", "off").textcomplete(strategies, options);

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
