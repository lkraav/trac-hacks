jQuery(document).ready(function($) {

    function enableSave(){
        var t = $(this).parents('form').attr('id').split('_');
        $('#' + t[0] + '_save').removeAttr('disabled');
    };

    $('input[name=sel]').click(enableSave);
    $('input[name=readonly]').click(enableSave);
    $('input[name=save]').attr('disabled', 'disabled');
});