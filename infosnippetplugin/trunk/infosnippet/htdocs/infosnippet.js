// TRAC TicketInfo-Plugin
//
// Copyright (C) 2021 Clemens
// All rights reserved.
//
// This software is licensed as described in the file COPYING, which
// you should have received as part of this distribution.

jQuery(function($) {

  var tooltip = 'Copy info snippet text to clipboard';
  
  // For the URL we are intentionally not using window.location.href 
  // because we want only the pure URL without local #anchors.
  var url = window.location.protocol + '//' + window.location.hostname + window.location.pathname;

  // We have a hidden Acknowledge text which appears only temporarily when the button is clicked.
  $ack = $('<span>')
    .addClass('ticketinfo-ack')
    .attr('style','display: none; padding-right: 0.5em;')
    .text('copy to clipboard completed');
  
  // Create a "ticket info" box 
  if ($('#ticketinfo').length == 0) { // only if not yet exists
    
    // The "Ticket Info" box.
    $fset = $('<fieldset>')
      .attr('id','ticketinfo');

    // Hide the box if not enabled in the config.
    // Note that - even if invisible - we need the box, because want to copy its content to the clipboard. 
    if (info.boxoption!='all' && info.boxoption!='ticket') { 
      $fset.hide();
    }

    $('<legend>').text('Ticket Info').appendTo($fset);
    // the COPY button
    $btn=$('<div>')
      .attr('id','ticketinfo-button')
      .append($ack.clone())
      .appendTo($fset);
    $('<a>')
      .attr('href','')
      .text('Copy to Clipboard')
      .addClass('button')
      .attr("title", tooltip)
      .appendTo($btn);
    // the actual info snippet text
    $info= $('<p>')
      .attr('id','ticketinfo-text')
      // Those variables info.??? are provided by TRAC from within the plugin.
      .append(info.projectname + ' Ticket #' + info.ticketid + '</br>'+ info.ticketsummary + '</br>')
      .appendTo($fset);
    // URL of current page is part of the info snippet text.
    $("<a>")
      .attr('href',url)
      .append(url)
      .appendTo($info);
    // The fieldset is inserted right after the ticket properties
    $("div.ticket #properties").after($fset);
  
    // register on-click handler 
    $("#ticketinfo-button").click(function() {
      CopyToClipboard('ticketinfo-text');
      $(".ticketinfo-ack").show().delay(5000).fadeOut();
      return false;
    });
  }

  // create a "Info" context navigation menu item at top of page. It will copy to clipboard.
  if ($('#infosnippet-nav').length == 0) { // only if not yet exists 
  if (info.navoption=='all' || info.navoption=='ticket') { 
  
    var $navbutton = $('<li/>');
    $("#ctxtnav ul li.first").after($navbutton);
    $ack.appendTo($navbutton);
    $("<a>")
      .attr('href', "#ticketinfo")
      .attr('id', 'infosnippet-nav')
      .attr("title", tooltip)
      .text("Info")
      .appendTo($navbutton);
      
    // register on-click handler 
    $navbutton.click(function() {
      $fset.show(); // make sure the box is shown otherwise cannot copy to clipboard
      CopyToClipboard('ticketinfo-text');
      if (info.boxoption!='all' && info.boxoption!='ticket') { 
        $fset.hide(); // hide again if disable in config
      }
      $(".ticketinfo-ack").show().delay(5000).fadeOut();
      return false;
    });
  }}
  
})

// copy the text from a DIV container (given by ID) into the system clipboard
function CopyToClipboard (containerid) {
  if (document.getElementById(containerid) == null) return;
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

