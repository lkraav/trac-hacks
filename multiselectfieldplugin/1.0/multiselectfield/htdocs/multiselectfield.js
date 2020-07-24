jQuery(function($) {
  $("input[type='text']").each(function() {
    var $field = $(this);
    name = $field.attr('name').slice(6);
    if (Object.keys(multiselectFields).indexOf(name) === -1) {
      return;
    }

    $multi = $(
      "<select multiple='multiple' class='multiselect' style='width:100%' />"
    )
    multiselectFields[name].forEach(function (opt) {
      $multi.append(new Option(opt, opt));
    });
    $field.prop('style', 'display:none').after($multi);

    function updateUiField() {
      var value = $field.attr('value');
      if (value) {
        // The value of multiselectfieldDelimiter is passed to js from python.
        var options = value.split(multiselectfieldDelimiter);
        $multi.val(options);
      }
    }

    updateUiField();

    if (!multiselectfieldSimple) {
      // Use improved "chosen" selection box.
      $multi.chosen();
    }

    // Listen to changes in the UI.
    $multi.change(function(event) {
      var values = $(event.target).val();
      if (values === null)  {
        $field.attr('value', '');
      } else {
        $field.attr('value', values.join(multiselectfieldDelimiter));
      }
    });

    // Listen to changes in the data (like revert).
    $field.change(function(event) {
      updateUiField();
      if (!multiselectfieldSimple) {
        $multi.trigger("chosen:updated");
      }
    });
  });
});
