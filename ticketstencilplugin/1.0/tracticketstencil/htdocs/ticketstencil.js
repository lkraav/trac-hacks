$(function() {
    $('#field-type').change(function () {
        var prev_type = $(this).data('prev') || '_ticketstencil_default_type';
        var prev_desc = $('#field-description').val().trim().replace(/\r\n/g, "\n");
        var new_type = $('#field-type option:selected').val().toLowerCase();
        var can_replace =
            prev_desc == "" ||
            prev_desc == _tracticketstencil[prev_type].trim().replace(/\r\n/g, "\n");
        $(this).data('prev', new_type);
        if (can_replace) {
            $('#field-description').val(_tracticketstencil[new_type]);
        }
    });
    $('#field-type').change();
});
