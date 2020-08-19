jQuery(document).ready(function($) {
  var i;

  for(i = 0; i < smp_pref_filter.length; i++){
    var html = smp_pref_filter[i];
    if(html['pos'] === 'prepend'){
       $(html['css']).prepend(html['html'])
    }
  }
});
