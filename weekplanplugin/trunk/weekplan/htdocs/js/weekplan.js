(function($){
    function deserialize_event(event) {
        event.start = new Date(event.start);
        event.end = new Date(event.end);
        event.allDay = true; // (changes meaning of "end" date!)
    }
    
    function serialized_post_data(event, action, plan_data) {
        return {
                "__FORM_TOKEN": plan_data.form_token,
                action: action,
                id: event.id,
                plan: event.plan,
                title: event.title,
                start: event.start.toISOString(),
                end: (event.end || event.start).toISOString()
        };
    }

    // Fix jQuery UI Dialogs. Pressing enter should "click the first button", not submit the form (with GET and a page refresh!)
    // See http://stackoverflow.com/questions/868889/submit-jquery-ui-dialog-on-enter
    $(document).delegate('.ui-dialog', 'keydown', function(e) {
        var tagName = e.target.tagName.toLowerCase();
        tagName = (tagName === 'input' && e.target.type === 'button') ? 'button' : tagName;
        if (e.which === $.ui.keyCode.ENTER && tagName !== 'textarea' && tagName !== 'select' && tagName !== 'button') {
            $(this).find('.ui-dialog-buttonset button').eq(0).trigger('click');
            return false;
        }
    });
    
    $(document).ready(function() {
        $('.trac-weekplan').each(function (index) {
            var plan_data = window['weekplan_' + this.id.slice(-12)];
            var calendar_data = plan_data.calendar_data;

            $.each(calendar_data.events, function(i, e) { deserialize_event(e); });

            calendar_data.eventRender = function(event, element, view) {
                $(element).children(".fc-event-inner").html(event.title_html);
                $(element).find("a").click(function(ev) {
                    ev.stopPropagation();
                });
            };

            // Create event
            var createDialog = $("<div title='Create event'><form><label>Title: <input type='text' name='title' /></label><br/><label>Plan: <select name='plan' /></label></form></div>");
            var ctrlCreateTitle = createDialog.find("input[name='title']");
            var ctrlCreatePlan = createDialog.find("select[name='plan']");
            $.each(plan_data.plans, function(i, plan) {
                    $('<option/>', { 'value': plan }).text(plan).css('background-color', plan_data.colors[plan]).appendTo(ctrlCreatePlan);
                });

            calendar_data.selectable = true;
            calendar_data.selectHelper = true;
            calendar_data.select = function(start, end, allDay) {
                ctrlCreateTitle.val('');
                createDialog.dialog({
                    modal: true,
                    buttons: {
                        "Create": function() {
                            var proposed_event = {
                                title: ctrlCreateTitle.val(),
                                plan: ctrlCreatePlan.find("option:selected").text(),
                                start: start,
                                end: end
                            };
                            var post_data = serialized_post_data(proposed_event, 'add_event', plan_data);
                            var current_dialog = $(this);
                            $.post(plan_data.api_url, post_data, function(added_event) {
                                deserialize_event(added_event);
                                added_event.color = plan_data.colors[added_event.plan];
                                calendar.fullCalendar('renderEvent', added_event,
                                    true); // make the event "stick"
                                current_dialog.dialog("close");
                              }, 'json');
                        },
                        "Cancel": function() {
                            $(this).dialog("close");
                        }
                    }
                });
                calendar.fullCalendar('unselect');
            };
            
            // Drag/drop/resize event
            calendar_data.editable = true;
            calendar_data.eventStartEditable = true;
            calendar_data.eventDurationEditable = true;
            calendar_data.eventDrop = function(event, dayDelta, minuteDelta, allDay, revertFunc, jsEvent, ui, view ) {
                var post_data = serialized_post_data(event, 'update_event', plan_data);
                $.ajax({
                    type: "POST",
                    url: plan_data.api_url,
                    data: post_data,
                    error: revertFunc
                });
            };
            calendar_data.eventResize = function(event, dayDelta, minuteDelta, revertFunc, jsEvent, ui, view) {
                var post_data = serialized_post_data(event, 'update_event', plan_data);
                $.ajax({
                    type: "POST",
                    url: plan_data.api_url,
                    data: post_data,
                    error: revertFunc
                });
            };

            // Click event (edit / delete)
            var eventEditDialog = $("<div title='Edit event'><form><label>Title: <input type='text' name='title' /></label><br/><label>Plan: <select name='plan' /></label></form></div>");
            var ctrlEditTitle = eventEditDialog.find("input[name='title']");
            var ctrlEditPlan = eventEditDialog.find("select[name='plan']");
            $.each(plan_data.plans, function(i, plan) {
                    $('<option/>', { 'value': plan }).text(plan).css('background-color', plan_data.colors[plan]).appendTo(ctrlEditPlan);
                });

            calendar_data.eventClick = function(edited_event) {
                ctrlEditTitle.val(edited_event.title);
                ctrlEditPlan.val(edited_event.plan).prop('selected',true);
                eventEditDialog.dialog({
                    modal: true,
                    buttons: {
                        "Edit": function() {
                            var post_data = serialized_post_data(edited_event, 'update_event', plan_data);
                            post_data.title = ctrlEditTitle.val();
                            post_data.plan = ctrlEditPlan.find("option:selected").text();
                            var current_dialog = $(this);
                            $.post( plan_data.api_url, post_data, function(updated_event) {
                                
                                edited_event.title_html = updated_event.title_html;
                                edited_event.title = updated_event.title;
                                edited_event.plan = updated_event.plan;
                                edited_event.color = plan_data.colors[updated_event.plan];
                                calendar.fullCalendar('updateEvent', edited_event);
                                current_dialog.dialog("close");
                            });
                        },
                        "Delete!": function() {
                            var post_data = serialized_post_data(edited_event, 'delete_event', plan_data);
                            var current_dialog = $(this);
                            $.post( plan_data.api_url, post_data, function(data) {
                                calendar.fullCalendar('removeEvents', edited_event.id);
                                current_dialog.dialog("close");
                            });
                        },
                        "Cancel": function() {
                            $(this).dialog("close");
                        }
                    }
                });
            };

            var calendar = $(this).empty().removeClass('system-message').fullCalendar(calendar_data);

        });
    });
 })(jQuery);
