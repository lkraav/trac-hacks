// TRAC TicketInfo-Plugin
//
// Copyright (C) 2021 Clemens
// All rights reserved.
//
// This software is licensed as described in the file COPYING, which
// you should have received as part of this distribution.

jQuery(function($) {

  // For the URL we are intentionally not using window.location.href 
  // because we want only the pure URL without local #anchors.
  var url = window.location.protocol + '//' + window.location.hostname + window.location.pathname;

  var tooltip = 'Copy info snippet text to clipboard';

  // We have a hidden Acknowledge text which appears only temporarily when the button is clicked.
  $ack = $('<span>')
    .addClass('infosnippet-ack')
    .attr('style','display: none; padding-right: 0.5em;')
    .text('copy to clipboard completed');

  
  CreateNav(url,$ack.clone(),tooltip);
  CreateBox(url,$ack.clone(),tooltip);
})


// create a "Info" context navigation menu item at top of page. It will copy to clipboard.
function CreateNav (url,ack,tooltip) {

  if ($('#infosnippet-nav').length == 0) { // only if not yet exists 
  if (info.navoption=='all' || info.navoption=='ticket' || info.navoption=='wiki') { 
  
    var $navbutton = $('<li/>');
    $("#ctxtnav ul li:first").after($navbutton);
    
    ack.appendTo($navbutton);
    $("<a>")
      .attr('href', "#infosnippet")
      .attr('id', 'infosnippet-nav')
      .attr("title", tooltip)
      .text("Info")
      .appendTo($navbutton);
      
    // register on-click handler 
    $navbutton.click(function() {
      $('#infosnippet').show(); // make sure the box is shown otherwise cannot copy to clipboard
      CopyToClipboard('infosnippet-text');
      if (info.boxoption!='all' && info.boxoption!='ticket') { 
        $('#infosnippet').hide(); // hide again if disable in config
      }
      $(".infosnippet-ack").show().delay(5000).fadeOut();
      return false;
    });
  }}
}

// Create a "Info Snippet" box at bottom of page
function CreateBox (url,ack,tooltip) {

  var $box;

  if ($('div.ticket').length){
  
    if ($('#infosnippet').length ) { return;} // skip if already exists
   
    // The "Ticket Info" box.
    $box = $('<fieldset>')
      .attr('id','infosnippet')
      .addClass('ticket');
      
    // Hide the box unless enabled in the config.
    // Note that we need the box (invisible or not), because want to copy its content to the clipboard. 
    $box.hide();
    if (info.boxoption=='all') { $box.show(); }
    if (info.boxoption=='ticket') { $box.show(); }
      
    $('<legend>').text('Ticket Info').appendTo($box);

    // the actual info snippet text
    $info= $('<p>')
      .attr('id','infosnippet-text')
      .append(info.projectname + ' Ticket #' + info.ticketid + '</br>'+ info.ticketsummary + '</br>')
      .appendTo($box);
    // URL of current page is part of the info snippet text.
    $("<a>")
      .attr('href',url)
      .append(url)
      .appendTo($info);
      
    // The fieldset is inserted right after the ticket properties
    $("div.ticket #properties").after($box);
  }
  else if ($('#content.wiki').length){
  
    if ($('#infosnippet').length ) { return;} // skip if already exists

    $box = $('<div>')
      .attr('id','infosnippet')
      .addClass('wiki');
      
    // Hide the box unless enabled in the config.
    // Note that we need the box (invisible or not), because want to copy its content to the clipboard. 
    $box.hide();
    if (info.boxoption=='all') { $box.show(); }
    if (info.boxoption=='wiki') { $box.show(); }
    
    // the actual info snippet text
    $info= $('<p>')
      .attr('id','infosnippet-text')
      .append(info.projectname + ' ' + info.page + '</br>')
      .appendTo($box);
    // search for the first head line in this page
    headline=$('#content.wiki .wikipage :header');
    if(headline.length){$info.append(headline[0].innerText+'</br>');}
    // URL of current page is part of the info snippet text.
    $("<a>")
      .attr('href',url)
      .append(url)
      .appendTo($info);
      
    // The infobox is inserted right after the ticket properties
    $("#content.wiki #attachments").after($box);
  }
  else {
    return;
  }
  
  $btn=$('<div>')
    .attr('id','infosnippet-button')
    .append(ack)
    .prependTo($box);
  $('<a>')
    .attr('href','')
    .text('Copy to Clipboard')
    .addClass('button')
    .attr("title", tooltip)
    .appendTo($btn);
  
  // register on-click handler 
  $btn.click(function() {
    CopyToClipboard('infosnippet-text');
    $(".infosnippet-ack").show().delay(5000).fadeOut();
    return false;
  });

}

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

