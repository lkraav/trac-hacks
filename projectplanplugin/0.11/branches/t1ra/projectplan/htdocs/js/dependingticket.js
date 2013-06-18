/**
 * AnBo, beta
 * ticket: adds javascript link looking like a button allowing to create a depending ticket
 * newticket: adds given ticket number to dependencies field
 */

/**
 * add button
 */
function ppCreateNewDependingTicket()
{
  if( /\/ticket\//.test(window.location.href) ) {
    var ppCreateNewDependingTicket = '<div style="margin-top:1.5ex;float:left"><a href="#" name="ppCreateNewDependingTicket" style="background-color:#EEE; padding: 0.1em 0.5em; border: 1px outset #CCCCCC; color:#222; margin:1em 0.5em 0.1em 0;" onclick="return ppCreateNewDependingTicketAction(this);">Create new depending ticket</a></div>';
    var ppCreateNewBlockingTicket = '<div style="margin-top:1.5ex;float:left"><a href="#" name="ppCreateNewBlockingTicket" style="background-color:#EEE; padding: 0.1em 0.5em; border: 1px outset #CCCCCC; color:#222; margin:1em 0.5em 0.1em 0;" onclick="return ppCreateNewBlockingTicketAction(this);">Create new blocking ticket</a></div>';
    $('.buttons').append('<div>'+ppCreateNewDependingTicket+ppCreateNewBlockingTicket+'</div>');
  }
}


/**
 * get query parameter of current url, thanks to http://css-tricks.com/snippets/javascript/get-url-variables/
 */
function getQueryVariable(variable)
{
       var query = window.location.search.substring(1);
       var vars = query.split("&");
       for (var i=0;i<vars.length;i++) {
               var pair = vars[i].split("=");
               if(pair[0] == variable){return pair[1];}
       }
       return(false);
}

/**
 * add dependencies ticket to new ticket form
 */
function ppAddDependenciesToNewDependingTicket()
{
  if( /\/newticket/.test(window.location.href) ) {
    if( getQueryVariable('dep') != "" ) {
      $('#field-dependencies').val( getQueryVariable('dep') );
    }
    if( getQueryVariable('blocking') != "" ) {
      $('#field-dependenciesreverse').val( getQueryVariable('blocking') );
    }
  }
}

/**
 * new form action
 */
function ppCreateNewDependingTicketAction(mylink) {
  mylink.href = '../newticket?dep='+$('.trac-id').html().replace('#','');
  console.log(mylink.href);
  return true;
}
function ppCreateNewBlockingTicketAction(mylink) {
  mylink.href = '../newticket?blocking='+$('.trac-id').html().replace('#','');
  console.log(mylink.href);
  return true;
}


$(document).ready(function () {
	ppCreateNewDependingTicket();
	ppAddDependenciesToNewDependingTicket();
});




