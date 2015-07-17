jQuery(document).ready(function($) {

    // Fix jQuery UI Dialogs. Pressing enter should "click the first button", not submit the form (with GET and a page refresh!)
    // See http://stackoverflow.com/questions/868889/submit-jquery-ui-dialog-on-enter
    $(document).delegate('.trac-cards-dialog', 'keydown', function(e) {
        var tagName = e.target.tagName.toLowerCase();
        tagName = (tagName === 'input' && e.target.type === 'button') ? 'button' : tagName;
        if (e.which === $.ui.keyCode.ENTER && tagName !== 'textarea' && tagName !== 'select' && tagName !== 'button') {
            $(this).find('.ui-dialog-buttonset button').eq(0).trigger('click');
            return false;
        }
    });

    function serialized_post_data(card, action, board_data) {
        return {
                "__FORM_TOKEN": board_data.form_token,
                action: action,
                id: card.id,
                stack: card.stack,
                rank: card.rank,
                title: card.title,
                stack_version: board_data.stacks_by_name[card.stack].version,
                old_stack_name: card.stack,
                old_stack_version: board_data.stacks_by_name[card.stack].version
        };
    }

    function show_error(xhr, textStatus, errorThrown) {
        alert($.parseJSON(xhr.responseText)['message']);
    }
    
    function add_card_element($stack_sorter, card) {
        var $card_slot = $("<div class='trac-card-slot'><div class='trac-card'></div></div>");
        var $card_element = $card_slot.find(".trac-card");
        $card_element.attr('id', 'trac-card-' + card.id);
        $card_element.html(card.title_html);
        $card_element.dblclick(showEditCardDialog);
        $stack_sorter.append($card_slot);
    }
    
    function add_card_elements($stacks_element, data) {
        var $sorters = $stacks_element.find(".trac-cards-stack-sorter");
        $sorters.empty();
        $.each(data.cards_by_id, function(id, card) {
            var $stack_sorter = $stacks_element.find('#trac-card-stack-' + card.stack).children('.trac-cards-stack-sorter');
            add_card_element($stack_sorter, card);
        });
    }
    
    function get_board_data($element) {
        var $board_element = $element.parents('.trac-cards-board');
        return window['cards_' + $board_element.get(0).id.slice(-12)];
    }
    
    function get_stack_name($element) {
        var $stack_element = $element.parents('.trac-cards-stack');
        return $stack_element.get(0).id.slice('trac-card-stack-'.length);    
    }
    
    function get_card_id($card_element) {
        return $card_element.get(0).id.slice('trac-card-'.length);
    }

    // Show initial data
    $(".trac-cards-stacks").map(function() {
        var board_data = get_board_data($(this));
        add_card_elements($(this), board_data);
    });

    // Refresh button
    function reloadCards() {
        var $element = $(this);
        var $stacks_element = $element.parents('.trac-cards-board').children('.trac-cards-stacks');
        var board_data = get_board_data($element);

        var get_data = {
            format: 'json',
            stack: $.map(board_data.stacks_by_name, function(s) {return s.name; }).join("|")
        };
        $.get(board_data.api_url, get_data)
            .done(function(refreshedData) {
                board_data.cards_by_id = refreshedData.cards_by_id;
                board_data.stacks_by_name = refreshedData.stacks_by_name;

                add_card_elements($stacks_element, board_data);
            })
            .fail(show_error);
    };
    $(".trac-cards-reload").click(reloadCards);

    // Auto-Refresh
    $(".trac-cards-reload").map(function() {
        var PERIOD = 10 * 1000;
        var element = this;
        var stacks_element = $(element).parents('.trac-cards-board').children('.trac-cards-stacks').get(0);
        function autoRefresh() {
            reloadCards.call(element);
        }
        function isElementPartiallyInViewport (el) {
            var rect = el.getBoundingClientRect();
            return rect.top <= $(window).height() && rect.left <= $(window).width() && rect.bottom >= 0 && rect.right >= 0;
        }
        function visibilityChanged() {
            clearInterval(timer);
            if (isElementPartiallyInViewport(stacks_element) && !document.hidden) {
                timer = setInterval(autoRefresh, PERIOD);
            }
        }
        var timer = setInterval(autoRefresh, PERIOD);
        $(document).on('DOMContentLoaded load resize scroll visibilitychange', visibilityChanged);
        
        // TODO: opening an edit dialog should maybe stop the auto-refresh-timer as well...
    });

    // Use jQuery UI Sortable to drag-and-drop cards in and between stacks
    $(".trac-cards-stack-sorter").sortable({
        connectWith: ".trac-cards-stack-sorter",
        cursor: "pointer",
        tolerance: "pointer",
        placeholder: "trac-card-placeholder",
        start: function (event, ui) {
            ui.placeholder.html("<div>&nbsp;</div>")
        },
        
        // Move
        update: function(event, ui) {
            if (ui.sender) return; // update is called twice when switching stack

            var $card_element = ui.item.children();

            var stack_name = get_stack_name($card_element);

            var board_data = get_board_data($card_element);

            var card_id = get_card_id($card_element);
            var card = board_data.cards_by_id[card_id];

            var old_stack_name = card.stack;

            card.stack = stack_name;
            card.rank = ui.item.index();

            var post_data = serialized_post_data(card, 'update_card', board_data);
            post_data.old_stack_name = old_stack_name;
            post_data.old_stack_version = board_data.stacks_by_name[old_stack_name].version;
            $.post(board_data.api_url, post_data)
                .done(function() {
                    board_data.stacks_by_name[stack_name].version += 1;
                    if (stack_name != old_stack_name) {
                        board_data.stacks_by_name[old_stack_name].version += 1;
                    }
                })
                .fail(show_error);
        }
    });
    
    // Edit / delete
    var editCardDialog = $("<div title='Edit card'><form><label for='title'>Title:</label><br /><textarea name='title' rows='5' cols='30'></textarea></form></div>");
    var ctrlEditTitle = editCardDialog.find("textarea[name='title']");
    function showEditCardDialog() {
    
        var board_data = get_board_data($(this));

        var $card_element = $(this);
        var card_id = get_card_id($card_element);
        var card = board_data.cards_by_id[card_id];
        ctrlEditTitle.val(card.title);
        editCardDialog.dialog({
            modal: true,
            dialogClass: "trac-cards-dialog",
            buttons: {
                "Edit": function() {
                    var post_data = serialized_post_data(card, 'update_card', board_data);
                    post_data.title = ctrlEditTitle.val();
                    var current_dialog = $(this);
                    $.post(board_data.api_url, post_data, function(updated_card) {
                        card.title_html = updated_card.title_html;
                        card.title = updated_card.title;
                        $card_element.html(card.title_html);

                        current_dialog.dialog("close");
                    }).done(function() {
                        board_data.stacks_by_name[card.stack].version += 1;
                    }).fail(show_error);
                },
                "Delete!": function() {
                    var post_data = serialized_post_data(card, 'delete_card', board_data);
                    var current_dialog = $(this);
                    $.post(board_data.api_url, post_data, function(data) {
                        $card_element.parent().remove();
                        current_dialog.dialog("close");
                    }).done(function() {
                        board_data.stacks_by_name[card.stack].version += 1;
                    }).fail(show_error);
                },
                "Cancel": function() {
                    $(this).dialog("close");
                }
            }
        });
    };
    
    // Create
    var createDialog = $("<div title='Create card'><form><label>Title: <input type='text' name='title' /></label></form></div>");
    var ctrlCreateTitle = createDialog.find("input[name='title']");
    function showAddCardDialog() {
        var $element = $(this);
        var board_data = get_board_data($element);
        var stack_id = get_stack_name($element);
        var $stack_element = $element.parents('.trac-cards-stack');
        var $stack_sorter = $stack_element.children('.trac-cards-stack-sorter');

        ctrlCreateTitle.val('');
        createDialog.dialog({
            modal: true,
            dialogClass: "trac-cards-dialog",
            buttons: {
                "Create": function() {
                    var proposed_card = {
                        id: -1, // Initialized server-side
                        stack: stack_id,
                        rank: -1, // Initialized server-side
                        title: ctrlCreateTitle.val(),                        
                    };
                    var post_data = serialized_post_data(proposed_card, 'add_card', board_data);
                    var current_dialog = $(this);
                    $.post(board_data.api_url, post_data, function(added_card) {
                        board_data.cards_by_id[added_card.id] = added_card;
                        board_data.stacks_by_name[added_card.stack].version += 1;

                        add_card_element($stack_sorter, added_card);

                        current_dialog.dialog("close");
                      }, 'json').fail(show_error);
                },
                "Cancel": function() {
                    $(this).dialog("close");
                }
            }
        });
    };
    $(".trac-card-add").click(showAddCardDialog);

});
