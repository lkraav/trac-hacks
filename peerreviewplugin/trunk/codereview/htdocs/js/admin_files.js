
jQuery(document).ready(function($) {
   var cur_repo_path = repo_browser;

    /* Called after browser is loaded */
    function create_browser_link(){
       $('#repo_browser .dir, #repo_browser .file,#repo_browser .parent,#repo_browser .pathentry, .link_repo_idx').each(function(idx){
          var url = $(this).attr('href');
          $(this).on("click", function(){
              /* Reset line selection stuff */
              cur_repo_path = url;
              load_browser(url);
              return false;});
       });
       $('#addfiles').on('click', function(){
            $('.fileselect:checked').each(function(idx){
                 /* $('#fileRevVal').val($(this).data('rev')); */
                 addFile($(this).val());
                 });
       });
    };

    function switch_rev(event){
      if ( event.which == 13 ) {
          if($('#switch_rev').val() != ""){
             load_browser(cur_repo_path.split('?')[0]+"?rev="+$('#switch_rev').val()+'&repo='+$('#reponame').val());
             event.preventDefault();
          }
          else{
             load_browser(cur_repo_path.split('?')[0]+'?repo='+$('#reponame').val());
             event.preventDefault();
          };
      };
    };

    function changeRepo(){
        load_browser($(this).val()+'&rev='+encodeURIComponent($('#switch_rev').val()));
    };

    function load_browser(url){
      $('#repo_browser').load(url, function(){
           create_browser_link();
           $('#repo_browser #switch_rev').on('keypress',switch_rev);
           $('#sel_repo').on('change', changeRepo);
           $('#rootfolder').val($('#root_path').val());
      });
    };

    if(show_repo_idx){
        load_browser(repo_browser.split('?')[0]);
    }
    else{
        load_browser(repo_browser);
    };
});