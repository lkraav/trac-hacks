// TRAC TicketInfo-Plugin
//
// Copyright (C) 2021 Clemens
// All rights reserved.
//
// This software is licensed as described in the file COPYING, which
// you should have received as part of this distribution.

jQuery(function($) {
  // Create a "ticket info" box (unless already exists.
  // The variables info.XXX are provided by TRAC from within the plugin.
  if ($('#ticketinfo').length > 0) return;
  var $ticketinfo = $('<fieldset id="ticketinfo"><!-- TicketInfoPlugin -->' +
    '<legend>Ticket Info</legend>'+
    '<div id="ticketinfo-button">' +
    '<span id="ticketinfo-ack" style="display: none;">copy to clipboard completed</span>' +
    '<a class="button" href="#ticketinfo" title="Copy to clipboard"><span>copy</span></a>' +
    '</div>' +
    '<p id="ticketinfo-text">'+
    info.projectname + ' Ticket #' + info.ticketid + '</br>' + 
    info.ticketsummary + '</br>' + 
    // create link 
    // Intentionally do not use window.location.href here 
    // because we want only the base URL but not relative anchors (typically from #sub-headlines)
    '<a href="'+window.location.protocol + '//' + window.location.hostname + window.location.pathname + '">'+ 
                window.location.protocol + '//' + window.location.hostname + window.location.pathname +'</a>'+
    '</p>'+
    '</fieldset>');
  $("div.ticket #properties").after($ticketinfo);
  
  // register on-click handler 
  $("#ticketinfo").click(function() {
    CopyToClipboard('ticketinfo-text');
    $("#ticketinfo-ack").show().delay(5000).fadeOut();
    return false;
  });

})

// copy the text from a DIV container (given by ID) into the system clipboard
function CopyToClipboard (containerid) {
  var dummy= document.createElement('textarea')
  dummy.id = 'temp_element';
  dummy.style.height = 0;
  dummy.style.border = 0;
  document.body.appendChild(dummy);
  dummy.value = document.getElementById(containerid).innerText; // copy text from container into textarea
  document.getElementById("temp_element").select();
  document.execCommand('copy');
  document.body.removeChild(dummy);
}
