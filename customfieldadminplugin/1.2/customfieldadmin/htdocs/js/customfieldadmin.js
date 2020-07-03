/**********
* User Interface function for Trac Custom Field Admin plugin.
* License: BSD
* (c) 2007-2009 ::: www.Optaros.com (cbalan@optaros.com)
**********/
(function($){
    function toggle_options(type_element){
        function label(property){ return $(property).parents('div.field') }
        function capitalize(word){
            return word[0].toUpperCase()+word.slice(1).toLowerCase();
        }
        function setOptions(type) {
          var $format = $('#format');
          $format.find('option').remove();
          var formats = field_formats[type];
          for (var i=0; i<formats.length; ++i) {
            $format.append($('<option>', {
              value: formats[i],
              text: capitalize(formats[i]),
            }));
          }
        }
        switch (type_element.selectedIndex) {
            case 0: // text
                label('#options, #rows').hide();
                label('#format').show();
                setOptions('text');
                break;
            case 1: // select
                label('#options').show();
                label('#rows, #format').hide();
                break;
            case 2: // checkbox
                label('#options, #rows, #format').hide();
                break;
            case 3: // radio
                label('#options').show();
                label('#rows, #format').hide();
                break;
            case 4: // textarea
                label('#options').hide();
                label('#rows, #format').show();
                setOptions('textarea');
                break;
            case 5: // time
                label('#options, #rows').hide();
                label('#format').show();
                setOptions('time');
                break;
        }
    }

    $(function(){
        $('#type').each(function(){
            toggle_options(this);
            $(this).change(function(){
                toggle_options(this);
            });
        });
    });
})(jQuery);
