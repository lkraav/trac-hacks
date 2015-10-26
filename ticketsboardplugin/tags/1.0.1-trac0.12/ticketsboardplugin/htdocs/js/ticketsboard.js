/*
 * Copyright (c) 2013 Jean-Philippe Save
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in
 * all copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 */

jQuery(document).ready(function($){

    var actions = new Array();

    /* Each status column is considered as a sortable list given by JQuery-ui.
     * Thus, each "ticket box" can be draggable/droppable from one column to
     * another. So, we will be able to change "graphically" a ticket status.
     */
    $(".column_tickets").sortable({
        connectWith: '.column_tickets',
        placeholder: 'ticket_placeholder'
    })

    /* We have to store tickets changes (id, old status and new status) once
     * the drop is done.
     * To retrieve informations we used id fields of html tags.
     * For ticket id: we use the "ticket_box" id which content ticket id.
     * For status: we use "column_tickets" id which is the status name.
     */
    $(".column_tickets").bind("sortreceive", function(event, ui){
        var ticket = /(ticket_box_)(\d+)/.exec(ui.item.attr("id"))[2];
        var from = ui.sender.context.id;
        var to = event.currentTarget.id;

        //Check if this ticket has already been moved, to thus, store only the
        //new status.
        for(var i=0; i<actions.length; i++){
            if(actions[i].ticket == ticket){
                actions[i].to = to;
                break;
            }
        }

        //Store complete informations for a new ticket.
        if(i == actions.length){
            actions.push({
               "ticket": ticket,
                "from": from,
                "to": to
            });
        }
    });

    /* User has pushed the submit button to save changes.
     * We have to store collected informations about ticket changes during the
     * drag/drop in the variable "ticketsboard_changes". Thus this variable
     * could be interpreted by the trac request process after the html form
     * action.
     */
    $("#ticketsboard_form").submit(function(){
        try{
            var changesValue = "";

            //Set changes with the following format:
            //'ticket_id:new_status,ticket_id:new_status,...'
            //Store only tickets that have really changed.
            for(var i=0; i<actions.length; i++){
                if(actions[i].from != actions[i].to){
                    changesValue += actions[i].ticket + ":" +
                                    actions[i].to + ",";
                }
            }

            //No ticket change, so do not call html form action
            if(changesValue == ""){
                return false;
            }
            else{
                $("#ticketsboard_changes").val(changesValue);
            }
            return true;
        }
        catch(e){
            alert(e);
            return false;
        }
    });
});
