jQuery(document).ready(function($) {
  var i;

  for(i = 0; i < smp_filter.length; i++){
    var html = smp_filter[i];
    switch(html['pos']){
      case 'after':
        $(html['css']).after(html['html']);
        break;
      case 'before':
        $(html['css']).before(html['html']);
        break;
      case 'prepend':
        $(html['css']).prepend(html['html']);
        break;
      case 'remove':
        $(html['css']).remove();
        break;
      default:
        break;
    };
  } // for
});
