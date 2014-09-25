(function($){

    // Custom FullCalendar view rendering of multiple weeks:
    $.fullCalendar.views.multiWeek = MultiWeekView;
    function MultiWeekView(element, calendar) {
        var t = this;
        
        // exports
        t.incrementDate = incrementDate;
        t.render = render;
        
        // imports
        $.fullCalendar.BasicView.call(t, element, calendar, 'multiWeek');
        var opt = t.opt;
        var renderBasic = t.renderBasic;
        var skipHiddenDays = t.skipHiddenDays;
        var getCellsPerWeek = t.getCellsPerWeek;
        var formatRange = calendar.formatRange;
        
        function incrementDate(date, delta) {
            return date.clone().stripTime().add('days', delta * 7);
        }
    
        function render(date) {
            var weeks = opt('weeks');
            var start = date.clone().stripTime().subtract('days', (date.day() - opt('firstDay') + 7) % 7);
            var end = start.clone().add('days', weeks * 7);

            t.intervalStart = start;
            t.intervalEnd = end;
            
            t.start = t.skipHiddenDays(t.intervalStart);
            t.end = t.skipHiddenDays(t.intervalEnd, -1, true);

            var colCnt = getCellsPerWeek();
            var rowCnt = weeks;

            t.title = formatRange(
                t.start,
                t.end.clone().subtract(1), // make inclusive by subtracting 1 ms
                opt('titleFormat'),
                ' \u2014 ' // emphasized dash
            );
            
            renderBasic(rowCnt, colCnt, 'multiWeek');
        }
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
    $(document).delegate('.trac-weekplan-dialog', 'keydown', function(e) {
        var tagName = e.target.tagName.toLowerCase();
        tagName = (tagName === 'input' && e.target.type === 'button') ? 'button' : tagName;
        if (e.which === $.ui.keyCode.ENTER && tagName !== 'textarea' && tagName !== 'select' && tagName !== 'button') {
            $(this).find('.ui-dialog-buttonset button').eq(0).trigger('click');
            return false;
        }
    });
    
    $(window).load(function() {
        $('.trac-weekplan').each(function (index) {
            var plan_data = window['weekplan_' + this.id.slice(-12)];
            var calendar_data = plan_data.calendar_data;
            
            calendar_data.defaultDate = moment(calendar_data.defaultDate);
            calendar_data.allDayDefault = true;

            calendar_data.eventDataTransform = function(event) {
                event.color = plan_data.colors[event.plan];
                return event;
            };

            calendar_data.eventRender = function(event, element, view) {
                $(element).children(".fc-event-inner").html(event.title_html);
                $(element).find("a").click(function(ev) {
                    ev.stopPropagation();
                });
            };

            // Create event
            if (plan_data.plans_with_add_event.length > 0) {
                var createDialog = $("<div title='Create event'><form><label>Title: <input type='text' name='title' /></label><br/><label>Plan: <select name='plan' /></label></form></div>");
                var ctrlCreateTitle = createDialog.find("input[name='title']");
                var ctrlCreatePlan = createDialog.find("select[name='plan']");
                $.each(plan_data.plans_with_add_event, function(i, plan) {
                        $('<option/>', { 'value': plan }).text(plan_data.labels[plan]).css('background-color', plan_data.colors[plan]).appendTo(ctrlCreatePlan);
                    });

                calendar_data.selectable = true;
                calendar_data.selectHelper = true;
                calendar_data.select = function(start, end, allDay) {
                    ctrlCreateTitle.val('');
                    createDialog.dialog({
                        modal: true,
                        dialogClass: "trac-weekplan-dialog",
                        buttons: {
                            "Create": function() {
                                var proposed_event = {
                                    title: ctrlCreateTitle.val(),
                                    plan: ctrlCreatePlan.find("option:selected").val(),
                                    start: start,
                                    end: end
                                };
                                var post_data = serialized_post_data(proposed_event, 'add_event', plan_data);
                                var current_dialog = $(this);
                                $.post(plan_data.api_url, post_data, function(added_event) {
                                    added_event.color = plan_data.colors[added_event.plan];
                                    calendar.fullCalendar('renderEvent', added_event);
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
            }

            // Drag/drop/resize event
            calendar_data.editable = true;
            calendar_data.eventStartEditable = true;
            calendar_data.eventDurationEditable = true;
            calendar_data.eventDrop = function(event, delta, revertFunc, jsEvent, ui, view) {
                if ($.inArray(event.plan, plan_data.plans_with_update_event) == -1)
                {
                    revertFunc();
                    return;
                }

                var post_data = serialized_post_data(event, 'update_event', plan_data);
                $.ajax({
                    type: "POST",
                    url: plan_data.api_url,
                    data: post_data,
                    error: revertFunc
                });
            };
            calendar_data.eventResize = function(event, delta, revertFunc, jsEvent, ui, view) {
                if ($.inArray(event.plan, plan_data.plans_with_update_event) == -1)
                {
                    revertFunc();
                    return;
                }

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
            $.each(plan_data.plans_with_update_event, function(i, plan) {
                    $('<option/>', { 'value': plan }).text(plan_data.labels[plan]).css('background-color', plan_data.colors[plan]).appendTo(ctrlEditPlan);
                });

            calendar_data.eventClick = function(edited_event) {
                if ($.inArray(edited_event.plan, plan_data.plans_with_update_event) == -1) return;

                var buttons = {
                    "Edit": function() {
                        var post_data = serialized_post_data(edited_event, 'update_event', plan_data);
                        post_data.title = ctrlEditTitle.val();
                        post_data.plan = ctrlEditPlan.find("option:selected").val();
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
                };
                if ($.inArray(edited_event.plan, plan_data.plans_with_delete_event) == -1)
                {
                    delete buttons["Delete!"];
                }

                ctrlEditTitle.val(edited_event.title);
                ctrlEditPlan.val(edited_event.plan).prop('selected',true);
                eventEditDialog.dialog({
                    modal: true,
                    dialogClass: "trac-weekplan-dialog",
                    buttons: buttons,
                });
            };

            var calendar = $(this).empty().removeClass('system-message');
            calendar.fullCalendar(calendar_data);
        });
    });
 })(jQuery);
