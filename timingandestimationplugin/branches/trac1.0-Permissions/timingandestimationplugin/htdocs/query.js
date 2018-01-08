function queryScreenTotaler(){
  // Fields we will total
  var columns = ['totalhours','estimatedhours'];
  var tbodies = $('table.listing.tickets tbody.trac-query-results');
  // console.log('Found ', tbodies.length, 'tables to sum');
  var addFooter = false;
  var totalsRowTemp = $('table.listing.tickets tbody.trac-query-results tr').first()
        .clone().attr('class', 'total-row');
  // Build footer row
  $('td',totalsRowTemp).empty()
    .css({'background-color':'#dde',
          'text-align':'right',
          'font-weight': 'bold',
          'padding':'0.1em 0.5em',
          'border':'1px solid #DDD'});

  tbodies.each(function(idx, tbody){
    // console.log('Handling tbody ', idx, 'kids:', $('tr', tbody).length);
    tbody = $(tbody);
    if(tbody.has('tr').length == 0) return true;
    // true tfeet render at teh bottom
    var tfoot = tbody.next('tbody.foot.totals');
    if(tfoot.length==0){
      tfoot = $('<tbody class="foot totals"></tbody>');
    }
    var totalsRow = $('.total-row', tfoot);
    if(totalsRow.length == 0){
      totalsRow = totalsRowTemp.clone();
    }

    $.each(columns,function(idx, field){
      // count totals
      var total = 0;
      $('td.'+field, tbody).each(function(cidx, cell){
	$(cell).css('text-align','right');
	var val = Number($(cell).text());
	if(!isNaN(val)) total += val;
      });
      //set total text in each footer row
      if(!isNaN(total) && total ){
        addFooter = true;
        // console.log('Setting total', total,' tblIdx: ', idx, 'field:', field);
        $('td.'+field,totalsRow).text(total.toString());
      }
    });
    if(addFooter){
      // console.log('Adding tfoot');
      tbody.after(tfoot);
      tfoot.append(totalsRow);
    }
  });
};
// queryScreenTotaler();
$(document).ready(function(){window.setTimeout(queryScreenTotaler, 125);});
