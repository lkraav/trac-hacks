jQuery(document).ready(function($) {
  function apply_transform(filter_list){
      var i;
      for(i = 0; i < filter_list.length; i++){
        var html = filter_list[i];
        switch(html['pos']){
          case 'after':
            $(html['css']).after(html['html']);
            break;
          case 'append':
            $(html['css']).append(html['html']);
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
          case 'replace':
            $(html['css']).replaceWith(html['html']);
            break;
          default:
            break;
        };
      } // for
  };

  if(typeof tff_filter !== 'undefined'){
      apply_transform(tff_filter);
  };
});
