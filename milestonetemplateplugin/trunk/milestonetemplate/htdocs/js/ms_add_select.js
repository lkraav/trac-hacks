jQuery(document).ready(function($) {
  var i;

  for(i = 0; i < ms_filter.length; i++){
    var html = ms_filter[i];
    if(html['pos'] === 'before'){
       $(html['css']).before(html['html'])
    }
    else{
       $(html['css']).after(html['html'])
    };
  }
});
