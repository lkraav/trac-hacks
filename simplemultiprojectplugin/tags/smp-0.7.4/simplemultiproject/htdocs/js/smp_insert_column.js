jQuery(document).ready(function($) {
  /* Insert project column in given table. Data is in javascript vars. */
  $(smp_tbl_hdr['css'] + ' th:nth-of-type(2)').after(smp_tbl_hdr['html']);
  $(smp_tbl_hdr['css'] + ' tbody>tr').each(function(row){
       var the_name = $(this).find('input[name=sel]').val();
       if(the_name in smp_tbl_cols){
         $(this).children('td:nth-of-type(2)').after('<td class="' + smp_td_class + '">' + smp_tbl_cols[the_name] + '</td>');
       }else {
         $(this).children('td:nth-of-type(2)').after('<td class="' + smp_td_class + '"></td>');
       }
  });
});