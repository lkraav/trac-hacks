/*! Javsscript code for Trac Watchlist Plugin 
 * $Id: watchlist.js $
 * */

jQuery(document).ready(function() {
  // Autocomplete Wiki Names
  var asWikiNames = [];
  $("table#wikilist tbody td.name").each(function () {
      asWikiNames.push( $(this).text().replace(/^\s*|\s*$/g,'') );
  });
  $("#wikis .remfromwatch input[name=resid]")
      .autocomplete(asWikiNames);
  $("#wikis tfoot th.name input")
      .autocomplete(asWikiNames);
  ///
  
  // Wiki author names
  var osAuthorsHash = new Object();
  var asAuthors = new Array();
  $("table#wikilist tbody td.author").each(function () {
      osAuthorsHash[ $(this).text().replace(/^\s*|\s*$/g,'') ] = 1;
  });
  for (key in osAuthorsHash) {
    asAuthors.push(key);
  }
  $("#wikis tfoot th.author input")
      .autocomplete(asAuthors);
  osAuthorsHash = 0;
  asAuthors     = 0;
  ///

  // Autocomplete Ticket Ids
  var asTicketIds = [];
  $("table#ticketlist tbody td.id").each(function () {
      asTicketIds.push( $(this).text().replace(/^\s*#|\s*$/g,'') );
  });
  $("#tickets .remfromwatch input[name=resid]")
      .autocomplete(asTicketIds);
  $("#tickets tfoot th.id input")
      .autocomplete(asTicketIds);
  asWikiNames = 0;
  asTicketIds = 0;
  ///

  // AJAX calls
  var options = {delay:750, matchCase:true, matchSubset:true,
        selectFirst:false, multiple:true, multipleSeparator:',', cacheLength:10, max:100 }
  $("#tickets .addtowatch input[name=resid]")
      .autocomplete("./watchlist?action=search&realm=ticket", options);
  $("#wikis .addtowatch input[name=resid]")
      .autocomplete("./watchlist?action=search&realm=wiki", options);
  ///
});


