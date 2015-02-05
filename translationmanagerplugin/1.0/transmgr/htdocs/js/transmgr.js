function check() {
	var checkbox = document.getElementsByName('see');
	if (checkbox[1].checked || checkbox[2].checked) {
		checkbox[0].checked = false;
	}
}

function allCheck() {
	var checkbox = document.getElementsByName('see');
	if (checkbox[0].checked) {
		checkbox[1].checked = false;
		checkbox[2].checked = false;
	}
}


var Anzahl = 1;
function addingLang(here) {
	var ur = here.parentNode.childNodes[1].childNodes[1];
	var clone = ur.cloneNode(true);
	ur.parentNode.appendChild(clone);
	Anzahl++;
}


function delLang(here) {
	del_element = here.parentNode.childNodes[1].lastChild;
	del_element.parentNode.removeChild(del_element);
	Anzahl--;
}

function quantity() {
	var del_button = document.getElementsByName("del")
	if (Anzahl > 1) {
		for (var i = 0; i < del_button.length; i++) {
			del_button[i].disabled=false;
		}
	}
	else if (Anzahl == 1) {
		for (var i = 0; i < del_button.length; i++) {
			del_button[i].disabled=true;
		}
	}
}

// nach start_to_main, welche geändert wurden:
function namen(obj, a) {
	var x = obj.parentNode.cellIndex;
	var head = document.getElementById("head").getElementsByTagName("th")[x].id;
	obj.name = a + "_from_" + head;
	obj.style.backgroundColor = "#FFFF80"
}


$(document).ready(function() {

$("input[id='input_values']").keyup(function(){
	if ($(this).val())
		{
		$("input[id='checkin']").removeAttr("disabled")
		}
})

function enabled(event) {
		if ($("input#own").is(":checked")) {
			$(event.data.div).removeAttr("disabled");
			$(event.data.div).css("color", "black");
			if (Anzahl == 1) {
				$(event.data.del).attr("disabled", "disabled");
			}
		}
		else {
			$(event.data.div).attr("disabled", "disabled");
			$(event.data.div).css("color", "gray")
		}
}

function load_div() {
	var $comment = $("#comment_check").val();
	var $user = $("#user_name").val();
	var $full_comment = $user + " " + $comment
	$("input#comment_form").val($full_comment);
}

var $fil = $("div#extra").load('/trac/Legato/transmgr/extra.html', function() {
	
	$("div#own_setting *").attr("disabled", "disabled");
	$("div#own_setting *").css("color", "gray");
	$("input[name='see']").bind('change', {div:"div#own_setting *", del:"#filter_del"}, enabled);
	
	var checkboxen = $("table.listing.tickets td:first-child").children("input")
//		$("input[name='warning_exist']");
	$("input#all_checked").click(function(){
		if ($("input#all_checked").is(":checked")) {
			checkboxen.attr("checked", "checked")
		}
		else {
			checkboxen.attr("checked", false)
		}
	})
	
	$('div#export_dialog').dialog({
		autoOpen: false,
	    modal: true,
	    draggable: true,
	    resizable: false,
	    position: ['center', 'center'],
	    width: 400,
	    height: "auto",
	    buttons: {
	        "Abbrechen": function() {
	            $(this).dialog("close");
	        },
			"Download": function() {
				$(this).dialog("close");
				$('div#export_dialog > form').submit();
			}
	    },
	});

	$('div#add').dialog({
		autoOpen: false,
	    modal: true,
	    draggable: true,
	    resizable: false,
	    position: ['center', 'center'],
	    width: 370,
	    height: "auto",
	    buttons: {
	        "Abbrechen": function() {
	            $(this).dialog("close");
	        },
			"Hinzufügen": function() {
				$(this).dialog("close");
				$("div#add > form").submit();
				$("div#wait").dialog("open");
			},
	    },
	});
	
	$('div#delete').dialog({
		autoOpen: false,
	    modal: true,
	    draggable: true,
	    resizable: false,
	    position: ['center', 'center'],
	    width: 370,
	    height: "auto",
	    buttons: {
	        "Abbrechen": function() {
	            $(this).dialog("close");
	        },
			"Entfernen": function() {
				$(this).dialog("close");
				$("div#delete > form").submit();
			}
	    },
	});

	$('div#filter').dialog({
		autoOpen: false,
	    modal: true,
	    draggable: true,
	    resizable: false,
	    position: ['center', 'center'],
	    width: 650,
	    height: "auto",
	    buttons: {
	        "Abbrechen": function() {
	            $(this).dialog("close");
	        },
			"Hinzufügen": function() {
				$(this).dialog("close");
				$("div#filter > form").submit();
				$("div#wait").dialog("open");
			}
	    },
	});

	$('div#search1').dialog({
		autoOpen: false,
	    modal: true,
	    draggable: true,
	    resizable: false,
	    position: ['center', 'center'],
	    width: 400,
	    height: "auto",
	    buttons: {
	        "Abbrechen": function() {
	            $(this).dialog("close");
	        },
			"Suchen": function() {
				$(this).dialog("close");
				$("div#search1 > form").submit();
			}
	    },
	});

	$('div#check-in').dialog({
		autoOpen: false,
	    modal: true,
	    draggable: true,
	    resizable: false,
	    position: ['center', 'center'],
	    width: 400,
	    height: "auto",
	    buttons: {
	        "Abbrechen": function() {
	            $(this).dialog("close");
	        },
			"Einchecken": function() {
				$(this).dialog("close");
//				geänderten Wörter und main_to_main:
				load_div();
				$('div#Einchecken > form').submit();
				$("div#wait").dialog("open");
			}
	    },
	});
	
	error_exist = $("#error_exist").val();
	$('div#warning_exist').dialog({
		autoOpen: (error_exist == "keys_exist" ? true : false),
	    modal: true,
	    draggable: true,
	    resizable: false,
	    position: ['center', 'center'],
	    width: 400,
	    height: "auto",
	    buttons: {
//	        "Abbrechen": function() {
//	            $(this).dialog("close");
//	        },
			"Markierte importieren": function() {
				$(this).dialog("close");
				$('div#warning_exist > form').submit();
			}
	    },
	});
	
	error_new = $("#error_new").val();
	$('div#warning_new').dialog({
		autoOpen: (error_new == "keys_new" ? true : false),
	    modal: true,
	    draggable: true,
	    resizable: false,
	    position: ['center', 'center'],
	    width: 400,
	    height: "auto",
	    buttons: {
//	        "Abbrechen": function() {
//	            $(this).dialog("close");
//	        },
			"Markierte importieren": function() {
				$(this).dialog("close");
				$('div#warning_new > form').submit();
			}
	    },
	});
	
	error_no_value = $("#error_no_value").val();
	$('div#warning_no_value').dialog({
		autoOpen: (error_no_value == "keys_no_value" ? true : false),
	    modal: true,
	    draggable: true,
	    resizable: false,
	    position: ['center', 'center'],
	    width: 400,
	    height: "auto",
	    buttons: {
//	        "Abbrechen": function() {
//	            $(this).dialog("close");
//	        },
			"Markierte importieren": function() {
				$(this).dialog("close");
				$('div#warning_no_value > form').submit();
			}
	    },
	});
	
	$("#checkin").click(function() { $("div#check-in").dialog("open"); });
	$("#searching").click(function() { $("div#search1").dialog("open"); });
	$("#add_filter").click(function(){ $("div#filter").dialog("open"); });
	$("#export-button").click(function(){ $("div#export_dialog").dialog("open"); });
	$("#add_lang").click(function(){ $("div#add").dialog("open"); });
	$("#del_lang").click(function(){ $("div#delete").dialog("open"); });
	
});

var $im = $("div#import").load('/trac/Legato/transmgr/import-export.html', function() {
//// für tm-start:
//	$("div#double *").attr("disabled", "disabled");
//	$("div#double *").css("color", "gray");
//	$("input[name='see']").bind('change', {div:"div#double *", del:"#double_del"}, enabled);
	
	$('div#wait').dialog({
		open: function(event, ui) {
			$(".ui-dialog-titlebar-close", ui.dialog || ui).hide();
		},
		autoOpen: false,
	    modal: true,
	    draggable: false,
	    resizable: false,
	    position: ['center', 'center'],
	    width: 250,
	    height: "auto",
	});
	
// für import
up = $("#up").val();
$("div#durchsuchen").dialog({
	autoOpen: false,
	modal: true,
	resizable: false,
	position:['center', 'center'],
	height:"auto",
	width:"auto",
	buttons: {
	"Abbrechen": function() {
		$(this).dialog("close");
	},
	"Weiter": function() {
		$(this).dialog("close");
		$("#durchsuchen > form").submit();
	},}
});

$("div#import_dialog").dialog({
	autoOpen: (up == "durchsuchen" ? true : false),
    modal: true,
    draggable: false,
    resizable: false,
    position: ['center', 'center'],
    width: 500,
    height: "auto",
    buttons: {
        "Abbrechen": function() {
            $(this).dialog("close");
        },
        "Zurück": function() {
        	$(this).dialog("close");
        	$("div#durchsuchen").dialog("open");
        },
		"Weiter": function() {
			$(this).dialog("close");
			$("#import_dialog > form").submit();
		}
    },
});

$('div#import_dialog2').dialog({
	autoOpen: (up == "import_dialog" ? true : false),
    modal: true,
    draggable: false,
    resizable: false,
    position: ['center', 'center'],
    width: 500,
    height: "auto",
    buttons: {
        "Abbrechen": function() {
            $(this).dialog("close");
        },
        "Zurück": function() {
        	$("div#import_dialog").dialog("open")
        	$(this).dialog("close")
        },
		"OK": function() {
			$(this).dialog("close");
			$("div#import_dialog2 > form").submit();
		}
    },
});


$("#import-button").click(function(){ $("div#durchsuchen").dialog("open"); });

})
})