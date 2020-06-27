/* Refresh ticket actions when ticket type is changed */
jQuery(document).ready(function(){
    $("#field-type").autoSubmit({mw_refresh: '1', preview: '1'}, function(data, reply) {
        var previouslyCheckedAction = $("#action input[name='action']:checked");
        var items = $(reply);
        var actions = items.filter('#action');
        if(actions.length > 0)
            $("#action").replaceWith(actions);

        /* We try to keep the previous selection */
        var actionToClick = $("#action input[id='" + previouslyCheckedAction.attr('id') + "']");
        if (actionToClick.length !== 0)
        {
            actionToClick.click();
        }
        else
            $("#action input[name='action']:first").click();
    }, "#action .trac-loading");
    $("#field-type").blur()
});