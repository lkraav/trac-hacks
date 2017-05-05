(function($) {
    if (window.tracflexiblequeryui === undefined)
        return;
    var html = $('html');
    var fields = tracflexiblequeryui.fields;
    $.each(fields, function(idx, field) {
        if (!field.enabled)
            html.addClass('tracflexiblequeryui-disabled-' + field.name);
    });
    var selectors = $.map(fields, function(field) {
        return $.format('.tracflexiblequeryui-disabled-$name ' +
                        'table.tickets tr > .$name', {name: field.name});
    });
    var style = $('<style id="tracflexiblequeryui-style" type="text/css">' +
                  '</style>');
    style.text(
        '#columns div.ui-sortable label { display: inline-block; ' +
            'float: none; line-height: 2em; white-space: nowrap; ' +
            'padding: 0; margin: 0 }\n' +
        '#columns div.ui-sortable label .handle { ' +
            'display: inline-block; cursor: move; visibility: ' +
            'hidden; vertical-align: middle }\n' +
        '#columns div.ui-sortable label:hover .handle { ' +
            'visibility: visible }\n' +
        selectors.join(', ') + ' { display: none }');
    style.appendTo('head');
})(jQuery);

jQuery(document).ready(function($) {
    if (window.tracflexiblequeryui === undefined)
        return;

    var data = tracflexiblequeryui;
    var container = $('#columns div');
    var replace_col_args = function() {
        var col_args = ['col=id'];
        container.find('label input').filter(':checked')
                 .each(function() { col_args.push('col=' + this.value) });
        var elements = $(
            '#content .paging a, #content .trac-columns a, #altlinks a, ' +
            'link[rel=alternate], link[rel=next], link[rel=prev]');
        elements.each(function() {
            var href = this.getAttribute('href');
            var pos = href.indexOf('?');
            if (pos === -1)
                return;
            var args = href.substring(pos + 1).split(/&/g);
            args = $.grep(args, function(arg) { return !/^col=/.test(arg) });
            args.push.apply(args, col_args);
            this.href = href.substring(0, pos) + '?' + args.join('&');
        });
    };
    var initialize = function() {
        var labels = {}
        container.children('label').each(function() {
            var name = $(this).children('input').attr('value');
            labels[name] = this;
        });
        $.each(data.fields, function(idx, field) {
            container.append(labels[field.name], ' ');
        });
        container.children('label').each(function() {
            $('<span class="handle ui-icon ui-icon-arrow-4"></span>')
            .appendTo(this);
        });
    };

    initialize();
    container.on('click', 'label input', function() {
        var name = this.value;
        $('html').toggleClass('tracflexiblequeryui-disabled-' + name,
                              !this.checked);
        replace_col_args();
    });
    var options = {items: '> label', handle: '> span.handle'};
    options.start = function(event, ui) {
        var placeholder = $(ui.placeholder);
        placeholder.css('height', '1em');
    };
    options.stop = function(event, ui) {
        var rows = $('#content table.tickets')
                   .children('thead, tbody').children('tr');
        var columns = $(rows[0]).children('th').map(function() {
            var class_ = this.className;
            return class_ === 'batchmod_selector sel' || class_ === 'id' ?
                   '' : this.className.split(/\s/)[0];
        });
        var columns_idx = {};
        $.each(columns, function(idx, name) { columns_idx[name] = idx });
        var labels = container.find('> label input')
                     .map(function() { return this.value });
        labels = $.grep(labels, function(name) { return name in columns_idx });
        var name = $(ui.item).children('input').attr('value');
        var label_idx = $.inArray(name, labels);
        var last = label_idx === labels.length - 1;
        var dst = labels[last ? labels.length - 2 : label_idx + 1];
        var src_idx = columns_idx[name];
        var dst_idx = columns_idx[dst];
        rows.each(function() {
            var cells = $(this).children('th, td');
            var method = last ? 'insertAfter' : 'insertBefore';
            $(cells[src_idx])[method](cells[dst_idx]);
        });
        replace_col_args();
    };
    container.sortable(options);
});
