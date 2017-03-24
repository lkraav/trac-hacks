$(function() {
    $(document).find('table.code tr th a').each(function(){
        $(this).attr('title', 'Double click to create a ticket');
        var cls = $(this).attr('class');
        $(this).attr('class', cls == null ? 'citecode' : cls + ' citecode');
    });

    $('a.citecode').dblclick(function() {
        var path = $(location).attr('pathname');
        var query = $(location).attr('search');
        var line = $(this).attr('href').substr(2); // drop "#L"
        query = query == "" ? "?L=" + line : query + "&L=" + line;
        query += '&path=' + path.match('/.*\/browser(\/.*)')[1]
        window.open(_traccitecode.newticket + query, '_blank');
    });
});
