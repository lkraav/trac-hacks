var TracWysiwyg = function(textarea) {
    var self = this;
    var editorMode = TracWysiwyg.getEditorMode();

    this.textarea = textarea;
    this.wikitextToolbar = textarea.previousSibling;

    var anonymous = document.createElement("div");
    anonymous.innerHTML = '<iframe class="wysiwyg" '
        + 'width="100%" height="' + textarea.offsetHeight + '" '
        + 'frameborder="0" marginwidth="0" marginheight="0">'
        + '</iframe>';
    var frame = anonymous.firstChild;
    textarea.parentNode.insertBefore(frame, textarea.nextSibling);

    this.frame = frame;
    this.contentWindow = frame.contentWindow;
    this.contentDocument = this.contentWindow.document;

    this.initializeEditor(this.contentDocument);
    this.wysiwygToolbar = this.createWysiwygToolbar(document);
    this.styleMenu = this.createStyleMenu(document);
    this.decorationMenu = this.createDecorationMenu(document);
    this.tableMenu = this.createTableMenu(document);
    this.menus = [ this.styleMenu, this.decorationMenu, this.tableMenu ];
    this.toolbarButtons = this.setupMenuEvents();
    this.savedWysiwygHTML = null;

    frame.parentNode.insertBefore(this.wysiwygToolbar, frame);
    var body = document.body;
    for (var i = 0; i < this.menus.length; i++) {
        body.insertBefore(this.menus[i], body.firstChild);
    }

    switch (editorMode) {
    case "textarea":
        frame.style.display = this.wysiwygToolbar.style.display = "none";
        break;
    case "wysiwyg":
        textarea.style.display = this.wikitextToolbar.style.display = "none";
        break;
    }
    this.setupToggleEditorButtons();

    function lazySetup() {
        if (self.contentDocument.body) {
            try { self.execCommand("useCSS", false); } catch (e) { }
            try { self.execCommand("styleWithCSS", false); } catch (e) { }
            if (editorMode == "wysiwyg") {
                self.loadWysiwygDocument();
            }
            self.setupEditorEvents();
            self.setupFormEvent();
        }
        else {
            setTimeout(lazySetup, 100);
        }
    }
    lazySetup();
};

TracWysiwyg.prototype.initializeEditor = function(d) {
    var l = window.location;
    var css = {};
    css.trac = TracWysiwyg.tracBasePath + "chrome/common/css/trac.css";
    css.editor = TracWysiwyg.tracBasePath + "chrome/tracwysiwyg/editor.css";
    var html = [
        '<!DOCTYPE html PUBLIC',
        ' "-//W3C//DTD XHTML 1.0 Transitional//EN"',
        ' "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">\n',
        '<html xmlns="http://www.w3.org/1999/xhtml" xmlns:tw="http://trac-hacks.org/wiki/TracWysiwygPlugin">',
        '<head>',
        '<base href="', l.protocol, '//', l.host, '/" />',
        '<meta http-equiv="Content-Type" content="text/html; charset=utf-8" />',
        '<link rel="stylesheet" href="' + css.trac + '" type="text/css" />',
        '<link rel="stylesheet" href="' + css.editor + '" type="text/css" />',
        '<title></title>',
        '</head>',
        '<body></body>',
        '</html>' ];

    d.designMode = "On";
    d.open();
    d.write(html.join(""));
    d.close();
};

TracWysiwyg.prototype.listenerToggleEditor = function(type) {
    var self = this;

    switch (type) {
    case "textarea":
        return function(event) {
            if (self.textarea.style.display == "none") {
                self.textarea.style.display = self.wikitextToolbar.style.display = "";
                self.frame.style.display = self.wysiwygToolbar.style.display = "none";
                self.loadTracWikiText();
                TracWysiwyg.setEditorMode(type);
            }
            self.focusTextarea();
        };
    case "wysiwyg":
        return function(event) {
            if (self.frame.style.display == "none") {
                self.textarea.style.display = self.wikitextToolbar.style.display = "none";
                self.frame.style.display = self.wysiwygToolbar.style.display = "";
                self.loadWysiwygDocument();
                TracWysiwyg.setEditorMode(type);
            }
            self.focusWysiwyg();
        };
    }
};

TracWysiwyg.prototype.setupFormEvent = function() {
    var self = this;

    function listener(event) {
        var textarea = self.textarea;
        try {
            if (textarea.style.display == "none") {
                var body = self.contentDocument.body;
                if (self.savedWysiwygHTML !== null && body.innerHTML != self.savedWysiwygHTML) {
                    textarea.value = self.domToWikitext(body);
                }
            }
        }
        catch (e) {
            TracWysiwyg.stopEvent(event || window.event);
        }
    }
    addEvent(this.textarea.form, "submit", listener);
};

TracWysiwyg.prototype.createWysiwygToolbar = function(d) {
    var html = [
        '<ul>',
        '<li title="Style"><a id="wt-style" href="#">Style</a></li>',
        '<li title="Bold (Ctrl+B)"><a id="wt-strong" href="#"></a></li>',
        '<li title="Italic (Ctrl+I)"><a id="wt-em" href="#"></a></li>',
        '<li title="Underline (Ctrl+U)"><a id="wt-underline" href="#"></a></li>',
        '<li title="Monospace"><a id="wt-monospace" href="#"></a></li>',
        '<li><a id="wt-decorationmenu" href="#"></a></li>',
        '<li title="Remove format"><a id="wt-remove" href="#"></a></li>',
        '<li title="Link"><a id="wt-link" href="#"></a></li>',
        '<li title="Unlink"><a id="wt-unlink" href="#"></a></li>',
        '<li title="Ordered list"><a id="wt-ol" href="#"></a></li>',
        '<li title="List"><a id="wt-ul" href="#"></a></li>',
        '<li title="Outdent"><a id="wt-outdent" href="#"></a></li>',
        '<li title="Indent"><a id="wt-indent" href="#"></a></li>',
        '<li title="Table"><a id="wt-table" href="#"></a></li>',
        '<li><a id="wt-tablemenu" href="#"></a></li>',
        '<li title="Horizontal rule"><a id="wt-hr" href="#"></a></li>',
        '<li title="Line break (Shift+Enter)"><a id="wt-br" href="#"></a></li>',
        '</ul>' ];
    var div = d.createElement("div");
    div.className = "wysiwyg-toolbar";
    div.innerHTML = html.join("");

    return div;
};

TracWysiwyg.prototype.createStyleMenu = function(d) {
    var html = [
        '<p><a id="wt-paragraph" href="#">Normal</a></p>',
        '<h1><a id="wt-heading1" href="#">Header 1</a></h1>',
        '<h2><a id="wt-heading2" href="#">Header 2</a></h2>',
        '<h3><a id="wt-heading3" href="#">Header 3</a></h3>',
        '<h4><a id="wt-heading4" href="#">Header 4</a></h4>',
        '<h5><a id="wt-heading5" href="#">Header 5</a></h5>',
        '<h6><a id="wt-heading6" href="#">Header 6</a></h6>',
        '<pre class="wiki"><a id="wt-code" href="#">Code block</a></pre>',
        '<blockquote class="citation"><a id="wt-quote" href="#">Quote</a></blockquote>' ].join("");
    var menu = d.createElement("div");
    menu.className = "wysiwyg-menu";
    var style = menu.style;
    style.top = style.left = "-1000px";
    style.position = "absolute";
    style.zIndex = 1000;
    menu.innerHTML = html;
    return menu;
};

TracWysiwyg.prototype.createDecorationMenu = function(d) {
    var html = [
        '<ul class="menu">',
        '<li><a id="wt-strike" href="#">Strike</a></li>',
        '<li><a id="wt-sup" href="#">Superscript</a></li>',
        '<li><a id="wt-sub" href="#">Subscript</a></li>',
        '</ul>' ].join("");
    var menu = d.createElement("div");
    menu.className = "wysiwyg-menu";
    var style = menu.style;
    style.top = style.left = "-1000px";
    style.position = "absolute";
    style.zIndex = 1000;
    menu.innerHTML = html;
    return menu;
};

TracWysiwyg.prototype.createTableMenu = function(d) {
    var html = [
        '<ul class="menu">',
        '<li><a id="wt-insert-row-before" href="#">Insert row before</a></li>',
        '<li><a id="wt-insert-row-after" href="#">Insert row after</a></li>',
        '<li><a id="wt-insert-col-before" href="#">Insert column before</a></li>',
        '<li><a id="wt-insert-col-after" href="#">Insert column after</a></li>',
        '<li><a id="wt-delete-row" href="#">Delete row</a></li>',
        '<li><a id="wt-delete-col" href="#">Delete column</a></li>',
        '</ul>' ].join("");
    var menu = d.createElement("div");
    menu.className = "wysiwyg-menu";
    var style = menu.style;
    style.top = style.left = "-1000px";
    style.position = "absolute";
    style.zIndex = 1000;
    menu.innerHTML = html;
    return menu;
};

TracWysiwyg.prototype.setupMenuEvents = function() {
    function addToolbarEvent(element, self, args) {
        var method = args.shift();
        addEvent(element, "click", function(event) {
            var w = self.contentWindow;
            TracWysiwyg.stopEvent(event || w.event);
            var keepMenus = false;
            try { keepMenus = method.apply(self, args) } catch (e) { }
            if (!keepMenus) {
                self.hideAllMenus();
            }
            element.blur();
            w.focus();
        });
    }

    function argsByType(self, name, element) {
        switch (name) {
        case "style":       return [ self.toggleMenu, self.styleMenu, element ];
        case "strong":      return [ self.execDecorate, "bold" ];
        case "em":          return [ self.execDecorate, "italic" ];
        case "underline":   return [ self.execDecorate, "underline" ];
        case "strike":      return [ self.execDecorate, "strikethrough" ];
        case "sub":         return [ self.execDecorate, "subscript" ];
        case "sup":         return [ self.execDecorate, "superscript" ];
        case "monospace":   return [ self.execDecorate, "monospace" ];
        case "decorationmenu":  return [ self.toggleMenu, self.decorationMenu, element ];
        case "remove":      return [ self.execCommand, "removeformat" ];
        case "paragraph":   return [ self.formatParagraph ];
        case "heading1":    return [ self.formatHeaderBlock, "h1" ];
        case "heading2":    return [ self.formatHeaderBlock, "h2" ];
        case "heading3":    return [ self.formatHeaderBlock, "h3" ];
        case "heading4":    return [ self.formatHeaderBlock, "h4" ];
        case "heading5":    return [ self.formatHeaderBlock, "h5" ];
        case "heading6":    return [ self.formatHeaderBlock, "h6" ];
        case "link":        return [ self.createLink ];
        case "unlink":      return [ self.execCommand, "unlink" ];
        case "ol":          return [ self.insertOrderedList ];
        case "ul":          return [ self.insertUnorderedList ];
        case "outdent":     return [ self.outdent ];
        case "indent":      return [ self.indent ];
        case "table":       return [ self.insertTable ];
        case "tablemenu":   return [ self.toggleMenu, self.tableMenu, element ];
        case "insert-row-before":   return [ self.insertTableRow, false ];
        case "insert-row-after":    return [ self.insertTableRow, true ];
        case "insert-col-before":   return [ self.insertTableColumn, false ];
        case "insert-col-after":    return [ self.insertTableColumn, true ];
        case "delete-row":  return [ self.deleteTableRow ];
        case "delete-col":  return [ self.deleteTableColumn ];
        case "code":        return [ self.formatCodeBlock ];
        case "quote":       return [ self.formatQuoteBlock ];
        case "hr":          return [ self.insertHorizontalRule ];
        case "br":          return [ self.insertHTML, "<br />" ];
        }
        return null;
    }

    function setup(container) {
        var elements = container.getElementsByTagName("a");
        var length = elements.length;
        for (var i = 0; i < length; i++) {
            var element = elements[i];
            var name = element.id.replace(/^wt-/, "");
            var args = argsByType(this, name, element);
            if (args) {
                addToolbarEvent(element, this, args);
                buttons[name] = element;
            }
        }
    }

    var buttons = {};
    setup.call(this, this.wysiwygToolbar);
    for (var i = 0; i < this.menus.length; i++) {
        setup.call(this, this.menus[i]);
    }
    return buttons;
};

TracWysiwyg.prototype.toggleMenu = function(menu, element) {
    var style = menu.style;
    if (parseInt(style.left, 10) < 0) {
        this.hideAllMenus(menu);
        var position = TracWysiwyg.elementPosition(element);
        style.left = position[0] + "px";
        style.top = (position[1] + 18 /* XXX */) + "px";
    }
    else {
        this.hideAllMenus();
    }
    return true;
};

TracWysiwyg.prototype.hideAllMenus = function(except) {
    var menus = this.menus;
    var length = menus.length;
    for (var i = 0; i < length; i++) {
        if (menus[i] != except) {
            var style = menus[i].style;
            style.left = style.top = "-1000px";
        }
    }
};

TracWysiwyg.prototype.execDecorate = function(name) {
    if (this.selectionContainsTagName("pre")) {
        return;
    }
    var getSelfOrAncestor = TracWysiwyg.getSelfOrAncestor;
    var position = this.getSelectionPosition();
    var ancestor = {};
    ancestor.start = getSelfOrAncestor(position.start, "a") || getSelfOrAncestor(position.start, "tt");
    ancestor.end = getSelfOrAncestor(position.end, "a") || getSelfOrAncestor(position.end, "tt");
    this.expandSelectionToElement(ancestor);

    if (name != "monospace") {
        this.execCommand(name);
    }
    else {
        this.execDecorateMonospace();
    }
    this.selectionChanged();
};

TracWysiwyg.prototype.execDecorateMonospace = function() {
    var html = this.getSelectionHTML();
    var removePattern = /<tt.*?>|<\/tt>/gi;
    if (/^<tt.*?>/i.test(html) && /<\/tt>$/i.test(html)) {
        html = html.replace(removePattern, "");
    }
    else {
        var id = this.generateDomId();
        html = '<tt id="' + id + '">' + html.replace(removePattern, "") + "</tt>";
    }
    this.insertHTML(html);
    var node = this.contentDocument.getElementById(id);
    if (node) {
        this.selectNode(node);
    }
};

TracWysiwyg.prototype.execCommand = function(name, arg) {
    this.contentDocument.execCommand(name, false, arg);
};

TracWysiwyg.prototype.setupEditorEvents = function() {
    var self = this;
    var d = this.contentDocument;

    function listenerKeydown(event) {
        var method = null;
        var args = null;
        event = event || self.contentWindow.event;
        if (event.ctrlKey && !event.shiftKey && !event.altKey) {
            switch (event.keyCode) {
            case 0x42:  // C-b
                method = self.execDecorate;
                args = [ "bold" ];
                break;
            case 0x49:  // C-i
                method = self.execDecorate;
                args = [ "italic" ];
                break;
            case 0x55:  // C-u
                method = self.execDecorate;
                args = [ "underline" ];
                break;
            }
        }
        if (method !== null) {
            TracWysiwyg.stopEvent(event);
            method.apply(self, args);
            self.selectionChanged();
        }
    }
    addEvent(d, window.opera ? "keypress" : "keydown", listenerKeydown);

    function listenerKeyup(event) {
        self.selectionChanged();
    }
    addEvent(d, "keyup", listenerKeyup);

    function listenerMouseup(event) {
        self.selectionChanged();
    }
    addEvent(d, "mouseup", listenerMouseup);

    function listenerClick(event) {
        self.hideAllMenus();
        self.selectionChanged();
    }
    addEvent(d, "click", listenerClick);
};

TracWysiwyg.prototype.loadWysiwygDocument = function() {
    var d = this.contentDocument;
    var container = d.body;
    var tmp;

    while (tmp = container.lastChild) {
        container.removeChild(tmp);
    }
    var fragment = this.wikitextToFragment(this.textarea.value, d);
    if (fragment.childNodes.length == 0) {
        var paragraph = d.createElement("p");
        if (paragraph.addEventListener) {
            paragraph.appendChild(d.createElement("br"));
        }
        fragment.appendChild(paragraph);
    }
    container.appendChild(fragment);
    this.savedWysiwygHTML = container.innerHTML;
};

TracWysiwyg.prototype.focusWysiwyg = function() {
    var self = this;
    var w = this.contentWindow;
    function lazy() {
        w.focus();
        try { self.execCommand("useCSS", false); } catch (e) { }
        try { self.execCommand("styleWithCSS", false); } catch (e) { }
        self.selectionChanged();
    }
    setTimeout(lazy, 10);
};

TracWysiwyg.prototype.loadTracWikiText = function() {
    this.textarea.value = this.domToWikitext(this.contentDocument.body);
    this.savedWysiwygHTML = null;
};

TracWysiwyg.prototype.focusTextarea = function() {
    this.textarea.focus();
};

TracWysiwyg.prototype.setupToggleEditorButtons = function() {
    var toggle = document.createElement("div");
    var mode = TracWysiwyg.editorMode;
    var html = ''
        + '<label for="editor-wysiwyg-@">'
        + '<input type="radio" name="__EDITOR__@" value="wysiwyg" id="editor-wysiwyg-@" '
        + (mode == "wysiwyg" ? 'checked="checked"' : '') + ' />'
        + 'wysiwyg</label> '
        + '<label for="editor-textarea-@">'
        + '<input type="radio" name="__EDITOR__@" value="textarea" id="editor-textarea-@" '
        + (mode == "textarea" ? 'checked="checked"' : '') + ' />'
        + 'textarea</label> '
        + '&nbsp; ';
    toggle.className = "editor-toggle";
    toggle.innerHTML = html.replace(/@/g, ++TracWysiwyg.count);

    var buttons = toggle.getElementsByTagName("input");
    for (var i = 0; i < buttons.length; i++) {
        var button = buttons[i];
        addEvent(button, "click", this.listenerToggleEditor(button.value));
    }
    var wikitextToolbar = this.wikitextToolbar;
    wikitextToolbar.parentNode.insertBefore(toggle, wikitextToolbar);
};

TracWysiwyg.prototype.formatParagraph = function() {
    if (this.selectionContainsTagName("table")) {
        return;
    }
    this.execCommand("formatblock", "<p>");
    this.selectionChanged();
};

TracWysiwyg.prototype.formatHeaderBlock = function(name) {
    if (this.selectionContainsTagName("table")) {
        return;
    }
    this.execCommand("formatblock", "<" + name + ">");
    this.selectionChanged();
};

TracWysiwyg.prototype.insertOrderedList = function() {
    if (this.selectionContainsTagName("table") || this.selectionContainsTagName("pre")) {
        return;
    }
    this.execCommand("insertorderedlist");
    this.selectionChanged();
};

TracWysiwyg.prototype.insertUnorderedList = function() {
    if (this.selectionContainsTagName("table") || this.selectionContainsTagName("pre")) {
        return;
    }
    this.execCommand("insertunorderedlist");
    this.selectionChanged();
};

TracWysiwyg.prototype.outdent = function() {
    if (this.selectionContainsTagName("table") || this.selectionContainsTagName("pre")) {
        return;
    }
    this.execCommand("outdent");
};

TracWysiwyg.prototype.indent = function() {
    if (this.selectionContainsTagName("table") || this.selectionContainsTagName("pre")) {
        return;
    }
    this.execCommand("indent");
};

TracWysiwyg.prototype.insertTable = function() {
    if (this.selectionContainsTagName("table") || this.selectionContainsTagName("pre")) {
        return;
    }
    var id = this.generateDomId();
    var html = [
        '<table class="wiki">',
        '<tbody>',
        '<tr><td id="' + id + '"></td><td></td><td></td></tr>',
        '<tr><td></td><td></td><td></td></tr>',
        '</tbody>',
        '</table>' ];
    this.insertHTML(html.join(""));
    var element = this.contentDocument.getElementById(id)
    if (element) {
        this.selectNodeContents(element);
    }
    this.selectionChanged();
};

TracWysiwyg.prototype._getFocusForTable = function() {
    var hash = { node: null, cell: null, row: null, table: null };
    hash.node = this.getFocusNode();
    hash.cell = hash.node
        ? TracWysiwyg.getSelfOrAncestor(hash.node, "td") || TracWysiwyg.getSelfOrAncestor(hash.node, "th")
        : null;
    hash.row = hash.cell ? TracWysiwyg.getSelfOrAncestor(hash.cell, "tr") : null;
    hash.table = hash.row ? TracWysiwyg.getSelfOrAncestor(hash.row, "table") : null;
    return hash;
};

TracWysiwyg.prototype.insertTableRow = function(after) {
    var focus = this._getFocusForTable();
    if (focus.table && focus.row) {
        var d = this.contentDocument;
        var cells = focus.row.getElementsByTagName("td");
        var row = focus.table.insertRow(focus.row.rowIndex + (after ? 1 : 0));
        for (var j = 0; j < cells.length; j++) {
            this.insertTableCell(row, 0);
        }
    }
};

TracWysiwyg.prototype.insertTableColumn = function(after) {
    var focus = this._getFocusForTable();
    if (focus.table && focus.cell) {
        var d = this.contentDocument;
        var rows = focus.table.rows;
        var length = rows.length;
        var cellIndex = focus.cell.cellIndex + (after ? 1 : 0);
        for (var i = 0; i < length; i++) {
            var row = rows[i];
            this.insertTableCell(row, Math.min(cellIndex, row.cells.length));
        }
    }
};

TracWysiwyg.prototype.deleteTableRow = function() {
    var focus = this._getFocusForTable();
    if (focus.table && focus.row) {
        focus.table.deleteRow(focus.row.rowIndex);
    }
};

TracWysiwyg.prototype.deleteTableColumn = function() {
    var focus = this._getFocusForTable();
    if (focus.table && focus.cell) {
        var rows = focus.table.rows;
        var length = rows.length;
        var cellIndex = focus.cell.cellIndex;
        for (var i = 0; i < length; i++) {
            var row = rows[i];
            if (cellIndex < row.cells.length) {
                row.deleteCell(cellIndex);
            }
        }
    }
};

TracWysiwyg.prototype.formatCodeBlock = function() {
    if (this.selectionContainsTagName("table") || this.selectionContainsTagName("pre")) {
        return;
    }
    var text = this.getSelectionText();
    if (!text) {
        var node = this.getFocusNode();
        while (node.nodeType == 3) {
            node = node.parentNode;
        }
        text = TracWysiwyg.getTextContent(node);
        this.selectNode(node);
    }

    var fragment = this.getSelectionFragment();
    text = this.domToWikitext(fragment).replace(/\s+$/, "");

    var d = this.contentDocument;
    var anonymous = d.createElement("div");
    var pre = d.createElement("pre");
    pre.className = "wiki";
    anonymous.appendChild(pre);
    if (text) {
        pre.appendChild(d.createTextNode(text));
    }

    this.insertHTML(anonymous.innerHTML);
    this.selectionChanged();
};

TracWysiwyg.prototype.formatQuoteBlock = function() {
    if (this.selectionContainsTagName("table") || this.selectionContainsTagName("pre")) {
        return;
    }
    var d = this.contentDocument;
    var anonymous = d.createElement("div");

    var container = d.createElement("blockquote");
    container.className = "citation";
    var fragment = this.getSelectionFragment();
    var childNodes = fragment.childNodes;
    for (var i = childNodes.length - 1; i >= 0; i--) {
        var child = childNodes[i];
        var text = null;
        switch (child.nodeType) {
        case 1:
            if (child.tagName.toLowerCase() != "blockquote" || child.className != "citation") {
                text = TracWysiwyg.getTextContent(child);
            }
            break;
        case 3:
            text = child.nodeValue;
            break;
        default:
            continue;
        }
        if (text !== null) {
            if (!text) {
                continue;
            }
            var tmp = d.createElement("p");
            tmp.appendChild(d.createTextNode(text));
            child = tmp;
        }
        container.insertBefore(child, container.firstChild);
    }
    if (container.childNodes.length == 0) {
        container.appendChild(d.createElement("p"));
    }
    anonymous.appendChild(container);

    this.insertHTML(anonymous.innerHTML);
    this.selectionChanged();
};

TracWysiwyg.prototype.insertHorizontalRule = function() {
    if (this.selectionContainsTagName("table") || this.selectionContainsTagName("pre")) {
        return;
    }
    this.execCommand("inserthorizontalrule");
    this.selectionChanged();
};

TracWysiwyg.prototype.createLink = function() {
    if (this.selectionContainsTagName("pre")) {
        return;
    }

    var focus = this.getFocusNode();
    var anchor = TracWysiwyg.getSelfOrAncestor(focus, "a");
    var expand = anchor || TracWysiwyg.getSelfOrAncestor(focus, "tt");
    var currLink = anchor ? (anchor.getAttribute("tw:link") || anchor.href) : "";
    if (expand) {
        this.selectNodeContents(expand);
    }
    var text = this.getSelectionText() || "";
    var newLink = (prompt(text ? "Enter TracLink:" : "Insert TracLink:", currLink) || "").replace(/^\s+|\s+$/g, "");
    if (newLink && newLink != currLink) {
        text = text || newLink;
        newLink = this.normalizeTracLink(newLink);
        var id = this.generateDomId();
        var d = this.contentDocument;
        var anonymous = d.createElement("div");
        anchor = d.createElement("a");
        anchor.id = id;
        anchor.href = TracWysiwyg.quickSearchURL(newLink);
        anchor.title = newLink;
        anchor.setAttribute("tw:link", newLink);
        anchor.appendChild(d.createTextNode(text));
        anonymous.appendChild(anchor);
        this.insertHTML(anonymous.innerHTML);
        anchor = d.getElementById(id);
        if (anchor) {
            this.selectNodeContents(anchor);
        }
    }
    this.selectionChanged();
};

TracWysiwyg.prototype.collectChildNodes = function(dest, source) {
    var childNodes = source.childNodes;
    for (var i = childNodes.length - 1; i >= 0; i--) {
        dest.insertBefore(childNodes[i], dest.firstChild);
    }
};

TracWysiwyg.prototype.generateDomId = function() {
    var d = this.contentDocument;
    for ( ; ; ) {
        var id = "tmp-" + (new Date().valueOf().toString(36));
        if (!d.getElementById(id)) {
            return id;
        }
    }
};

TracWysiwyg.prototype.selectionChanged = function() {
    var status = {
        strong: false, em: false, underline: false, strike: false, sub: false,
        sup: false, monospace: false, paragraph: false, heading1: false,
        heading2: false, heading3: false, heading4: false, heading5: false,
        heading6: false, link: false, ol: false, ul: false, outdent: false,
        indent: false, table: false, code: false, quote: false, hr: false,
        br: false };
    var tagNameToKey = {
        b: "strong", i: "em", u: "underline", del: "strike", tt: "monospace",
        p: "paragraph", h1: "heading1", h2: "heading2", h3: "heading3",
        h4: "heading4", h5: "heading5", h6: "heading6", a: "link", pre: "code",
        blockquote: "quote" };
    var position = this.getSelectionPosition();

    var node = position.start == position.end ? position.start.firstChild : position.start.nextSibling;
    node = node || position.start;
    while (node) {
        if (node.nodeType == 1) {
            var name = node.tagName.toLowerCase();
            if (name in tagNameToKey) {
                name = tagNameToKey[name];
            }
            status[name] = true;
        }
        node = node.parentNode;
    }

    var toolbarButtons = this.toolbarButtons;
    for (var name in status) {
        var button = toolbarButtons[name];
        if (button) {
            var parent = button.parentNode;
            parent.className = (parent.className || "").replace(/ *\bselected\b|$/, status[name] ? " selected" : "");
        }
    }

    var styles = [ "quote", "paragraph", "code", "heading1",
        "heading2", "heading3", "heading4", "heading5", "heading6" ];
    var styleButton = toolbarButtons["style"];
    var styleButtonText = "Style";
    for (var i = 0; i < styles.length; i++) {
        if (status[styles[i]]) {
            styleButtonText = TracWysiwyg.getTextContent(toolbarButtons[styles[i]]);
            break;
        }
    }
    if (TracWysiwyg.getTextContent(styleButton) != styleButtonText) {
        styleButton.replaceChild(document.createTextNode(styleButtonText), styleButton.firstChild);
    }
};

(function() {
    var _linkScheme = "[\\w.+-]+";
    var _quotedString = "'[^']+'|" + '"[^"]+"';
    var _citation = "^(?: *>)+";
    var _changesetId = "(?:\\d+|[a-fA-F\\d]{6,})";
    var _ticketLink = "#\\d+";
    var _reportLink = "\\{\\d+\\}";
    var _changesetPath = "/[^\\]]*";
    var _tracLink = _linkScheme + ":(?:" + _quotedString
        + "|[a-zA-Z0-9/?!#@](?:(?:\\|(?=[^| \\t\\r\\f\\v])|[^|<> \\t\\r\\f\\v])*[a-zA-Z0-9/=])?)";
    var _wikiPageName = "[A-Z][a-z]+(?:[A-Z][a-z]*[a-z/])+(?:#[\\w:][-\\w\\d.:]*)?"
        + "(?=:(?:$|[ \\t\\r\\f\\v])|[^:a-zA-Z]|[ \\t\\r\\f\\v]|$)";
    var wikiInlineRules = [];
    wikiInlineRules.push("!?'''''");        // 1. bolditalic
    wikiInlineRules.push("!?'''");          // 2. bold
    wikiInlineRules.push("!?''");           // 3. italic
    wikiInlineRules.push("!?__");           // 4. underline
    wikiInlineRules.push("!?~~");           // 5. strike
    wikiInlineRules.push("!?,,");           // 6. subscript
    wikiInlineRules.push("!?\\^");          // 7. superscript
    wikiInlineRules.push("!?\\{\\{\\{.*?\\}\\}\\}");  // 8. code block
    wikiInlineRules.push("!?`.*?`");        // 9. inline
    wikiInlineRules.push("[!&]?" + _ticketLink);    // 10. ticket
    wikiInlineRules.push("!?" + _reportLink);       // 11. report
    wikiInlineRules.push(                   // 12. changeset
        "!?\\[" + _changesetId + "(?:" + _changesetPath + ")?\\]"
        + "|(?:\\b|!)r" + _changesetId + "\\b(?!:" + _changesetId + ")");
    wikiInlineRules.push(                   // 13. log
        "!?\\[" + _changesetId + "[-:]" + _changesetId + "(?:" + _changesetPath + ")?\\]"
        + "|(?:\\b|!)r" + _changesetId + "[-:]" + _changesetId + "\\b");
    wikiInlineRules.push("!?" + _tracLink); // 14. wiki:TracLinks
    wikiInlineRules.push("!?\\[(?:"         // 15. [wiki:TracLinks label] or [/relative label]
        + "[/.#][^ \\t\\r\\f\\v[\\]]*|"
        + _linkScheme + ":(?:" + _quotedString + "|[^\\] \\t\\r\\f\\v]*)|"
        + _wikiPageName + "[ \\t\\r\\f\\v]+(?:" + _quotedString + "|[^\\]]+)"
        + ")(?:[ \\t\\r\\f\\v]+(?:" + _quotedString + "|[^\\]]+))?\\]");
                                            // 16. [[macro]]
    wikiInlineRules.push("!?\\[\\[[\\w/+-]+(?:\\]\\]|\\(.*?\\)\\]\\])");
                                            // 17. WikiPageName
    wikiInlineRules.push("!?" + _wikiPageName);
                                            // 18. ["internal free link"]
    wikiInlineRules.push("!?\\[(?:" + _quotedString + ")\\]");

    var wikiRules = [];
    wikiRules.push.apply(wikiRules, wikiInlineRules);
    wikiRules.push(_citation);              // 19. citation
                                            // 20. header
    wikiRules.push("^ *={1,6} *.*? *={1,6} *(?:#[\\w:][-\\w\\d.:]*)?$");
                                            // 21. list
    wikiRules.push("^ +(?:[-*]|[0-9]+\\.|[a-zA-Z]\\.|[ivxIVX]{1,5}\\.) ");
                                            // 22. definition
    wikiRules.push("^[ \\t\\r\\f\\v]+(?:`[^`]*`|\\{\\{\\{.*?\\}\\}\\}|[^`{:]|:[^:])+::(?:[ \\t\\r\\f\\v]+|$)");
    wikiRules.push("^[ \\t\\r\\f\\v]+(?=[^ \\t\\r\\f\\v])");    // 23. leading space
    wikiRules.push("^[ \\t\\r\\f\\v]*\\|\\|");  // 24. opening table row
    wikiRules.push("\\|\\|[ \\t\\r\\f\\v]*$");  // 25. closing table row
    wikiRules.push("\\|\\|");               // 26. cell

    var wikiSyntaxRules = [];
    wikiSyntaxRules.push(_ticketLink);
    wikiSyntaxRules.push(_reportLink);
    wikiSyntaxRules.push("\\[" + _changesetId + "(?:" + _changesetPath + ")?\\]");
    wikiSyntaxRules.push("r" + _changesetId);
    wikiSyntaxRules.push("\\[" + _changesetId + "[-:]" + _changesetId + "(?:" + _changesetPath + ")?\\]");
    wikiSyntaxRules.push("r" + _changesetId + "[-:]" + _changesetId);

    var wikiInlineRulesPattern = new RegExp("(?:" + wikiInlineRules.join("|") + ")", "g");
    var wikiRulesPattern = new RegExp("(?:(" + wikiRules.join(")|(") + "))", "g");
    var wikiSyntaxPattern = new RegExp("^(?:" + wikiSyntaxRules.join("|") + ")$");
    var wikiSyntaxLogPattern = new RegExp("^[\\[r]" + _changesetId + "[-:]");

    TracWysiwyg.prototype._linkScheme = _linkScheme;
    TracWysiwyg.prototype._quotedString = _quotedString;
    TracWysiwyg.prototype._citation = _citation;
    TracWysiwyg.prototype._changesetId = _changesetId;
    TracWysiwyg.prototype._tracLink = _tracLink;
    TracWysiwyg.prototype._wikiPageName = _wikiPageName;
    TracWysiwyg.prototype.wikiInlineRules = wikiInlineRules;
    TracWysiwyg.prototype.wikiRules = wikiRules;
    TracWysiwyg.prototype.wikiInlineRulesPattern = wikiInlineRulesPattern;
    TracWysiwyg.prototype.wikiRulesPattern = wikiRulesPattern;
    TracWysiwyg.prototype.wikiSyntaxPattern = wikiSyntaxPattern;
    TracWysiwyg.prototype.wikiSyntaxLogPattern = wikiSyntaxLogPattern;
})();

TracWysiwyg.prototype.normalizeTracLink = function(link) {
    link = this.convertWikiSyntax(link);
    if (/^[\/.#]/.test(link)) {
        link = encode(link);
    }
    if (!/^[\w.+-]+:/.test(link)) {
        link = "wiki:" + link;
    }
    if (/^wiki:[^\"\']/.test(link) && /\s/.test(link)) {
        if (link.indexOf('"') < 0) {
            link = 'wiki:"' + link + '"';
        }
        else if (link.indexOf("'") < 0) {
            link = "wiki:'" + link + "'";
        }
        else {
            link = 'wiki:"' + link.replace(/"/g, "%22") + '"';
        }
    }
    return link;
};

TracWysiwyg.prototype.convertWikiSyntax = function(link) {
    var match = this.wikiSyntaxPattern.exec(link);
    if (match) {
        switch (match[0].charCodeAt(0)) {
        case 0x7b:  // "{"
            link = "report:" + link.slice(1, -1);
            break;
        case 0x5b:  // "["
            link = (this.wikiSyntaxLogPattern.test(link) ? "log:@" : "changeset:") + link.slice(1, -1);
            break;
        case 0x23:  // #
            link = "ticket:" + link.substring(1);
            break;
        case 0x72:  // r
            link = (this.wikiSyntaxLogPattern.test(link) ? "log:@" : "changeset:") + link.substring(1);
            break;
        }
    }
    return link;
};

TracWysiwyg.prototype.wikitextToFragment = function(wikitext, contentDocument) {
    var getSelfOrAncestor = TracWysiwyg.getSelfOrAncestor;
    var quickSearchURL = TracWysiwyg.quickSearchURL;
    var _linkScheme = this._linkScheme;
    var _quotedString = this._quotedString;
    var wikiInlineRules = this.wikiInlineRules;
    var wikiRulesPattern = new RegExp(this.wikiRulesPattern.source, "g");

    var self = this;
    var fragment = contentDocument.createDocumentFragment();
    var holder = fragment;
    var lines = wikitext.split("\n");
    var codeText = null;
    var currentHeader = null;
    var quoteDepth = [];
    var listDepth = [];
    var decorationStatus;
    var decorationStack;
    var inCodeBlock, inParagraph, inDefList, inTable, inTableRow;
    inCodeBlock = inParagraph = inDefList = inTable = inTableRow = false;

    function handleCodeBlock(line) {
        if (/^ *\{\{\{ *$/.test(line)) {
            inCodeBlock++;
            if (inCodeBlock == 1) {
                closeParagraph();
                codeText = [];
            }
            else {
                codeText.push(line);
            }
        }
        else if (/^ *\}\}\} *$/.test(line)) {
            inCodeBlock--;
            if (inCodeBlock == 0) {
                var pre = contentDocument.createElement("pre");
                pre.className = "wiki";
                pre.appendChild(contentDocument.createTextNode(codeText.join(
                    pre.addEventListener && !window.opera ? "\n" : "\n\r")));
                holder.appendChild(pre);
                codeText = [];
            }
            else {
                codeText.push(line);
            }
        }
        else {
            codeText.push(line);
        }
    }

    function handleCitation(value) {
        var quote = /^(?: *>)+/.exec(value)[0];
        var depth = quote.replace(/ +/, "").length;

        if (depth > quoteDepth.length) {
            closeParagraph();
            while (depth > quoteDepth.length) {
                openQuote((new RegExp("^(?: *>){" + (quoteDepth.length + 1) + "}")).exec(quote)[0].length, true);
            }
        }
        else if (depth == quoteDepth.length) {
            // nothing to do
        }
        else {
            closeParagraph();
            while (depth < quoteDepth.length) {
                closeQuote();
            }
        }
    }

    function openQuote(length, citation) {
        var target = holder;
        if (target != fragment) {
            target = getSelfOrAncestor(target, "blockquote");
        }

        var element = contentDocument.createElement("blockquote");
        if (citation) {
            element.className = "citation";
        }
        (target || fragment).appendChild(element);
        holder = element;
        quoteDepth.push(length);
    }

    function closeQuote() {
        var target = getSelfOrAncestor(holder, "blockquote");
        holder = target.parentNode;
        quoteDepth.pop();
    }

    function handleHeader(line) {
        var match = /^ *(={1,6}) *(.*?) *(={1,6}) *(?:#([\w:][-\w\d:.]*))?$/.exec(line);
        if (!match || match[1].length != match[3].length) {
            return null;
        }

        closeToFragment();
        var tag = "h" + match[1].length;
        var element = contentDocument.createElement(tag);
        if (match[4]) {
            element.id = match[4];
        }
        fragment.appendChild(element);
        holder = element;
        return tag;
    }

    function closeHeader() {
        if (currentHeader) {
            var target = getSelfOrAncestor(holder, currentHeader);
            holder = target.parentNode;
            currentHeader = null;
        }
    }

    function handleInline(name) {
        if (name == "bolditalic") {
            if (decorationStatus.italic) {
                handleInline("italic");
                handleInline("bold");
            }
            else {
                handleInline("bold");
                handleInline("italic");
            }
            return;
        }

        var d = contentDocument;
        if (decorationStatus[name]) {
            var tagNames = [];
            for (var index = decorationStack.length - 1; index >= 0; index--) {
                var tagName = holder.tagName;
                holder = holder.parentNode;
                if (decorationStack[index] == name) {
                    break;
                }
                tagNames.push(tagName);
            }
            decorationStack.splice(index, 1);
            decorationStatus[name] = false;
            while (tagNames.length > 0) {
                var element = d.createElement(tagNames.pop());
                holder.appendChild(element);
                holder = element;
            }
            return;
        }

        var tagName;
        switch (name) {
        case "bold":        tagName = "b";      break;
        case "italic":      tagName = "i";      break;
        case "underline":   tagName = "u";      break;
        case "strike":      tagName = "del";    break;
        case "subscript":   tagName = "sub";    break;
        case "superscript": tagName = "sup";    break;
        }

        if (holder == fragment) {
            openParagraph();
        }
        element = d.createElement(tagName);
        holder.appendChild(element);
        holder = element;
        decorationStatus[name] = true;
        decorationStack.push(name);
    }

    function handleInlineCode(value, length) {
        var d = contentDocument;
        var element = d.createElement("tt");
        value = value.slice(length, -length);
        if (value.length > 0) {
            element.appendChild(d.createTextNode(value));
            holder.appendChild(element);
        }
    }

    function createAnchor(link, label) {
        var d = contentDocument;
        var anchor = d.createElement("a");
        anchor.href = quickSearchURL(link);
        anchor.title = link;
        anchor.setAttribute("tw:link", link);
        anchor.appendChild(d.createTextNode(label));
        holder.appendChild(anchor);
    }

    function handleTracLinks(value) {
        var d = contentDocument;
        var match = handleTracLinks.pattern.exec(value);
        if (match) {
            var link = match[1];
            if (!/^(?:[\w.+-]+:|[\/.#].*)/.test(link)) {
                link = "wiki:" + link;
            }
            var text = (match[2] || match[1]).replace(/^(["'])(.*)\1$/g, "$2");
            createAnchor(link, text);
        }
        else {
            holder.appendChild(d.createTextNode(value));
        }
    }
    handleTracLinks.pattern = new RegExp("\\["
        + "((?:" + _linkScheme + ":)?(?:" + _quotedString + "|[^\\]\\s]+))"
        + "(?:\\s+(.*))?\\]");

    function handleTracWikiLink(value) {
        createAnchor(value, value);
    }

    function handleWikiPageName(value) {
        createAnchor("wiki:" + value, value);
    }

    function handleTracOtherLinks(value) {
        createAnchor(self.convertWikiSyntax(value), value);
    }

    function handleTracTicketLink(value) {
        if (!/^&/.test(value)) {
            handleTracOtherLinks(value);
            return true;
        }
        return false;
    }

    function handleList(value) {
        var match = /^( +)(?:([-*])|((?:([0-9]+)|([a-z])|([A-Z])|[ivxIVX]{1,5})))/.exec(value);
        var tag, className, depth, start;
        if (!match) {
            holder.appendChild(contentDocument.createTextNode(value));
            return;
        }

        depth = match[1].length;
        if (match[2]) {
            tag = "ul";
        }
        else if (match[3]) {
            tag = "ol";
            switch (match[3]) {
            case "0":
                className = "arabiczero";
                break;
            case "1":
                break;
            case "i":
                className = "lowerroman";
                break;
            case "I":
                className = "upperroman";
                break;
            default:
                start = match[3];
                if (match[4]) {
                    start = parseInt(match[4], 10);
                }
                else if (match[5]) {
                    className = "loweralpha";
                }
                else if (match[6]) {
                    className = "upperalpha";
                }
                break;
            }
        }

        var last = listDepth.length - 1;
        if (depth > (last >= 0 ? listDepth[last] : 0)) {
            closeParagraph();
            openList(tag, className, start, depth);
        }
        else {
            while (listDepth.length > 1) {
                if (depth >= listDepth[last]) {
                    break;
                }
                closeList();
                last = listDepth.length - 1;
            }
            var list = getSelfOrAncestor(holder, "li");
            if (tag != list.parentNode.tagName.toLowerCase()) {
                closeList();
                openList(tag, className, start, depth);
            }
            else {
                var tmp = contentDocument.createElement("li");
                list.parentNode.appendChild(tmp);
                holder = tmp;
                listDepth[last] = depth;
            }
        }
    }

    function openList(tag, className, start, depth) {
        var d = contentDocument;
        var h = holder;

        var container = d.createElement(tag);
        if (className) {
            container.className = className;
        }
        if (start) {
            container.setAttribute("start", start);
        }
        var list = d.createElement("li");
        container.appendChild(list);

        var target;
        if (h == fragment) {
            target = fragment;
        }
        else {
            target = getSelfOrAncestor(h, "li");
            if (!target) {
                closeToFragment();
                target = fragment;
            }
        }
        target.appendChild(container);
        holder = list;
        listDepth.push(depth);
    }

    function closeList() {
        var target = getSelfOrAncestor(holder, "li");
        holder = target.parentNode.parentNode;
        listDepth.pop();
    }

    function handleDefinition(value) {
        var d = contentDocument;
        var h = holder;
        var dl = null;
        if (inDefList) {
            dl = getSelfOrAncestor(h, "dl");
        }
        else {
            closeParagraph();
            dl = d.createElement("dl");
            fragment.appendChild(dl);
            inDefList = true;
        }

        var match = /^ +(.*?)\s*::/.exec(value);
        var dt = d.createElement("dt");
        var oneliner = self.wikitextToOnelinerFragment(match[1], d);
        dt.appendChild(oneliner);
        dl.appendChild(dt);

        var dd = d.createElement("dd");
        dl.appendChild(dd);
        holder = dd;
    }

    function closeDefList() {
        var element = getSelfOrAncestor(holder, "dl");
        if (element) {
            holder = element.parentNode;
        }
        inDefList = false;
    }

    function handleIndent(value) {
        var depth = value.length;
        var last = quoteDepth.length - 1;

        if (depth > (last >= 0 ? quoteDepth[last] : 0)) {
            closeParagraph();
            openQuote(depth, false);
        }
        else {
            while (quoteDepth.length > 0) {
                if (depth >= quoteDepth[last]) {
                    break;
                }
                closeParagraph();
                closeQuote();
                last = quoteDepth.length - 1;
            }
            quoteDepth[last] = depth;
        }
    }

    function openParagraph() {
        if (!inParagraph) {
            var element = contentDocument.createElement("p");
            holder.appendChild(element);
            holder = element;
            inParagraph = true;
        }
    }

    function closeParagraph() {
        if (inParagraph) {
            var target = holder;
            if (target != fragment) {
                target = getSelfOrAncestor(target, "p");
            }
            holder = target.parentNode;
            inParagraph = false;
        }
    }

    function handleTableCell(action) {
        var d = contentDocument;
        var h = holder;
        var table, tbody;

        if (!inTable) {
            closeToFragment();
            table = d.createElement("table");
            table.className = "wiki";
            tbody = d.createElement("tbody");
            table.appendChild(tbody);
            fragment.appendChild(table);
            inTable = true;
            inTableRow = false;
        }
        else {
            tbody = getSelfOrAncestor(h, "tbody");
        }

        var row;
        switch (action) {
        case 1:
            row = d.createElement("tr");
            tbody.appendChild(row);
            inTableRow = true;
            break;
        case 0:
            row = getSelfOrAncestor(h, "tr");
            break;
        case -1:
            if (inTableRow) {
                var target = getSelfOrAncestor(h, "tr");
                holder = target.parentNode;
                inTableRow = false;
            }
            return;
        }

        var cell = d.createElement("td");
        row.appendChild(cell);
        holder = cell;
    }

    function closeTable() {
        if (inTable) {
            var target = getSelfOrAncestor(holder, "table");
            holder = target.parentNode;
            inTable = inTableRow = false;
        }
    }

    function closeToFragment() {
        var element = holder;
        var _fragment = fragment;

        while (element != _fragment) {
            switch (element.tagName.toLowerCase()) {
            case "p":
                closeParagraph();
                element = holder;
                break;
            case "li":
                closeList();
                element = holder;
                break;
            case "dd":
                closeDefList();
                element = holder;
                break;
            case "blockquote":
                closeQuote();
                element = holder;
                break;
            case "td": case "tr": case "tbody": case "table":
                closeTable();
                element = holder;
                break;
            default:
                element = element.parentNode;
                break;
            }
        }

        holder = _fragment;
    }

    function getMatchFirstIndex(match) {
        var length = match.length;
        for (var i = 1; i < length; i++) {
            if (match[i]) {
                return i;
            }
        }
        return null;
    }

    for (var indexLines = 0; indexLines < lines.length; indexLines++) {
        var line = lines[indexLines].replace(/\r$/, "");
        if (inCodeBlock || /^ *\{\{\{ *$/.test(line)) {
            handleCodeBlock(line);
            continue;
        }
        if (/^----/.test(line)) {
            closeToFragment();
            fragment.appendChild(contentDocument.createElement("hr"));
            continue;
        }
        if (line.length == 0) {
            closeToFragment();
            continue;
        }
        line = line.replace(/\t/g, "        ");

        wikiRulesPattern.lastIndex = 0;
        var prevIndex = wikiRulesPattern.lastIndex;
        decorationStatus = {};
        decorationStack = [];
        for ( ; ; ) {
            var match = wikiRulesPattern.exec(line);
            var matchFirstIndex = null;
            var text = null;
            if (match) {
                matchFirstIndex = getMatchFirstIndex(match);
                if (prevIndex < match.index) {
                    text = line.substring(prevIndex, match.index);
                }
            }
            else {
                text = line.substring(prevIndex);
            }

            if ((prevIndex == 0 ? !!text : (match && match.index == 0 && matchFirstIndex <= wikiInlineRules.length))
                && (!inParagraph || quoteDepth.length > 0)
                && (!inDefList || !/^ /.test(line)))
            {
                closeToFragment();
            }
            if (text || match && matchFirstIndex <= wikiInlineRules.length) {
                if (inParagraph && (prevIndex == 0 || /^(?:(?: *>)+|\s+)$/.test(line.substring(0, prevIndex)))) {
                    text = text ? (" " + text) : " ";
                }
                if (holder == fragment || quoteDepth.length > 0) {
                    if (!inParagraph) {
                        openParagraph();
                    }
                }
                if (text) {
                    holder.appendChild(contentDocument.createTextNode(text));
                }
            }
            if (!match) {
                break;
            }
            prevIndex = wikiRulesPattern.lastIndex;
            var matchText = match[0];

            if (!/^!/.test(matchText)) {    // start '!'
                switch (matchFirstIndex) {
                case 1:     // bolditalic
                    handleInline("bolditalic");
                    continue;
                case 2:     // bold
                    handleInline("bold");
                    continue;
                case 3:     // italic
                    handleInline("italic");
                    continue;
                case 4:     // underline
                    handleInline("underline");
                    continue;
                case 5:     // strike
                    handleInline("strike");
                    continue;
                case 6:     // subscript
                    handleInline("subscript");
                    continue;
                case 7:     // superscript
                    handleInline("superscript");
                    continue;
                case 8:     // code block
                    handleInlineCode(matchText, 3);
                    continue;
                case 9:     // inline
                    handleInlineCode(matchText, 1);
                    continue;
                case 10:    // ticket
                    if (handleTracTicketLink(matchText)) {
                        continue;
                    }
                    break;
                case 11:    // report
                case 12:    // changeset
                case 13:    // log
                    handleTracOtherLinks(matchText);
                    continue;
                case 14:    // wiki:TracLinks
                    handleTracWikiLink(matchText);
                    continue;
                case 15:    // [wiki:TracLinks label]
                    handleTracLinks(matchText);
                    continue;
                case 16:    // [[macro]]
                    break;
                case 17:    // WikiPageName
                    handleWikiPageName(matchText);
                    continue;
                case 18:    // ["internal free link"]
                    handleWikiPageName(matchText.slice(1, -1));
                    continue;
                case 19:    // citation
                    handleCitation(matchText);
                    continue;
                case 20:    // header
                    currentHeader = handleHeader(matchText);
                    if (currentHeader) {
                        line = line.replace(/ *=+ *(?:#[\w:][-\w\d:.]*)?$/, "");
                        wikiRulesPattern.lastIndex = prevIndex = line.match(/^ *=+ */)[0].length;
                        continue;
                    }
                    break;
                case 21:    // list
                    handleList(matchText)
                    continue;
                case 22:    // definition
                    handleDefinition(matchText);
                    continue;
                case 23:    // leading space
                    if (listDepth.length == 0 && !inDefList) {
                        handleIndent(matchText);
                        continue;
                    }
                    break;
                case 24:    // opening table row
                    handleTableCell(1);
                    continue;
                case 25:    // closing table row
                    if (inTable) {
                        handleTableCell(-1);
                        continue;
                    }
                    break;
                case 26:    // cell
                    if (inTable) {
                        handleTableCell(0);
                        continue;
                    }
                    break;
                }
            }

            if (matchText) {
                if (listDepth.length == 0 && !currentHeader && !inDefList && !inTable) {
                    openParagraph();
                }
                var tmp;
                if (matchFirstIndex == 16) {
                    tmp = matchText == "[[BR]]"
                        ? contentDocument.createElement("br")
                        : contentDocument.createTextNode(matchText);
                }
                else {
                    tmp = contentDocument.createTextNode(/^!/.test(matchText) ? matchText.substring(1) : matchText);
                }
                holder.appendChild(tmp);
            }
        }
        if (currentHeader) {
            closeHeader();
        }
        if (inTable) {
            handleTableCell(-1);
        }
    }

    return fragment;
};

TracWysiwyg.prototype.wikitextToOnelinerFragment = function(wikitext, contentDocument) {
    var source = this.wikitextToFragment(wikitext, contentDocument);
    var fragment = contentDocument.createDocumentFragment();
    this.collectChildNodes(fragment, source.firstChild);
    return fragment;
};

TracWysiwyg.prototype.wikiOpenTokens = {
    "h1": "= ", "h2": "== ", "h3": "=== ", "h4": "==== ", "h5": "===== ", "h6": "====== ",
    "b": "'''", "strong": "'''",
    "i": "''", "em": "''",
    "u": "__",
    "del": "~~", "strike": "~~",
    "sub": ",,",
    "sup": "^",
    "hr": "----\n",
    "dl": true,
    "dt": " ",
    "dd": "   ",
    "table": true,
    "tbody": true,
    "tr": true,
    "td": "||", "th": "||" };

TracWysiwyg.prototype.wikiCloseTokens = {
    "#text": true,
    "a": true,
    "tt": true,
    "h1": " =", "h2": " ==", "h3": " ===", "h4": " ====", "h5": " =====", "h6": " ======",
    "b": "'''", "strong": "'''",
    "i": "''", "em": "''",
    "u": "__",
    "del": "~~", "strike": "~~",
    "sub": ",,",
    "sup": "^",
    "br": true,
    "hr": true,
    "dl": "\n",
    "dt": "::\n",
    "dd": "\n",
    "table": "\n",
    "tbody": true,
    "tr": "||\n",
    "td": true, "th": true };

TracWysiwyg.prototype.wikiBlockTags = {
    "h1": true, "h2": true, "h3": true, "h4": true, "h5": true, "h6": true,
    "table": true, "dl": true, "hr": true };

TracWysiwyg.prototype.wikiInlineTags = {
    "a": true, "tt": true, "b": true, "strong": true, "i": true, "u": true,
    "del": true, "strike": true, "sub": true, "sup": true, "br": true };

TracWysiwyg.prototype.domToWikitext = function(root) {
    var getTextContent = TracWysiwyg.getTextContent;
    var wikiOpenTokens = this.wikiOpenTokens;
    var wikiCloseTokens = this.wikiCloseTokens;
    var wikiInlineTags = this.wikiInlineTags;
    var wikiBlockTags = this.wikiBlockTags;
    var wikiInlineRulesPattern = this.wikiInlineRulesPattern;
    var tracLinkPattern = new RegExp("^" + this._tracLink + "$");
    var wikiPageNamePattern = new RegExp("^" + this._wikiPageName + "$");
    var decorationTokenPattern = /^(?:'''|''|__|\^|,,)$/;

    var texts = [];
    var stack = [];
    var last = root;
    var listDepth = 0;
    var quoteDepth = 0;
    var quoteCitation = false;
    var needEscape = true;
    var inCodeBlock = false;
    var skipNode = null;

    function escapeText(s) {
        if (/^!?\[\[/.test(s) && /\]\]$/.test(s)) {
            return s != "[[BR]]" ? s : "!" + s;
        }
        if (/^&#\d+/.test(s)) {
            return s;
        }
        return "!" + s;
    }

    function isTailEscape() {
        var t = texts;
        var length = t.length;
        return length > 0 && /!$/.test(t[length - 1]);
    }

    function isInlineNode(node) {
        if (node) {
            switch (node.nodeType) {
            case 1:
                return (node.tagName.toLowerCase() in wikiInlineTags);
            case 3:
                return true;
            }
        }
        return false;
    }

    function nodeDecorations(node) {
        var _wikiOpenTokens = wikiOpenTokens;
        var _decorationTokenPattern = decorationTokenPattern;
        var hash = {};

        for ( ; ; ) {
            var childNodes = node.childNodes;
            if (!childNodes || childNodes.length != 1) {
                break;
            }
            var child = childNodes[0];
            if (child.nodeType != 1) {
                break;
            }
            var token = _wikiOpenTokens[child.tagName.toLowerCase()];
            if (_decorationTokenPattern.test(token)) {
                hash[token] = true;
            }
            node = child;
        }

        return hash;
    }

    function pushTextWithDecorations(text, node) {
        var _texts = texts;
        var _decorationTokenPattern = decorationTokenPattern;
        var decorationsHash = nodeDecorations(node);
        var decorations = [];
        var cancelDecorations = [];

        while (_texts.length > 0) {
            var token = _texts[_texts.length - 1];
            if (_decorationTokenPattern.test(token)) {
                if (decorationsHash[token]) {
                    delete decorationsHash[token];
                    cancelDecorations.push(_texts.pop());
                    continue;
                }
                if ((token == "'''" || token == "''") && _texts.length > 1) {
                    var moreToken = _texts[_texts.length - 2];
                    if (_decorationTokenPattern.test(moreToken)
                        && token + moreToken == "'''''"
                        && decorationsHash[moreToken])
                    {
                        delete decorationsHash[moreToken];
                        cancelDecorations.push(moreToken);
                        _texts[_texts.length - 2] = _texts[_texts.length - 1];
                        _texts.pop();
                    }
                }
            }
            break;
        }

        for (var token in decorationsHash) {
            decorations.push(token);
        }
        decorations.sort();

        if (decorations.length > 0) {
            texts.push.apply(texts, decorations);
        }
        texts.push(text);
        if (decorations.length > 0) {
            decorations.reverse();
            texts.push.apply(texts, decorations);
        }
        if (cancelDecorations.length > 0) {
            cancelDecorations.reverse();
            texts.push.apply(texts, cancelDecorations);
        }
    }

    function pushOpenToken(token) {
        var _texts = texts;
        var _decorationTokenPattern = decorationTokenPattern;
        var length = _texts.length;
        if (length == 0 || !_decorationTokenPattern.test(token)) {
            _texts.push(token);
            return;
        }
        var last = _texts[length - 1];
        if (!_decorationTokenPattern.test(last)) {
            _texts.push(token);
            return;
        }
        if (last == token) {
            _texts.pop();
            return;
        }
        if (length < 2 || last + token != "'''''") {
            _texts.push(token);
            return;
        }
        if (_texts[length - 2] == token) {
            _texts[length - 2] = _texts[length - 1];
            _texts.pop();
        }
        else {
            _texts.push(token);
        }
    }

    function pushAnchor(node) {
        var link = node.getAttribute("tw:link") || node.href;
        var value = getTextContent(node).replace(/^\s+|\s+$/g, "");
        if (!value) {
            return;
        }
        var text = null;
        if (link == value) {
            text = tracLinkPattern.test(value) ? value : "[" + value + "]";
        }
        else {
            var usingValue = false;
            var match = /^([\w.+-]+):(@?(.*))$/.exec(link);
            switch (match && match[1]) {
            case "wiki":
                usingValue = value == match[2] && wikiPageNamePattern.test(value);
                break;
            case "changeset":
                usingValue = value == "[" + match[2] + "]"
                    || /^\d+$/.test(match[2]) && value == "r" + match[2];
                break;
            case "log":
                usingValue = value == "[" + match[3] + "]" || value == "r" + match[3];
                break;
            case "report":
                usingValue = value == "{" + match[2] + "}";
                break;
            case "ticket":
                usingValue = value == "#" + match[2];
                break;
            }
            if (usingValue) {
                text = value;
            }
        }
        if (isTailEscape()) {
            texts.push(" ");
        }
        if (text === null) {
            if (!/[\]\"\']/.test(value)) {
                text = "[" + link + " " + value + "]";
            }
            else if (!/\"/.test(value)) {
                text = "[" + link + ' "' + value + '"]';
            }
            else if (!/\'/.test(value)) {
                text = "[" + link + " '" + value + "']";
            }
            else {
                text = "[" + link + ' "' + value.replace(/"+/g, "") + '"]';
            }
        }
        pushTextWithDecorations(text, node);
    }

    function string(source, times) {
        var value = (1 << times) - 1;
        if (value <= 0) {
            return "";
        }
        else {
            return value.toString(2).replace(/1/g, source);
        }
    }

    function open(name, node) {
        if (skipNode) {
            return;
        }
        var token = wikiOpenTokens[name];
        if (token) {
            if (name in wikiBlockTags && isInlineNode(node.previousSibling)) {
                texts.push("\n");
            }
            if (token !== true) {
                if (name in wikiInlineTags && isTailEscape()) {
                    texts.push(" ");
                }
                pushOpenToken(token);
            }
        }
        else {
            switch (name) {
            case "#text":
                var value = node.nodeValue;
                if (value) {
                    if (needEscape) {
                        value = value.replace(wikiInlineRulesPattern, escapeText);
                    }
                    if (!inCodeBlock) {
                        value = value.replace(/^\s+|\s+$/g, " ");
                    }
                    texts.push(value);
                }
                break;
            case "p":
                if (quoteDepth > 0) {
                    texts.push(string(quoteCitation ? ">" : "  ", quoteDepth));
                }
                break;
            case "a":
                skipNode = node;
                pushAnchor(node);
                break;
            case "li":
                texts.push(" " + string("  ", listDepth - 1));
                var container = node.parentNode;
                if ((container.tagName || "").toLowerCase() == "ol") {
                    var start = container.getAttribute("start") || "";
                    if (/^(?:[0-9]+|[a-zA-Z]|[ivxIVX]{1,5})$/.test(start)) {
                        texts.push(start, ". ");
                    }
                    else {
                        switch (container.className) {
                        case "arabiczero":  texts.push("0. "); break;
                        case "lowerroman":  texts.push("i. "); break;
                        case "upperroman":  texts.push("I. "); break;
                        case "loweralpha":  texts.push("a. "); break;
                        case "upperalpha":  texts.push("A. "); break;
                        default:            texts.push("1. "); break;
                        }
                    }
                }
                else {
                    texts.push("* ");
                }
                break;
            case "ul": case "ol":
                if (listDepth == 0) {
                    if (isInlineNode(node.previousSibling)) {
                        texts.push("\n");
                    }
                }
                else if (listDepth > 0) {
                    if (node.parentNode.tagName.toLowerCase() == "li") {
                        texts.push("\n");
                    }
                }
                listDepth++;
                break;
            case "br":
                if (node.nextSibling) {
                    var value;
                    if (inCodeBlock) {
                        value = "\n";
                    }
                    else if (isTailEscape()) {
                        value = " [[BR]]";
                    }
                    else {
                        value = "[[BR]]";
                    }
                    texts.push(value);
                }
                break;
            case "pre":
                if (isInlineNode(node.previousSibling)) {
                    texts.push("\n");
                }
                texts.push(/^(?:li|dd)$/i.test(node.parentNode.tagName) ? "\n{{{\n" : "{{{\n");
                needEscape = false;
                inCodeBlock = true;
                break;
            case "blockquote":
                if (isInlineNode(node.previousSibling)) {
                    texts.push("\n");
                }
                quoteDepth++;
                if (quoteDepth == 1) {
                    quoteCitation = (node.className == "citation");
                }
                break;
            case "tt":
                skipNode = node;
                var value = getTextContent(node);
                var text;
                if (value) {
                    if (isTailEscape()) {
                        texts.push(" ");
                    }
                    if (!/`/.test(value)) {
                        text = "`" + value + "`";
                    }
                    else if (!/\{\{\{|\}\}\}/.test(value)) {
                        text = "{{{" + value + "}}}";
                    }
                    else {
                        text = value.replace(/[^`]+|`+/g, function(m) {
                            return m.charCodeAt(0) != 0x60 ? "`" + m + "`" : "{{{" + m + "}}}";
                        });
                    }
                    pushTextWithDecorations(text, node);
                }
                break;
            case "span":
                if (node.className == "underline") {
                    texts.push(wikiOpenTokens["u"]);
                }
                break;
            }
        }
    }

    function close(name, node) {
        if (skipNode) {
            if (skipNode == node) {
                skipNode = null;
            }
            return;
        }
        var token = wikiCloseTokens[name];
        if (token === true) {
            // nothing to do
        }
        else if (token) {
            if (name in wikiInlineTags && isTailEscape()) {
                texts.push(" ", token);
            }
            else {
                texts.push(token);
            }
        }
        else {
            switch (name) {
            case "p":
                texts.push(quoteDepth == 0 ? "\n\n" : "\n");
                break;
            case "li":
                if (node.getElementsByTagName("li").length == 0) {
                    texts.push("\n");
                }
                break;
            case "ul": case "ol":
                listDepth--;
                if (listDepth == 0) {
                    texts.push("\n");
                }
                break;
            case "pre":
                var text;
                var parentNode = node.parentNode;
                if (parentNode && /^(?:li|dd)$/i.test(parentNode.tagName)) {
                    var nextSibling = node.nextSibling;
                    if (!nextSibling) {
                        text = "\n}}}";
                    }
                    else if (nextSibling.nodeType != 1) {
                        text = "\n}}}\n";
                    }
                    else if (nextSibling.tagName.toLowerCase() == "pre") {
                        text = "\n}}}";
                    }
                    else {
                        text = "\n}}}\n";
                    }
                    if (text.slice(-1) == "\n") {
                        text += listDepth > 0 ? string("  ", listDepth + 1) : "    ";
                    }
                }
                else {
                    text = "\n}}}\n";
                }
                texts.push(text);
                needEscape = true;
                inCodeBlock = false;
                break;
            case "blockquote":
                quoteDepth--;
                break;
            case "span":
                if (node.className == "underline") {
                    texts.push(wikiCloseTokens["u"]);
                }
                break;
            }
        }
        if (/^h[1-6]$/.test(name)) {
            if (/^[\w:][-\w\d.:]*$/.test(node.id || "")) {
                texts.push(" #", node.id);
            }
            texts.push("\n");
        }
    }

    function iterator(node) {
        var name = null;
        switch (node && node.nodeType) {
        case 1: // element
            name = node.tagName.toLowerCase();
            break;
        case 3: // text
            name = "#text";
            break;
        }

        if (node && last == node.parentNode) {  // down
            // nothing to do
        }
        else if (node && last == node.previousSibling) {    // forward
            close(stack.pop(), last);
        }
        else {  // up, forward
            var tmp = last;
            var nodeParent = node ? node.parentNode : root;
            for ( ; ; ) {
                var parent = tmp.parentNode;
                if (parent == node) {
                    break;
                }
                close(stack.pop(), tmp);
                if (parent == nodeParent || !parent) {
                    if (!node) {
                        return;
                    }
                    break;
                }
                tmp = parent;
            }
        }
        open(name, node);
        stack.push(name);
        last = node;
    }

    this.treeWalk(root, iterator);
    return texts.join("").replace(/^(?: *\n)+|(?: *\n)+$/g, "");
};

if (window.getSelection) {
    TracWysiwyg.prototype.insertTableCell = function(row, index) {
        var cell = row.insertCell(index);
        cell.appendChild(this.contentDocument.createElement("br"));
        return cell;
    };
    TracWysiwyg.prototype.getFocusNode = function() {
        return this.contentWindow.getSelection().focusNode;
    };
    TracWysiwyg.prototype.selectNode = function(node) {
        var selection = this.contentWindow.getSelection();
        selection.removeAllRanges();
        var range = this.contentDocument.createRange();
        range.selectNode(node);
        selection.addRange(range);
    };
    TracWysiwyg.prototype.selectNodeContents = function(node) {
        var selection = this.contentWindow.getSelection();
        selection.removeAllRanges();
        var range = this.contentDocument.createRange();
        range.selectNodeContents(node);
        selection.addRange(range);
    };
    TracWysiwyg.prototype.getSelectionRange = function() {
        var selection = this.contentWindow.getSelection();
        return selection.rangeCount > 0 ? selection.getRangeAt(0) : null;
    };
    TracWysiwyg.prototype.getSelectionText = function() {
        var range = this.getSelectionRange();
        return range ? range.toString() : null;
    };
    TracWysiwyg.prototype.getSelectionHTML = function() {
        var fragment = this.getSelectionFragment();
        var anonymous = this.contentDocument.createElement("div");
        anonymous.appendChild(fragment);
        return anonymous.innerHTML;
    };
    TracWysiwyg.prototype.getSelectionFragment = function() {
        var range = this.getSelectionRange();
        return range ? range.cloneContents() : this.contentDocument.createDocumentFragment();
    };
    TracWysiwyg.prototype.getSelectionPosition = function() {
        var range = this.getSelectionRange();
        var position = { start: null, end: null };
        if (range) {
            position.start = range.startContainer;
            position.end = range.endContainer;
        }
        return position;
    };
    TracWysiwyg.prototype.expandSelectionToElement = function(arg) {
        var selection = this.contentWindow.getSelection();
        if (arg.start || arg.end) {
            var range = selection.rangeCount > 0 ? selection.getRangeAt(0) : this.contentDocument.createRange();
            selection.removeAllRanges();
            if (arg.start) {
                range.setStartBefore(arg.start);
            }
            if (arg.end) {
                range.setEndAfter(arg.end);
            }
            selection.addRange(range);
        }
    };
    TracWysiwyg.prototype.selectionContainsTagName = function(name) {
        var selection = this.contentWindow.getSelection();
        if (selection.rangeCount <= 0) {
            return false;
        }
        var ancestor = selection.getRangeAt(0).commonAncestorContainer;
        if (!ancestor) {
            return false;
        }
        if (TracWysiwyg.getSelfOrAncestor(ancestor, name)) {
            return true;
        }
        if (ancestor.nodeType != 1) {
            return false;
        }
        var elements = ancestor.getElementsByTagName(name);
        var length = elements.length;
        for (var i = 0; i < length; i++) {
            if (selection.containsNode(elements[i], true)) {
                return true;
            }
        }
        return false;
    };
    TracWysiwyg.prototype.insertHTML = function(html) {
        this.execCommand("inserthtml", html);
    };
}
else if (document.selection) {
    TracWysiwyg.prototype.insertTableCell = function(row, index) {
        return row.insertCell(index);
    };
    TracWysiwyg.prototype.getFocusNode = function() {
        this.contentWindow.focus();
        var d = this.contentDocument;
        var range = d.selection.createRange();
        var node = range.item ? range.item(0) : range.parentElement();
        return node.ownerDocument == d ? node : null;
    };
    TracWysiwyg.prototype.selectNode = function(node) {
        var d = this.contentDocument;
        var body = d.body;
        var range;
        d.selection.empty();
        try {
            range = body.createControlRange();
            range.addElement(node);
        }
        catch (e) {
            range = body.createTextRange();
            range.moveToElementText(node);
        }
        range.select();
    };
    TracWysiwyg.prototype.selectNodeContents = function(node) {
        var d = this.contentDocument;
        d.selection.empty();
        var range = d.body.createTextRange();
        range.moveToElementText(node);
        range.select();
    };
    TracWysiwyg.prototype.getSelectionRange = function() {
        var range = this.contentDocument.selection.createRange();
        if (range && range.item) {
            range = range.item(0);
        }
        return range;
    };
    TracWysiwyg.prototype.getSelectionText = function() {
        var range = this.getSelectionRange();
        return range ? range.text : null;
    };
    TracWysiwyg.prototype.getSelectionHTML = function() {
        var range = this.getSelectionRange();
        return range ? range.htmlText : null;
    };
    TracWysiwyg.prototype.getSelectionFragment = function() {
        var d = this.contentDocument;
        var fragment = d.createDocumentFragment();
        var anonymous = d.createElement("div");
        anonymous.innerHTML = this.getSelectionHTML();
        this.collectChildNodes(fragment, anonymous);
        return fragment;
    };
    TracWysiwyg.prototype.getSelectionPosition = function() {
        this.contentWindow.focus();
        var d = this.contentDocument;
        var range = d.selection.createRange();
        var startNode = null;
        var endNode = null;
        if (range.item) {
            if (range.item(0).ownerDocument == d) {
                startNode = range.item(0);
                endNode = range.item(range.length - 1);
            }
        }
        else {
            if (range.parentElement().ownerDocument == d) {
                var startRange = range.duplicate();
                startRange.collapse(true);
                startNode = startRange.parentElement();
                var endRange = range.duplicate();
                endRange.collapse(false);
                endNode = endRange.parentElement();
            }
        }
        return { start: startNode, end: endNode };
    };
    TracWysiwyg.prototype.expandSelectionToElement = function(arg) {
        var d = this.contentDocument;
        var body = d.body;
        var range = d.selection.createRange();
        var tmp;
        if (arg.start) {
            tmp = body.createTextRange();
            tmp.moveToElementText(arg.start);
            range.setEndPoint("StartToStart", tmp);
        }
        if (arg.end) {
            tmp = body.createTextRange();
            tmp.moveToElementText(arg.end);
            range.setEndPoint("EndToEnd", tmp);
        }
        if (tmp) {
            range.select();
        }
    };
    TracWysiwyg.prototype.selectionContainsTagName = function(name) {
        this.contentWindow.focus();
        var d = this.contentDocument;
        var selection = d.selection;
        var range = selection.createRange();
        var parent = range.item ? range.item(0) : range.parentElement();
        if (!parent) {
            return false;
        }
        if (TracWysiwyg.getSelfOrAncestor(parent, name)) {
            return true;
        }
        var elements = parent.getElementsByTagName(name);
        var length = elements.length;
        for (var i = 0; i < length; i++) {
            var testRange = selection.createRange();
            testRange.moveToElementText(elements[i]);
            if (range.compareEndPoints("StartToEnd", testRange) <= 0
                && range.compareEndPoints("EndToStart", testRange) >= 0)
            {
                return true;
            }
        }
        return false;
    };
    TracWysiwyg.prototype.insertHTML = function(html) {
        var range = this.contentDocument.selection.createRange();
        range.pasteHTML(html);
    };
}
else {
    TracWysiwyg.prototype.insertTableCell = function(row, index) { return null };
    TracWysiwyg.prototype.getFocusNode = function() { return null };
    TracWysiwyg.prototype.selectNode = function(node) { };
    TracWysiwyg.prototype.selectNodeContents = function(node) { return null };
    TracWysiwyg.prototype.getSelectionRange = function() { return null };
    TracWysiwyg.prototype.getSelectionText = function() { return null };
    TracWysiwyg.prototype.getSelectionHTML = function() { return null };
    TracWysiwyg.prototype.getSelectionFragment = function() { return null };
    TracWysiwyg.prototype.getSelectionPosition = function() { return null };
    TracWysiwyg.prototype.expandSelectionToElement = function(arg) { };
    TracWysiwyg.prototype.selectionContainsTagName = function(name) { return false };
    TracWysiwyg.prototype.insertHTML = function(html) { };
}

TracWysiwyg.prototype.treeWalk = (function() {
    var accept, reject;

    function filter(node) {
        switch (node.nodeType) {
        case 1: // element
            return /^(?:script|style)/i.test(node.tagName) ? reject : accept;
        case 3: // text
            return accept;
        default:
            return reject;
        }
    }

    if (document.createTreeWalker && navigator.userAgent.indexOf("AppleWebKit/") < 0) {
        accept = NodeFilter.FILTER_ACCEPT;
        reject = NodeFilter.FILTER_REJECT;
        return function(root, iterator) {
            var d = root.ownerDocument;
            var walker = d.createTreeWalker(root,
                NodeFilter.SHOW_ELEMENT | NodeFilter.SHOW_TEXT,
                { acceptNode: filter }, true);
            while (walker.nextNode()) {
                iterator(walker.currentNode);
            }
            iterator(null);
        };
    }
    else {
        accept = true;
        reject = false;
        return function(root, iterator) {
            var element = root;
            var tmp;
            while (element) {
                if ((tmp = element.firstChild) && filter(tmp) === accept) {
                    element = tmp;
                }
                else if (tmp = element.nextSibling) {
                    element = tmp;
                }
                else {
                    for ( ; ; ) {
                        element = element.parentNode;
                        if (element == root || !element) {
                            iterator(null);
                            return;
                        }
                        if (tmp = element.nextSibling) {
                            element = tmp;
                            break;
                        }
                    }
                }
                iterator(element);
            }
        };
    }
})();

TracWysiwyg.count = 0;
TracWysiwyg.tracBasePath = null;

TracWysiwyg.getTracBasePath = function() {
    var links = document.getElementsByTagName("link");
    var length = links.length;
    for (var i = 0; i < length; i++) {
        var link = links[i];
        var rel = (link.getAttribute("rel") || "").toLowerCase();
        var href = link.getAttribute("href") || "";
        if (rel == "stylesheet" && /^(.*)\/chrome\/common\/css\/trac\.css$/.test(href)) {
            return RegExp.$1.replace(/[\w.+-]+:\/\/[^:]+(?::\d+)?/, "") + "/";
        }
    }
    return null;
};

TracWysiwyg.getEditorMode = function() {
    if (TracWysiwyg.editorMode) {
        return TracWysiwyg.editorMode;
    }

    var mode = null;
    var cookies = (document.cookie || "").split(";");
    var length = cookies.length;
    for (var i = 0; i < length; i++) {
        var match = /^\s*tracwysiwyg=(\S*)/.exec(cookies[i]);
        if (match) {
            switch (match[1]) {
            case "wysiwyg":
                mode = match[1];
                break;
            default:    // "textarea"
                mode = null;
                break;
            }
            break;
        }
    }

    TracWysiwyg.editorMode = mode || "textarea";
    return TracWysiwyg.editorMode;
};

TracWysiwyg.setEditorMode = function(mode) {
    switch (mode) {
    case "wysiwyg":
        break;
    default:    // "textarea"
        mode = "textarea";
        break;
    }
    TracWysiwyg.editorMode = mode;

    var expires = new Date();
    expires.setTime(expires.getTime() + 365 * 86400 * 1000);
    var pieces = [ "tracwysiwyg=" + mode,
        "path=" + TracWysiwyg.tracBasePath,
        "expires=" + expires.toUTCString() ];
    document.cookie = pieces.join("; ");
};

TracWysiwyg.stopEvent = function(event) {
    if (event.preventDefault) {
        event.preventDefault();
        event.stopPropagation();
    }
    else {
        event.returnValue = false;
        event.cancelBubble = true;
    }
};

TracWysiwyg.elementPosition = function(element) {
    var left = 0, top = 0;
    while (element) {
        left += element.offsetLeft || 0;
        top += element.offsetTop || 0;
        element = element.offsetParent;
    }
    return [ left, top ];
};

TracWysiwyg.getSelfOrAncestor = function(element, name) {
    var target = element;
    name = name.toLowerCase();
    if ((target.tagName || "").toLowerCase() != name) {
        target = getAncestorByTagName(element, name);
    }
    return target;
};

TracWysiwyg.quickSearchURL = function(link) {
    if (!/^(?:(?:https?|ftp|mailto|file):|[\/.#])/.test(link)) {
        link = TracWysiwyg.tracBasePath + "search?q=" + encodeURIComponent(link);
    }
    return link;
};

TracWysiwyg.getTextContent = (function() {
    var anonymous = document.createElement("div");
    if (typeof anonymous.textContent != "undefined") {
        return function(element) { return element.textContent };
    }
    else if (typeof anonymous.innerText != "undefined") {
        return function(element) { return element.innerText };
    }
    else {
        return function(element) { return null };
    }
})();

TracWysiwyg.initialize = function() {
    if ("replace".replace(/[a-e]/g, function(m) { return "*" }) != "r*pl***") {
        return;
    }
    if (typeof document.designMode == "undefined") {
        return;
    }
    if (navigator.appVersion.indexOf("AppleWebKit/") >= 0) {
        return;
    }
    TracWysiwyg.tracBasePath = TracWysiwyg.getTracBasePath();
    if (!TracWysiwyg.tracBasePath) {
        return;
    }
    var textareas = document.getElementsByTagName("textarea");
    for (var i = 0; i < textareas.length; i++) {
        var textarea = textareas[i];
        if (/\bwikitext\b/.test(textarea.className || "")) {
            new TracWysiwyg(textarea);
        }
    }
};

TracWysiwyg.initialize();

