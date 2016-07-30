jQuery(document).ready(function($) {

    function enableSave(){
       $(this).parents('form').find('input[type=submit]').removeAttr('disabled');
    };

    function enablePermissions(){
        var par = $(this).parents('form');
        if($(this).prop('checked')){
           par.find('input[name=sel]').removeAttr('disabled');
        }
        else{
           par.find('input[name=sel]').attr('disabled', 'disabled');
        };
    }
    $('input[name=use_perm]').click(enablePermissions).click(enableSave);
    $('input[name=sel]').click(enableSave);
    $('.save-button').attr('disabled', 'disabled');
});