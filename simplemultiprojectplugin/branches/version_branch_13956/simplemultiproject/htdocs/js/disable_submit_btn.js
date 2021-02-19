jQuery(document).ready(function($) {

    function anyChecked(){
        /* Any project selected ?*/
        var any = false;
        $(smp_input_control).each(function(){
            if (this.checked) {
                any = true;
            };
        });
        return any;
    };

    if(!anyChecked())
    {
        $(smp_submit_btn).attr('disabled', 'disabled');
    };

    $(smp_input_control).change(function() {
        if(!anyChecked()){
            $(smp_submit_btn).attr('disabled', 'disabled');
        }
        else{
            $(smp_submit_btn).removeAttr('disabled');
        };
    });

});
