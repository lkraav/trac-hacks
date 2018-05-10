(function($) {

    $(document).ready(function () {

        $('textarea[columns]').each(function (index, element) {

            $(element).parents('td.col1').wrapInner('<div style="display: none;"></div>');

            var table = $('<table/>').addClass('fieldoftable').addClass('wiki').attr('for', element.id);
            var rows = $(element).val().split('\n');
            var colcount = 0;

            for (var j in rows[0].split('||')) {
                if (rows[0].split('||')[j].replace(' ') != '') colcount++;
            }

            table.data('colcount', colcount);

            for (var i in rows) {
                var row = rows[i];
                var tr = $('<tr/>').addClass('fot-row');

                for (var j in row.split('||')) {

                    var col = row.split('||')[j];

                    if (col.replace(' ') != '') {
                        if (col.match(/=(.+)=/)) {
                            var td = $('<th>' + col.match(/=(.+)=/)[1] + '</th>');

                            tr.append(td);
                        } else {
                            var td = $('<td><input type="text" value="' + col + '" /></td>');
                            td.children().change(cellChanged);
                            tr.append(td);
                        }
                    }
                }

                if (i == 0) tr.append($('<th/>'));
                else tr.append(createExtraColumn());

                table.append(tr);
            }

            var tr = $('<tr/>').addClass('fot-row');
            for (var i = 0; i < colcount; i++) {
                var td = $('<td><input type="text" value="" /></td>');

                td.children().change(cellChanged);
                //td.children().focus(cellFocused);
                //td.children().blur(cellBlurred);

                tr.append(td);

            }

            tr.append(createExtraColumn());
            table.append(tr);

            $(element).parents('td.col1').append(table);

        })

    });

    function createExtraColumn() {
        var extraColumn = $('<td/>').addClass('fot-extra-column');
        extraColumn.append($('<div class="fot-insert-row">«</div>' +
                             '<div class="fot-delete-row">×</div>'));
        extraColumn.children('.fot-insert-row').click(insertRow);
        extraColumn.children('.fot-delete-row').click(deleteRow);
        return extraColumn;
    }

    function updateResult(table) {
        var result = [];

        table.find('tr').each(function (index1, element) {
            var line = [];

            $(element).children('th, td').each(function (index2, element2) {
                if (element2.tagName == 'TH' && $(element2).text() != '' && index1 == 0) {
                    line.push('=' + $(element2).text() + '=');
                } else if (!$(element2).hasClass('fot-extra-column') && index1 != 0) {
                    line.push($(element2).children().val());
                }
            });

            result.push('||' + line.join('||') + '||');
        });

        var last = result[result.length - 1];
        if (last.replace(/\|\|/g, '').trim() == '') result.splice(result.length - 1);

        var value = result.join("\n");

        $('#' + table.attr('for')).val(value);
    }

    function cellChanged() {
        var table = $(this).parents('.fieldoftable');
        updateResult(table);

        if ($(this).parents('tr.fot-row').is(':last-child')) {

            var colcount = table.data('colcount');

            var tr = $('<tr/>').addClass('fot-row');
            for (var i = 0; i < colcount; i++) {
                var td = $('<td><input type="text" value="" /></td>');

                td.children().change(cellChanged);
                //td.children().focus(cellFocused);
                //td.children().blur(cellBlurred);

                tr.append(td);
            }

            tr.append(createExtraColumn());

            table.append(tr);
        }
    }

    function deleteRow() {
        var table = $(this).parents('.fieldoftable');
        var tr = $(this).parents('.fot-row');
        tr.remove();
        updateResult(table);
    }

    function insertRow() {
        var table = $(this).parents('.fieldoftable');
        var tr = $(this).parents('.fot-row');
        var colcount = table.data('colcount');

        var newRow = $('<tr/>').addClass('fot-row');
        for (var i = 0; i < colcount; i++) {
            var td = $('<td><input type="text" value="" /></td>');

            td.children().change(cellChanged);
            //td.children().focus(cellFocused);
            //td.children().blur(cellBlurred);

            newRow.append(td);
        }

        newRow.append(createExtraColumn());
        tr.before(newRow);
        updateResult(table);
    }

    function cellFocused() {
        var tr = $(this).parents('.fot-row');
        var extraColumn = tr.children('.fot-extra-column');
        extraColumn.css('display', 'table-cell');
    }

    function cellBlurred() {
        var tr = $(this).parents('.fot-row');
        var extraColumn = tr.children('.fot-extra-column');
        extraColumn.css('display', 'none');
    }

})(jQuery);