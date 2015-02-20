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
        connectWith: ".column_tickets",
        placeholder: "ticket_placeholder"
    })

    /* We have to store tickets status changes (id, old status and new status)
     * once the drop is done.
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
        for(var i = 0; i < actions.length; i++){
            if(actions[i].ticket == ticket){
                actions[i].to = to;
                if(!actions[i].from){
                    actions[i].from = from;
                }
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

    /* We have to store tickets fields changes (id, field name and field value)
     * once user has changed the input form for each ticket field.
     * Note that the input form id has the following format :
     * owner_ticketid or reviewer_ticketid
     */
    $("#tickets_form").change(function(event){
        //The event.target corresponds to the input form id.
        var elt = event.target;
        var elt_info = elt.id.split(/_/);

        for(var i = 0; i < actions.length; i++){
            if(actions[i].ticket == elt_info[1]){
                if(elt_info[0] == "owner"){
                    actions[i].owner = elt.value ? elt.value : "NIL";
                }
                if(elt_info[0] == "reviewer"){
                    actions[i].reviewer = elt.value ? elt.value : "NIL";
                }
                break;
            }
        }

        if(i == actions.length){
            if(elt_info[0] == "owner"){
                actions.push({
                    "ticket": elt_info[1],
                    "owner": elt.value ? elt.value : "NIL"
                });
            }
            if(elt_info[0] == "reviewer"){
                actions.push({
                    "ticket": elt_info[1],
                    "reviewer": elt.value ? elt.value : "NIL"
                });
            }
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
            //'ticket_id:owner=val&reviewer=val&status=val&+ticket_id:...'
            //Store only tickets that have really changed.
            for(var i = 0; i < actions.length; i++){
                changesValue += actions[i].ticket + ":"
                if(actions[i].owner){
                    changesValue += "owner=" + actions[i].owner + "&";
                }
                if(actions[i].reviewer){
                    changesValue += "reviewer=" + actions[i].reviewer + "&";
                }
                if(actions[i].from && actions[i].to &&
                   actions[i].from != actions[i].to){
                    changesValue += "status=" + actions[i].to + "&";
                }
                //Remove the trailing character: &
                if(changesValue[changesValue.length - 1] == "&"){
                    changesValue = changesValue.slice(0, - 1);
                }
                changesValue += "\n"
            }

            //No ticket change, so do not call html form action
            if(changesValue == ""){
                return false;
            }
            else{
                //Remove the trailing character: +
                if(changesValue[changesValue.length - 1] == "\n"){
                    changesValue = changesValue.slice(0, - 1);
                }
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
