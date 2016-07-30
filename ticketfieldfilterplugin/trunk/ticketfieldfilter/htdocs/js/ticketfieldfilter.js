jQuery(document).ready(function($) {

    function typeChange(){
           $('#propertyform input[name=__FORM_TOKEN').remove();
           var data = $('#propertyform').serialize();
           data = data.replace(/field_/g, '');
           window.location.replace('newticket?' + data);
    };

    if(tff_newticket == 1){
        $('select[id=field-type]').change(typeChange);
    };
});