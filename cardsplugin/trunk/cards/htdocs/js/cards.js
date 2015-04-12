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
        };
    }

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

            var card_element = ui.item.children();

            var stack_element = card_element.parents('.trac-cards-stack');
            var stack_id = stack_element.get(0).id.slice('trac-card-stack-'.length);    

            var board_element = card_element.parents('.trac-cards-board');
            var board_data = window['cards_' + board_element.get(0).id.slice(-12)];

            var card_id = card_element.get(0).id.slice('trac-card-'.length);    
            var card = board_data.cards_by_id[card_id];

            card.stack = stack_id;
            card.rank = ui.item.index();

            var post_data = serialized_post_data(card, 'update_card', board_data);
            $.post(board_data.api_url, post_data);
        }
    });
    
    // Edit / delete
    var editCardDialog = $("<div title='Edit card'><form><label for='title'>Title:</label><br /><textarea name='title' rows='5' cols='30'></textarea></form></div>");
    var ctrlEditTitle = editCardDialog.find("textarea[name='title']");
    function showEditCardDialog() {
    
        var board_element = $(this).parents('.trac-cards-board');
        var board_data = window['cards_' + board_element.get(0).id.slice(-12)];

        var card_element = this;
        var card_id = card_element.id.slice('trac-card-'.length);
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
                        $(card_element).html(card.title_html);

                        current_dialog.dialog("close");
                    }).fail(function (xhr, textStatus, errorThrown) {
                        alert(errorThrown);
                    });
                },
                "Delete!": function() {
                    var post_data = serialized_post_data(card, 'delete_card', board_data);
                    var current_dialog = $(this);
                    $.post(board_data.api_url, post_data, function(data) {
                        $(card_element).parent().remove();
                        current_dialog.dialog("close");
                    });
                },
                "Cancel": function() {
                    $(this).dialog("close");
                }
            }
        });
    };
    $(".trac-card").dblclick(showEditCardDialog);
    
    // Create
    var createDialog = $("<div title='Create card'><form><label>Title: <input type='text' name='title' /></label></form></div>");
    var ctrlCreateTitle = createDialog.find("input[name='title']");
    function showAddCardDialog() {

        var board_element = $(this).parents('.trac-cards-board');
        var board_data = window['cards_' + board_element.get(0).id.slice(-12)];

        var stack_element = $(this).parents('.trac-cards-stack');
        var stack_id = stack_element.get(0).id.slice('trac-card-stack-'.length);

        var stack_sorter = stack_element.children('.trac-cards-stack-sorter');
        
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
                        
                        var card_slot = $("<div class='trac-card-slot'><div class='trac-card'></div></div>");
                        var card_element = card_slot.find(".trac-card");
                        card_element.attr('id', 'trac-card-' + added_card.id);
                        card_element.html(added_card.title_html);
                        card_element.dblclick(showEditCardDialog);
                        stack_sorter.append(card_slot);
                        
                        current_dialog.dialog("close");
                      }, 'json');
                },
                "Cancel": function() {
                    $(this).dialog("close");
                }
            }
        });
    };
    $(".trac-card-add").click(showAddCardDialog);

});