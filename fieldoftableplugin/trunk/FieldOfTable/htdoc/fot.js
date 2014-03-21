$(document).ready( function () {

    $('textarea[columns]').each( function (index, element) {

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

            var tr = $('<tr/>').addClass('fieldoftableline');

            for (var j in row.split('||')) {

                var col = row.split('||')[j];

                if (col.replace(' ') != '') {

                    if (col.match(/=(.+)=/))
                    {
                        var td = $('<th>' + col.match(/=(.+)=/)[1] + '</th>');

                        tr.append(td);
                    } else {
                        var td = $('<td><input type="text" value="' + col + '" /></td>');

                        td.children().change(fieldOfTableChange);

                        tr.append(td);
                    }

                    tr.append(td);
                }

            }

            table.append(tr);
        }

        var tr = $('<tr/>').addClass('lastline').addClass('fieldoftableline');
        for (var i = 0; i < colcount; i++)
        {
            var td = $('<td><input type="text" value="" /></td>');

            td.children().change(fieldOfTableChange);

            tr.append(td);
        }
        table.append(tr);

        $(element).parents('td.col1').append(table);

    })

});

function fieldOfTableChange() {
    var table = $(this).parents('.fieldoftable');
    var result = [];

    table.find('tr').each(function (index, element) {
        var line = [];

        $(element).children('th, td').each(function (index, element2) {
            if (element2.tagName == 'TH') {
                line.push('=' + $(element2).text() + '=');
            } else {
                line.push($(element2).children().val() + ' ');
            }
        });

        result.push('||' + line.join('||') + '||');
    });

    $('#' + table.attr('for')).val(result.join("\n"));

    if ($(this).parents('tr.fieldoftableline').hasClass('lastline')) {
        $(this).parents('tr.fieldoftableline').removeClass('lastline');

        var colcount = table.data('colcount');

        var tr = $('<tr/>').addClass('lastline').addClass('fieldoftableline');
        for (var i = 0; i < colcount; i++)
        {
            var td = $('<td><input type="text" value="" /></td>');

            td.children().change(fieldOfTableChange);

            tr.append(td);
        }
        table.append(tr);
    }
}