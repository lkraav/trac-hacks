jQuery(document).ready(function($) {
  var i;

  for(i = 0; i < smp_filter.length; i++){
    var html = smp_filter[i];
    console.log('filter ', html['pos']);
    if(html['pos'] === 'after'){
       $(html['css']).after(html['html']);
    }else {
       if(html['pos'] === 'before'){
         $(html['css']).before(html['html']);
       } else {
         if(html['pos'] === 'prepend'){
           $(html['css']).prepend(html['html']);
         }
       };
    };
  }
});
