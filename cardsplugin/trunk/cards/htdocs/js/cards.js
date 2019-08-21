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
                color: card.color,
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
        $card_element.css('background', card.color);
        $card_element.html(card.title_html);
        $card_element.dblclick(showEditCardDialog);
        $stack_sorter.append($card_slot);
    }
    
    function add_card_elements($stacks_element, data) {
        var $sorters = $stacks_element.find(".trac-cards-stack-sorter");
        $sorters.empty();

        var sorted_cards = $.map(data.cards_by_id, function(card, id) { return card; });
        sorted_cards.sort(function(a, b) { return a.rank - b.rank; });

        $.each(sorted_cards, function(index, card) {
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
        var element = this;
        var $element = $(this);
        var $stacks_element = $element.parents('.trac-cards-board').children('.trac-cards-stacks');
        var stacks_element = $stacks_element.get(0);
        var board_data = get_board_data($element);
        var period = board_data.auto_refresh_interval * 1000;
        function autoRefresh() {
            reloadCards.call(element);
        }
        function isElementPartiallyInViewport (el) {
            var rect = el.getBoundingClientRect();
            return rect.top <= $(window).height() && rect.left <= $(window).width() && rect.bottom >= 0 && rect.right >= 0;
        }
        board_data.reset_timer = function() {
            if (board_data.timer) {
                clearInterval(board_data.timer);
                if (isElementPartiallyInViewport(stacks_element) && !document.hidden) {
                    board_data.timer = setInterval(autoRefresh, period);
                }
            }
        }
        board_data.pause_timer = function() {
            if (board_data.timer) {
                clearInterval(board_data.timer);
            }
        }
        if (board_data.auto_refresh) {
            board_data.timer = setInterval(autoRefresh, period);
            $(document).on('DOMContentLoaded load resize scroll visibilitychange', board_data.reset_timer);
        }
    });

    // Use jQuery UI Sortable to drag-and-drop cards in and between stacks
    $(".trac-cards-stack-sorter").sortable({
        connectWith: ".trac-cards-stack-sorter",
        cursor: "pointer",
        tolerance: "pointer",
        placeholder: "trac-card-placeholder",
        start: function (event, ui) {
            ui.placeholder.html("<div>&nbsp;</div>")
            
            var $card_element = ui.item.children();
            var board_data = get_board_data($card_element);
            board_data.pause_timer();
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
            var old_stack_rank = card.rank;

            card.stack = stack_name;
            card.rank = ui.item.index();
            
            $.each(board_data.cards_by_id, function(id, c) {
                if (c != card && c.stack == old_stack_name && c.rank >= old_stack_rank) {
                    c.rank -= 1;
                }
                if (c != card && c.stack == card.stack && c.rank >= card.rank) {
                    c.rank += 1;
                }
            });

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
                .fail(show_error).always(board_data.reset_timer);
        }
    });
    
    // Edit / delete
    var editCardDialog = $("<div title='Edit card'><form><label for='title'>Title:</label><br /><textarea name='title' rows='5' cols='30'></textarea><br /><label>Color: <input type='color' name='color' /></label></form></div>");
    var ctrlEditTitle = editCardDialog.find("textarea[name='title']");
    var ctrlEditColor = editCardDialog.find("input[name='color']");
    function showEditCardDialog() {
    
        var board_data = get_board_data($(this));
        board_data.pause_timer();
        
        var $card_element = $(this);
        var card_id = get_card_id($card_element);
        var card = board_data.cards_by_id[card_id];
        ctrlEditTitle.val(card.title);
        ctrlEditColor.val(card.color || '#ffffe0');
        editCardDialog.dialog({
            modal: true,
            dialogClass: "trac-cards-dialog",
            buttons: {
                "Edit": function() {
                    var post_data = serialized_post_data(card, 'update_card', board_data);
                    post_data.title = ctrlEditTitle.val();
                    post_data.color = ctrlEditColor.val();
                    var current_dialog = $(this);
                    $.post(board_data.api_url, post_data, function(updated_card) {
                        card.title_html = updated_card.title_html;
                        card.title = updated_card.title;
                        $card_element.html(card.title_html);
                        card.color = updated_card.color;
                        $card_element.css('background', card.color);
                        current_dialog.dialog("close");
                    }).done(function() {
                        board_data.stacks_by_name[card.stack].version += 1;
                    }).fail(show_error).always(board_data.reset_timer);
                },
                "Delete!": function() {
                    var deleteCardDialog = $("<div title='Confirm delete'>Really delete card?</div>");
                    deleteCardDialog.dialog({
                        modal: true,
                        dialogClass: "trac-cards-dialog",
                        buttons: {
                            "Delete!": function() {
                                var post_data = serialized_post_data(card, 'delete_card', board_data);
                                $.post(board_data.api_url, post_data, function(data) {
                                    $card_element.parent().remove();
                                    deleteCardDialog.dialog("close");
                                    editCardDialog.dialog("close");
                                }).done(function() {
                                    board_data.stacks_by_name[card.stack].version += 1;
                                }).fail(show_error).always(board_data.reset_timer);
                            },
                            "Cancel": function() {
                                $(this).dialog("close");
                            }
                        }
                    });
                },
                "Cancel": function() {
                    $(this).dialog("close");
                    board_data.reset_timer();
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
        board_data.pause_timer();
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
                        color: '#ffffe0', // default: yellow
                    };
                    var post_data = serialized_post_data(proposed_card, 'add_card', board_data);
                    var current_dialog = $(this);
                    $.post(board_data.api_url, post_data, function(added_card) {
                        board_data.cards_by_id[added_card.id] = added_card;
                        board_data.stacks_by_name[added_card.stack].version += 1;

                        add_card_element($stack_sorter, added_card);

                        current_dialog.dialog("close");
                      }, 'json').fail(show_error).always(board_data.reset_timer);
                },
                "Cancel": function() {
                    $(this).dialog("close");
                    board_data.reset_timer();
                }
            }
        });
    };
    $(".trac-card-add").click(showAddCardDialog);

    // Export
    var exportDialog = $("<div title='Export'><form><label for='wiki'>Content:</label><br /><textarea name='wiki' rows='5' cols='30'></textarea></form></div>");
    var ctrlExportWiki = exportDialog.find("textarea[name='wiki']");
    function showExportStackDialog() {
        var $element = $(this);
        var board_data = get_board_data($element);
        var stack_id = get_stack_name($element);

        var sorted_cards = $.map(board_data.cards_by_id, function(card, id) { return card; })
                            .filter(function(card) { return card.stack == stack_id; });
        sorted_cards.sort(function(a, b) { return a.rank - b.rank; });
        var label = board_data.labels[stack_id];
        var wiki = '=== ' + label + '\n\n' + $.map(sorted_cards, function(card, id) { return card.title; }).join('\n\n');
        ctrlExportWiki.val(wiki);

        exportDialog.dialog({
            modal: true,
            dialogClass: "trac-cards-dialog",
            buttons: {
                "OK": function() {
                    $(this).dialog("close");
                }
            }
        });
    };
    function showExportBoardDialog() {
        var $element = $(this);
        var board_data = get_board_data($element);

        var wiki = '';
        $.each(board_data.stack_names, function(index, stack_id) {
            var sorted_cards = $.map(board_data.cards_by_id, function(card, id) { return card; })
                                .filter(function(card) { return card.stack == stack_id; });
            sorted_cards.sort(function(a, b) { return a.rank - b.rank; });

            var label = board_data.labels[stack_id];
            wiki += '=== ' + label + '\n\n' + $.map(sorted_cards, function(card, id) { return card.title; }).join('\n\n') + '\n\n';
        });
        ctrlExportWiki.val(wiki);

        exportDialog.dialog({
            modal: true,
            dialogClass: "trac-cards-dialog",
            buttons: {
                "OK": function() {
                    $(this).dialog("close");
                }
            }
        });
    };
    $(".trac-cards-export-stack").click(showExportStackDialog);
    $(".trac-cards-export-board").click(showExportBoardDialog);

});
