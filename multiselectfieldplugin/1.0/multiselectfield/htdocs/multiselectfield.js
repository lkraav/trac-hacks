
function createMultiselectField(field) {
	// Assumes that the previous (hidden) element contains the actual data.
	var dataField = field.prev();
	var uiField = field;

	function updateChosenField() {
		var value = dataField.attr('value');
		// The value of multiselectfieldDelimiter is passed to js from python.
		var options = value.split(multiselectfieldDelimiter);

		var length = options.length;
		for (var optionIndex = 0; optionIndex < length; optionIndex++) {
			if (options[optionIndex] == '') {
				continue;
			}
			uiField.children("option[value='" + options[optionIndex] + "']").attr('selected', 'selected');
		}
	}

	updateChosenField();

	// Listen to changes in the UI.
	uiField.chosen().change(function(event) {
		var values = jQuery(event.target).val();
		if (values === null)  {
			dataField.attr('value', '');
		} else {
			dataField.attr('value', values.join(multiselectfieldDelimiter));
		}
	});

	// Listen to changes in the data (like revert).
	dataField.change(function(event) {
		updateChosenField();
		uiField.trigger("chosen:updated");
	});
}

jQuery(document).ready(function($) {
	jQuery('.multiselect').each(function(i) {
		createMultiselectField(jQuery(this));
	});
});
