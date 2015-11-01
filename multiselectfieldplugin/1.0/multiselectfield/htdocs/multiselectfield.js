
function createMultiselectField(field) {
	// Assumes that the previous (hidden) element contains the actual data.
	var dataField = field.prev();
	var uiField = field;

	function updateUiField() {
		var value = dataField.attr('value');
		// The value of multiselectfieldDelimiter is passed to js from python.
		var options = value.split(multiselectfieldDelimiter);
		uiField.val(options);
	}

	updateUiField();

	if (!multiselectfieldSimple) {
		// Use improved "chosen" selection box.
		uiField.chosen();
	}

	// Listen to changes in the UI.
	uiField.change(function(event) {
		var values = jQuery(event.target).val();
		if (values === null)  {
			dataField.attr('value', '');
		} else {
			dataField.attr('value', values.join(multiselectfieldDelimiter));
		}
	});

	// Listen to changes in the data (like revert).
	dataField.change(function(event) {
		updateUiField();
		if (!multiselectfieldSimple) {
			uiField.trigger("chosen:updated");
		}
	});
}

jQuery(document).ready(function($) {
	jQuery('.multiselect').each(function(i) {
		createMultiselectField(jQuery(this));
	});
});
