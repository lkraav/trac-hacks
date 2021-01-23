(function($){
    $(document).delegate('textarea', 'keydown', function(e) { 
        var keyCode = e.keyCode || e.which;
        if (keyCode != 9 && keyCode != 13) return;

        var textbox = this;
        var all = textbox.value;
        var start = textbox.selectionStart, end = textbox.selectionEnd;

        function startsWith(s, sub) {
            if (typeof String.prototype.startsWith == 'function')  return s.startsWith(sub);
            return s.lastIndexOf(sub, 0) === 0;
        }

        function indentLines(delta) {
            var indent = Array(Math.abs(delta) + 1).join(' ');
            var firstLinePos = Math.max(0, all.lastIndexOf("\n", start - 1) + 1);
            var afterLastLinePos = all.indexOf("\n", end);
            if (afterLastLinePos == -1) afterLastLinePos = all.length;
            
            var newStart = start;
            var lines = all.slice(firstLinePos, afterLastLinePos).split("\n");
            for (var i = 0; i < lines.length; i++) {
                if (delta > 0) {
                    lines[i] = indent + lines[i];
                    if (i == 0) newStart = start + delta;
                }
                if (delta < 0 && startsWith(lines[i], indent)) {
                    lines[i] = lines[i].substring(-delta);
                    if (i == 0) newStart = Math.max(firstLinePos, start + delta);
                }
            }
            textbox.value = all.substring(0, firstLinePos) + lines.join("\n") + all.substring(afterLastLinePos);
            textbox.selectionStart = newStart;
            textbox.selectionEnd = textbox.value.length - (all.length - end);
        };
        
        if (keyCode == 9 && !e.shiftKey) { // TAB
            e.preventDefault();
            indentLines(2);
        }
        if (keyCode == 9 && e.shiftKey) { // SHIFT-TAB
            e.preventDefault();
            indentLines(-2);
        }
        if (keyCode == 13) { // ENTER
            if (start != end) return;

            var firstLinePos = Math.max(0, all.lastIndexOf("\n", start - 1) + 1);
            var afterLastLinePos = all.indexOf("\n", end);
            if (afterLastLinePos == -1) afterLastLinePos = all.length;
            var line = all.slice(firstLinePos, afterLastLinePos);
            
            var match = /^( *(?:[*-]|(?:\d\.)) ).*[^ ].*$/.exec(line);
            if (!match) return;
            if (start < firstLinePos + match[1].length - 1) return;
            e.preventDefault();

            textbox.value = all.substring(0, start) + "\n" + match[1] + all.substring(end);
            textbox.selectionStart = textbox.selectionEnd = start + 1 + match[1].length;
        }

    });
    $(document).delegate('textarea', 'paste', function(e) {

        let text_to_insert = (e.originalEvent.clipboardData || window.clipboardData).getData('text');
       
        const data = textareakeybindings;
        const pattern_re = new RegExp(data.baseurl_pattern);
        text_to_insert = text_to_insert.replace(pattern_re, function(match, realm, rest, offset, string) {
            if (realm == 'wiki' ||
                realm == 'changeset') {
                return realm + ':'+ rest;
            }
            if (realm == 'ticket') {
                if (rest.includes('#comment:')) {
                    const t = rest.split('#comment:');
                    return 'comment:' + t[1] + ':ticket:' + t[0];
                }
                return '#' + rest;
            }
            if (realm == 'browser') {
                const url = new URL(match);
                if (url.searchParams.has('rev')) {
                    const rev = url.searchParams.get('rev');
                    url.searchParams.delete('rev');
                    url.pathname = url.pathname + '@' + rev;
                }
                if (url.searchParams.has('marks')) {
                    const marks = url.searchParams.get('marks');
                    url.searchParams.delete('marks');
                    url.pathname = url.pathname + ':' + marks;
                }
                return 'source:' + url.href.replace(pattern_re, '$2')
            }
            if (realm == 'log') {
                const url = new URL(match);
                if (url.searchParams.has('rev')) {
                    const rev = url.searchParams.get('rev');
                    url.searchParams.delete('rev');
                    url.pathname = url.pathname + '@' + rev;
                }
                return 'log:' + url.href.replace(pattern_re, '$2')
            }
            if (realm == 'attachment') {
                return realm + ':'+ rest.replace('/', ':').replace(/\/([^/]*)$/, ':$1');
            }
            return match;
        });

        data.links.forEach(key_and_url_re => {
            const key = key_and_url_re[0];
            const url_re = key_and_url_re[1];
            text_to_insert = text_to_insert.replaceAll(new RegExp(url_re, 'g'), key);
        });

        const start = e.target.selectionStart;
        e.target.value = e.target.value.slice(0, start) + text_to_insert + e.target.value.slice(e.target.selectionEnd);
        e.target.selectionStart = start + text_to_insert.length;
        e.target.selectionEnd = start + text_to_insert.length;
        event.preventDefault();
    });
 })(jQuery);
