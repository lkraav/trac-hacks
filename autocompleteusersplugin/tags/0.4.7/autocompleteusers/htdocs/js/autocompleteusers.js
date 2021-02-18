(function($) {
    var methods = {};
    methods._create = function() {
        $.ui.autocomplete.prototype._create.apply(this, arguments);
        this.widget().addClass('tracautocompleteusers');
    };
    var itemData = function(item) {
        item = {username: item[0], email: item[1], name: item[2]};
        var label = item.name
                  ? $.format('$1 ($2)', item.username, item.name)
                  : item.username;
        item.label = label;
        item.value = item.username;
        return item;
    };
    var renderItem = function(ul, item) {
        var li = $(document.createElement('li'));
        var anchor = $(document.createElement('a'));
        anchor.text(item.label);
        if (item.email) {
            var span = $(document.createElement('span')).text(item.email);
            anchor.append(span);
        }
        li.append(anchor);
        ul.append(li);
        return li;
    };
    if ('_renderItemData' in $.ui.autocomplete.prototype) {
        methods._renderItemData = function(ul, item) {
            item = itemData(item);
            var li = renderItem(ul, item);
            li.data('ui-autocomplete-item', item);
            return li;
        };
    }
    else {
        methods._renderItem = function(ul, item) {
            item = itemData(item);
            var li = renderItem(ul, item);
            li.data('item.autocomplete', item);
            return li;
        };
    }
    $.widget('tracautocompleteusers.tracautocompleteusers',
             $.ui.autocomplete, methods);
})(jQuery);

jQuery(function($) {
    var settings = window.autocompleteusers;
    if (settings === undefined)
        return;

    var ticket_fields = function(fields) {
        fields = $.map(fields, function(val) {
            return 'input#field-' + val;
        });
        return fields.join(', ');
    };
    var multi_source = function(url) {
        return function(request, response) {
            var terms = request.term.split(/,\s*/);
            var term = terms.length === 0 ? '' : terms[terms.length - 1];
            $.getJSON(url, {term: term}, response);
        };
    };
    var single_select = function(event, ui) {
        this.value = ui.item.value;
        return false;
    };
    var multi_select = function(event, ui) {
        var terms = this.value.split(/,\s*/);
        terms.pop();
        terms.push(ui.item.value);
        terms.push('');
        this.value = terms.join(', ');
        return false;
    };
    var activate = function(target) {
        if (!target.selector)
            return;
        var options = {minLength: 0, autoFocus: true};
        var args = [];
        if (target.groups)
            args.push({name: 'groups', value: '1'});
        if (!target.users)
            args.push({name: 'users', value: '0'});
        args = args.length === 0 ? '' : '?' + $.param(args);
        var url = settings.url + args;
        if (target.multiple) {
            options.source = multi_source(url);
            options.select = multi_select;
        }
        else {
            options.source = url;
            options.select = single_select;
        }
        options.focus = function() { return false };
        $(target.selector).tracautocompleteusers(options);
    };

    var single_fields = $.merge(['owner', 'reporter'], settings.fields);
    var multi_fields = $.merge(['cc'], settings.multi_fields);
    switch (settings.template) {
    case 'ticket.html':
        activate({selector: ticket_fields(single_fields),
                  multiple: false, users: true, groups: false});
        activate({selector: ticket_fields(multi_fields),
                  multiple: true, users: true, groups: false});
        activate({selector: '#action input[id$=_reassign_owner], ' +
                            '.trac-autocomplete',
                  multiple: false, users: true, groups: false});
        activate({selector: '.trac-autocomplete-multi',
                  multiple: true, users: true, groups: false});
        break;
    case 'admin_perms.html':
        activate({selector: '#gp_subject, #sg_subject',
                  multiple: false, users: true, groups: true});
        activate({selector: '#sg_group',
                  multiple: false, users: false, groups: true});
        break;
    case 'query.html':
        $('#filters').on('focus', 'input:text', function() {
            var input = $(this);
            if (input.hasClass('ui-autocomplete-input'))
                return;
            var target = {selector: input, users: true, groups: false};
            var name = this.name.replace(/^[0-9]+_/, '');
            if ($.inArray(name, single_fields) !== -1)
                target.multiple = false;
            else if ($.inArray(name, multi_fields) !== -1)
                target.multiple = true;
            else
                return;
            activate(target);
        });
        break;
    }
});
