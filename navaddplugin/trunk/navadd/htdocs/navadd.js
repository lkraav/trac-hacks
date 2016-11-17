jQuery(document).ready(function(){
    $('#mainnav ul li a').each(function() {
        var currentPath = location.pathname + location.search;
        if ($(this).attr('href') == currentPath) {
               $('#mainnav ul li.active').removeClass('active');
               $(this).parent().addClass('active');
        }
    });
});
