/*
 * Layout 'class'
 */
var Layout = function (name) {
  this.name = name;

  // Selector for all field tds/ths
  this.selector = '';

  // Return the given field name's td/th element
  this.get_tx = function (field) {};

  // Return the given td/th element's field name
  this.get_field = function (tx) {};

  // Reorder the fields
  this.order_fields = function (fields) {};

  // Returns true if the field needs its own row
  this.needs_own_row = function (field) {
    var element = document.getElementById('field-' + field);
    return element !== null && element.tagName.toLowerCase() === 'textarea';
  };

  var saved_field_order = {};
  var prev_fields = null;

  // Update the field layout
  this.update = function () {
    var this_ = this;
    var name = this.name;

    // save original field order
    if (!(name in saved_field_order)) {
      saved_field_order[name] = [];
      jQuery(this.selector).each(function (i, e) {
        var field = this_.get_field($(this));
        if (field)
          saved_field_order[name].push(field);
      });
    }

    // get visible and hidden fields
    var visible = [];
    var hidden = [];
    jQuery.each(saved_field_order[name], function (i, field) {
      var tx = this_.get_tx(field);
      if (tx.hasClass('dynfields-hide')) {
        hidden.push(field);
      } else {
        visible.push(field);
      }
    });

    // get new field order
    var new_fields = jQuery.merge(visible, hidden); // warning: side-effects!

    // order the fields
    if (JSON.stringify(new_fields) !== JSON.stringify(prev_fields)) {
      this.order_fields(new_fields);
      prev_fields = new_fields;
    }
  };
};

var dynfields_group = function(values, n, callback) {
  var groups = [];
  var buf = [];
  jQuery.each(values, function(index, name) {
    if (callback(name)) {
      if (buf.length !== 0) {
        groups.push(buf.slice(0, n));
        buf = [];
      }
      groups.push([name, true]);
    } else {
      buf.push(name);
      if (buf.length === n) {
        groups.push(buf.slice(0, n));
        buf = [];
      }
    }
  });
  if (buf.length !== 0) {
    groups.push(buf.slice(0, n));
  }
  return groups;
};


/*
 * Inputs Layout implementation
 */
var inputs_layout = new Layout('inputs');

// selector
inputs_layout.selector = '#properties td[class!=fullrow]:parent';

// get_tx
inputs_layout.get_tx = function (field) {
  return jQuery('#field-' + field).closest('td');
};

// get_field
inputs_layout.get_field = function (td) {
  var name = td.attr('data-dynfields-name');
  if (!name) {
    var input = td.find(':input:first');
    name = input.length !== 0 ? input[0].id.slice(6) : '<missing>';
    td.attr('data-dynfields-name', name);
  }
  return name !== '<missing>' ? name : '';
};

inputs_layout.order_fields = function (new_fields) {
  var this_ = this;
  var properties = jQuery('#properties');
  var target_row = properties.find('textarea[name=field_description]')
                             .closest('tr');
  var cells = {};
  var headers = {};
  var fullrows = {};
  jQuery.each(new_fields, function(idx, name) {
    var cell = this_.get_tx(name);
    cells[name] = cell;
    headers[name] = cell.prev('th');
    fullrows[name] = cell.hasClass('fullrow');
  });
  var groups = dynfields_group(new_fields, 2,
                               function(name) { return fullrows[name] });
  jQuery.each(groups, function(idx, group) {
    var col1 = group[0];
    var col2 = group[1];
    var cell1 = cells[col1];
    var header1 = headers[col1];
    cell1.removeClass('col2');
    cell1.addClass('col1');
    header1.removeClass('col2');
    header1.addClass('col1');
    var row = jQuery('<tr>').append(headers[col1], cell1);
    if (col2 !== true) {
      var cell2, header2;
      if (col2) {
        cell2 = cells[col2];
        header2 = headers[col2];
        cell2.removeClass('col1');
        header2.removeClass('col1');
      } else {
        cell2 = jQuery('<td>');
        header2 = jQuery('<th>');
      }
      header2.addClass('col2');
      cell2.addClass('col2');
      row.append(header2, cell2);
    }
    target_row.after(row);
    target_row = row;
  });
  properties.find('> table > tbody > tr')
        .not('#dynfields-show-link')
        .each(function() {
    var row = $(this);
    var headers = row.children('th');
    if (headers.length === 0 || !jQuery.trim(headers.text()))
      row.remove();
  });
};


/*
 * Header Layout implementation
 */
var header_layout = new Layout('header');

// selector
header_layout.selector = '#ticket .properties th:parent';

// get_tx
header_layout.get_tx = function (field) {
  return jQuery('#h_' + field);
};

// get_field
header_layout.get_field = function (th) {
  var name = th.attr('data-dynfields-name');
  if (!name) {
    var name = th.length !== 0 ? th[0].id.slice(2) : '<missing>';
    th.attr('data-dynfields-name', name);
  }
  return name !== '<missing>' ? name : '';
};

header_layout.order_fields = function (new_fields) {
  var this_ = this;
  var cells = {};
  var headers = {};
  var fullrows = {};
  jQuery.each(new_fields, function(idx, name) {
    var header = this_.get_tx(name);
    var cell = header.next('td');
    headers[name] = header;
    cells[name] = cell;
    fullrows[name] = cell.attr('colspan') === '3';
  });
  var groups = dynfields_group(new_fields, 2,
                               function(name) { return fullrows[name] });
  var tbody = jQuery('#ticket table.properties > tbody');
  var target_row;
  jQuery.each(groups, function(idx, group) {
    var col1 = group[0];
    var col2 = group[1];
    var row = jQuery('<tr>').append(headers[col1], cells[col1]);
    if (col2 !== true) {
      var header2, cell2;
      if (col2) {
        header2 = headers[col2];
        cell2 = cells[col2];
      } else {
        cell2 = jQuery('<td>');
        header2 = jQuery('<th>');
      }
      row.append(header2, cell2);
    }
    if (target_row === undefined) {
      tbody.prepend(row);
    } else {
      target_row.after(row);
    }
    target_row = row;
  });
  tbody.children('tr').each(function() {
    var row = $(this);
    var headers = row.children('th');
    if (headers.length === 0 || !jQuery.trim(headers.text()))
      row.remove();
  });
};
