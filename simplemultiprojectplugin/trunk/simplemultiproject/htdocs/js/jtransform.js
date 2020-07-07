jQuery(document).ready(function($) {
  var i;

  for(i = 0; i < smp_filter.length; i++){
    var html = smp_filter[i];
    if(html['pos'] === 'after'){
       $(html['css']).after(html['html']);
    }else {
       if(html['pos'] === 'before'){
         $(html['css']).before(html['html']);
       };
    };
  }
});
