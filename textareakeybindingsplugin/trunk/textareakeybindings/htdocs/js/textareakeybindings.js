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
            if (start != afterLastLinePos) return;
            
            var match = /^( *[*-] ).*[^ ].*$/.exec(line);
            if (!match) return;
            e.preventDefault();

            textbox.value = all.substring(0, start) + "\n" + match[1] + all.substring(end);
            textbox.selectionStart = textbox.selectionEnd = start + 1 + match[1].length;
        }

    });
 })(jQuery);
