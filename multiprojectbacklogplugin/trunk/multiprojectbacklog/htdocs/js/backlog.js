jQuery(document).ready(function($) {
   /* Ticket field selection  */
   function field_select(){
      var val = $(this).val();
      if($(this).is(':checked')){
        $('.'+val).show();
      }
      else{
        $('.'+val).hide();
      };
   };
   $('.prj-field-sel').on('click', field_select);


   function highlight_table(success){
      if(success){
        $('.ticket-tr').effect('highlight', {color: '#92e468'});
      }else{
        $('.ticket-tr').effect('highlight', {color: '#f28686'});
      };
   };

   function drop_on_tr(event, ui){
     $(this).removeClass('tr-dragover')
     var drop_tid = ui.draggable.attr('id').split('_')[1];
     var after_tid = $(this).attr('id').split('_')[1];
     var target = this;

     /* Save value  */
     $.post(mp_post_url+'/move_after',
     {ticket_id: drop_tid,
      after_ticket_id: after_tid,
      __FORM_TOKEN: mp_form_token
     }, function(data) {
                       if(data['errorcode'] == 200){
                           ui.draggable.insertAfter(target);
                           highlight_table(true);
                           ui.draggable.effect('highlight', {duration: 1200});
                       }else{
                           highlight_table(false);
                       }
     }).fail(function(){highlight_table(false);});
   };

   function drop_on_th(event, ui){
     $('.ticket-th').on('dropout', function(event, ui){$('th', this).removeClass("tr-dragover");});
     var drop_tid = ui.draggable.attr('id').split('_')[1];
     var before_tid = $('#tickets tr:first').attr('id').split('_')[1];
     var target = this;
     /* Save value  */
     $.post(mp_post_url+'/move_before',
     {ticket_id: drop_tid,
      before_ticket_id: before_tid,
      __FORM_TOKEN: mp_form_token
     }, function(data) {
                        if(data['errorcode'] == 200){
                            ui.draggable.insertBefore($('#tickets tr:first'));
                            highlight_table(true);
                            ui.draggable.effect('highlight', {duration: 1200});
                        }else{
                            highlight_table(false);
                        }
      }).fail(function(){highlight_table(false);});
   };

    function drop_on_ms(event, ui){
        $(this).removeClass('milestone-dragover');
        var drop_tid = ui.draggable.attr('id').split('_')[1];
        var target = this;
        /* Save value  */
        $.post(mp_post_url+'/assign',
        {ticket_id: drop_tid,
         milestone: $(this).attr('id'),
         __FORM_TOKEN: mp_form_token
        }, function(data) {
                          if(data['errorcode'] == 200){
                              $('#ticket_'+drop_tid).remove();
                              $('.num_tickets', target).text(data['num_tickets']);
                              highlight_table(true);
                              $(target).effect('highlight', {color: '#92e468'});

                          }else{
                              $(target).effect('highlight', {color: '#f28686'});
                              highlight_table(false);
                          }
        }).fail(function(){highlight_table(false);});
      };

   /* Drag and drop */
   $('.ticket-tr').draggable({
                               cursor: "move",
                               cursorAt: {right: 5},
                               helper: function(event){
                                 var tid = $('.id', this).text();
                                       return $('<div class="drag-ticket" style="background-color: #ddd">Ticket '+ tid +' </div>')
                                       .data('tid', tid);
                                       }
                              });

   $('.ticket-tr, .ticket-th').droppable();
   $('.ticket-tr').on('dropover', function(event, ui){$(this).addClass('tr-dragover');});
   $('.ticket-tr, .ticket-th').on('dropout', function(event, ui){$(this).removeClass('tr-dragover');});

   $('.ticket-th').on('dropover', function(event, ui){$('th', this).addClass("tr-dragover");});
   $('.ticket-th').on('dropout', function(event, ui){$('th', this).removeClass("tr-dragover");});

   $('.ticket-tr').on('drop', drop_on_tr);
   $('.ticket-th').on('drop', drop_on_th);

   /* Drop on milestone */
   $('.milestone').droppable({
                             drop: drop_on_ms
                                 });
   $('.milestone').on('dropover', function(event, ui){$(this).addClass('milestone-dragover')});
   $('.milestone').on('dropout', function(event, ui){$(this).removeClass('milestone-dragover')});

});