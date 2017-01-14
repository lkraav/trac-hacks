mermaid.init();
$(".mermaid g[title]").css('cursor', 'pointer');

var tracMermaidDialog = $(
    "<div title='" + "preview" + "'>" +
    "<input id='mermaidsave' name='mermaidsave' value='Save' type='submit'></input>" +
    "<div style='display:table; height:100%; width:100%;'>" +
    "<textarea class='ui-corner-all' id='mermaidsource' cols='40' rows='20' style='display:table-cell; vertical-align:top;'>" +
    "</textarea>" +
    "<div id='mermaidpreview' style='display:table-cell; vertical-align:top;'>" +
    "</div>" +
    "</div>" +
    "</div>");

function updateMermaid(target, source) {
    target.text(source);
    target.removeAttr('data-processed');
    mermaid.init(undefined, target);
    $("g[title]", target).css('cursor', 'pointer');
}

$(function() {
    $('.mermaid').dblclick(function() {
        var source = $(this);
        var id = source.attr("id");
        var resourceRealm = source.data("mermaidresourcerealm");
        var resourceId = source.data("mermaidresourceid");
        var resourceVersion = source.data("mermaidresourceversion");
        if (resourceRealm != "wiki" || resourceVersion != "") {
            return;
        }
        var curr = decodeURIComponent(source.data("mermaidsource"));
        var prev = curr;
        var intervalId;
        tracMermaidDialog.dialog({
            modal: true,
            width: 640,
            open: function(evt, ui) {
                intervalId = setInterval(function() {
                    var curr = $("#mermaidsource").val();
                    if (curr != prev) {
                        updateMermaid($('#mermaidpreview'), curr);
                        prev = curr;
                    }
                }, 1000);
            },
            close: function(evt, ui) {
                clearInterval(intervalId);
            }
        });
        $("#mermaidsource").val(curr);
        updateMermaid($('#mermaidpreview'), curr);
        $('#mermaidsave').click(function() {
            var curr = $("#mermaidsource").val()
            var data = {
                "__FORM_TOKEN": form_token,
                id: id,
                wikipage: resourceId,
                source: curr
            }
            $.post(_tracmermaid.submit, data);

            // update the original chart
            source.data("mermaidsource", curr);
            updateMermaid(source, curr);

            tracMermaidDialog.dialog("close");
        });
    });

});
