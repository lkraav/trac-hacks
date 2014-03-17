// Copyright (C) 2013 OpenGroove,Inc.
// All rights reserved.
//
// This software is licensed as described in the file COPYING, which
// you should have received as part of this distribution.

jQuery(document).ready(function($) {
    var randstr = function() {
        var value = Math.floor(Math.random() * 2176782335).toString(36);
        return ('000000' + value).slice(-6);
    };

    var initSortable = function(list) {
        var options = {
            revert: 200, opacity: 0.9, tolerance: 'pointer',
            placeholder: 'ticketfieldslayout-placeholder',
            connectWith: '.ticketfieldslayout-admin ul'};
        options.update = function(event, ui) {
            if (ui.sender === null)
                return;
            var item = ui.item;
            var field = item.find('input').val();
            var target = item.closest('fieldset').find('input[name=group]').val();
            if (target === '=hidden' &&
                (field === 'summary' || field === 'reporter' ||
                 field === 'owner' || field === 'description'))
            {
                ui.sender.sortable('cancel');
                return;
            }
            if (/^@/.exec(field) && target !== '') {
                ui.sender.sortable('cancel');
                return;
            }
            var name;
            switch (target) {
                case '':        name = 'field';           break;
                case '=hidden': name = '';                break;
                default:        name = 'field.' + target; break;
            }
            ui.item.find('input').attr('name', name);
        };
        list.sortable(options);
        list.find('li').disableSelection();
    };

    var form = $('form.ticketfieldslayout-admin');
    form.find('.buttons input[name=add]').click(function() {
        var id = '_' + randstr() + randstr();
        var root = form.find('.ticketfieldslayout-root');

        var items = root.find('ul');
        var item = items.find('.ticketfieldslayout-tmpl-item').clone();
        var label = item.find('span').text();
        item.find('[name=field]').val('@' + id);
        item.find('input').removeAttr('disabled');
        item.removeClass('ticketfieldslayout-tmpl-item');
        items.prepend(item);

        var group = form.find('.ticketfieldslayout-tmpl-group').clone();
        group.find('[name=group]').val(id);
        group.find('[name=label]').attr('name', 'label.' + id).val(label);
        group.find('[name=collapsed]').attr('name', 'collapsed.' + id);
        group.find('input').removeAttr('disabled');
        group.removeClass('ticketfieldslayout-tmpl-group');
        root.after(group);
        group.find(':text').select().focus();
        initSortable(group.find('ul'));

        return false;
    });
    form.delegate('.ticketfieldslayout-remove', 'click', function() {
        var group = $(this).closest('fieldset');
        var id = group.find('legend input[type=text]').attr('name');
        id = '@' + id.replace(/^label\./, '');
        var items = group.find('li');
        items.find('input').attr('name', 'field');
        var root = form.find('.ticketfieldslayout-root');
        form.find('input[name=field]').each(function() {
            if (this.value === id) {
                $(this).closest('li').before(items).remove();
                return false;
            }
        });
        group.remove();
        return false;
    });
    form.delegate('legend input[type=text]', 'keyup change', function() {
        var id = '@' + this.name.replace(/^label\./, '');
        var text = this.value;
        form.find('.ticketfieldslayout-root input[name=field]').each(function() {
            if (this.value === id) {
                $(this).closest('li').find('span').text(text);
                return false;
            }
        });
    });
    initSortable(form.find('ul'));
});
