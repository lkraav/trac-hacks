/* -*- coding: utf-8 -*-
 * Copyright (C) 2008 Abbywinters.com
 * trac-dev@abbywinters.com
 * Contributor: Zach Miller
 */

if (!window.console)
  window.console = {};
  console.log = console.log || function () {
};

jQuery(function ($) {

  // Do post-load processing on each field type on the page

  var $table_inits_holder = $("#table_inits_holder");

  // SELECT
  $table_inits_holder.find("select").each(function () {
    var select = $(this);
    var field = select.attr("name");
    console.log("SELECT field name: " + field);
    $("td." + field).each(function () {
      var field_text = $.trim($(this).text());
      $(this).html(select.clone().get(0));
      var default_option = $(this).find(
        $.format('option[value="$1"]', field_text));
      if (default_option[0] !== undefined) {
        default_option.prop('selected', 'selected');
      } else {
	$(this).find('select').prepend(
          $($.format('<option value="$1" selected="selected">$1</option>',
		     field_text)))
      }
    });
  });
  // INPUT TEXT
  $table_inits_holder.find("input[type='text']").each(function () {
    var field = $(this).attr("name");
    console.log("TEXT field name: " + field);
    var text = $(this);
    $("td." + field).each(function () {
      var gridmod_default = $.trim($(this).text());
      $(this).html(text.clone().get(0));
      console.log("  gridmod_default: " + gridmod_default);
      if (gridmod_default != '') {
        $(this).contents('input').val(gridmod_default);
      }
    });
  });
  // INPUT CHECKBOX
  $table_inits_holder.find("input[type='checkbox']").each(function () {
    var field = $(this).attr("name");
    console.log("CHECKBOX field name: " + field);
    var checkbox = $(this);
    $("td." + field).each(function () {
      var gridmod_default = $.trim($(this).text());
      $(this).html(checkbox.clone().get(0));
      console.log("  gridmod_default: " + gridmod_default);
      if (gridmod_default == 'True' || gridmod_default == '1') {
        $(this).contents('input').val('True');
        $(this).contents('input').attr('checked', 'checked');
      } else {
        $(this).contents('input').val('False');
        $(this).contents('input').removeAttr('checked');
      }
    });
  });

  // INPUT RADIO
  // These are handled as INPUT SELECTs for screen real-estate reasons

  // INPUT TEXTAREA
  // We are ignoring TextArea for now, as there are several complications including:
  //  * Rendering is handled differently to other fields in the report form
  //  * TextAreas support Wiki formatting so would need to use the Wiki engine


  // Set up the change callbacks for each field type on the page

  $(".gridmod_form").each(function () {
    $(this).change(function () {
      var ticket_field = $(this).attr('name');
      var ticket_number = $(this).parent('td').siblings('.ticket, .id').text();
      ticket_number = ticket_number.replace(/[^\d]/g, '');

      // React differently depending on the field type
      // Note: SELECT takes care of RADIO as well, as we convert RADIOs to SELECTs on the page
      // for screen real-estate reasons - there should always be a 'selected' value though for
      // the RADIO 'SELECT's
      // Note: We are ignoring TextArea for now, as there are several complications including:
      //   * Rendering is handled differently in the report form
      //   * TextAreas support Wiki formatting so would need to use the Wiki engine

      var new_value;
      if ($(this).is('select')) {
        new_value = $(this).find('option:selected').text();
      } else if ($(this).attr('type') == 'text') {
        new_value = $(this).val();
      } else if ($(this).attr('type') == 'checkbox') {
        // force toggle - this needs investigating, shouldn't the browser do it? why do we need to do it here?
        new_value = $(this).val();
        if (new_value == 'True') {
          new_value = 'False';
        } else {
          new_value = 'True';
        }
      }

      console.log("Changing " + ticket_field + " for #" + ticket_number + " to " + new_value + ".");
      var url = $('link[rel="search"]').attr('href').replace(/\/search/, '');
      url += '/gridmod/update';
      var data = {'ticket': ticket_number};
      data[ticket_field] = new_value;
      var chromePath = $("script[src*='gridmod']").attr("src").replace("gridmod.js", "");
      var image = $(this).parent().find("img").get(0) || document.createElement('img');
      image.src = chromePath + 'loading.gif';
      $(image).insertAfter(this);
      $.ajax({
        // Although semantically this should be POST, that doesn't seem to work.
        'type': "GET",
        'url': url,
        'data': data,
        'success': function () {
          console.log('Updated #' + ticket_number + '.');
          image.src = chromePath + 'ok.png';
        },
        'error': function () {
          console.log('Failed to update #' + ticket_number + '.');
          image.src = chromePath + 'error.png';
        }
      });

    });
  });
});
