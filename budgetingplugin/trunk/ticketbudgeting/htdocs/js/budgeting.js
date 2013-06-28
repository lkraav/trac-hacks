/*
 * Hides the Table of all Entry row by changing the visibility of an
 * parent elment by the id hiddenbudgettable
 */
function hideTable() {
	$('#budget_table').hide();
}

function showTable() {
	$('#budget_table').show();
}

function getBudgetRows() {
	return $('#budget_container').children('tr');
}

/*
 * Adding a new entry row to the defined tbody table element at the bottom of
 * the list
 */
function addBudgetRow() {
	// Getting the values of the types - select by reading an hidden
	// Element with the id selectTypes in the html page
	if ($('#selectTypes').length != 0) {
		var types = $('#selectTypes').html();
		types = types.split('|');
	}
	var def_type_index = 0;
	if ($('#def_type').length != 0) {
		var def_type = $('#def_type').html();
		if (def_type != -1) {
			for ( var i = 0; i < types.length; i++) {
				if (types[i] == def_type) {
					def_type_index = i;
					break;
				}
			}
		}
	}

	// Getting the name-select values from html
	if ($('#selectNames').length != 0)
		var names = $('#selectNames').html();
	names = names.split('|');
	// Getting the default values for Name, Estimation, Cost and State
	var def_name_index = 0;
	if ($('#def_name').length != 0)
		var def_name = $('#def_name').html();
	for ( var i = 0; i < names.length; i++) {
		if (names[i] == def_name) {
			def_name_index = i;
			break;
		}
	}
	if ($('#def_estimation').length != 0)
		var def_estimation = $('#def_estimation').html();
	if ($('#def_cost').length != 0)
		var def_cost = $('#def_cost').html();
	if ($('#def_status').length != 0)
		var def_status = $('#def_status').html();

	var trElements = getBudgetRows();
	
	// initialise the rowcounter by the number of the last row
	var rowCounter = 1;
	if (trElements && trElements.length > 0) {
		rowCounter = trElements[trElements.length - 1].id.split('-')[2];
		rowCounter++;
	}

	var tableRow = document.createElement('tr');
	tableRow.id = 'budgeting-row-' + rowCounter;
	$('#budget_container').append(tableRow);

	// Adding column by column to the row element
	var col_names = new Array('username', 'type', 'estimation', 'cost', 'status',
			'comment')
	for (var column = 0; column < col_names.length; column++) {
		var td = document.createElement('td');
		tableRow.appendChild(td);
		var columnElement;
		switch (column) {
		case 0:
			// Select NAME Column Position 1
			columnElement = getSelect(names);
			columnElement.selectedIndex = def_name_index;
			break;
		case 1:
			// Select TYPES Column Position 2
			columnElement = getSelect(types);
			columnElement.selectedIndex = def_type_index;
			break;
		case 2:
			// Estimation
			columnElement = document.createElement('input');
			columnElement.setAttribute('value', def_estimation);
			columnElement.size = 10;
			break;
		case 3:
			// Cost
			columnElement = document.createElement('input');
			columnElement.setAttribute('value', def_cost);
			columnElement.size = 10;
			break;
		case 4:
			// State
			columnElement = document.createElement('input');
			columnElement.setAttribute('value', def_status);
			columnElement.size = 10;
			break;
		case 5:
			// Comment
			columnElement = document.createElement('input');
			columnElement.size = 60;
			break;
		default:
			break;
		}
		columnElement.name = 'budgeting-' + rowCounter + '-'
				+ col_names[column] + "-insert";
		td.appendChild(columnElement);
	}
	// Adding a Delete Button to the end of the row
	deleteButtonElement = document.createElement('td');
	deleteButtonElement.innerHTML = '<div class="inlinebuttons">'
			+ '<input type="button" class="deleteBudgetRow"'
			+ ' name="deleteRow' + rowCounter + '" onclick="deleteRow('
			+ rowCounter + ')"' + ' value = "&#x2718"/></div>';
	tableRow.appendChild(deleteButtonElement);
	// Change hidden tbody elment to be visible
	showTable();
}

/*
 * Creates a new Select Element with the optionsvalues which were given by the
 * submitted Array
 */
function getSelect(optionArray) {
	if (optionArray == null)
		return null;

	var columnElement = document.createElement('select');
	for (arrayPosition = 0; arrayPosition < optionArray.length; arrayPosition++) {
		newOption = document.createElement('option');
		newOption.text = optionArray[arrayPosition];
		try {// standards compliant; doesn't work in IE
			columnElement.add(newOption, null);
		} catch (ex) { // just ie
			columnElement.add(newOption, columnElement.selectedIndex);
		}
	}
	columnElement.setAttribute("class","budgeting_select")
	return columnElement
}

/*
 * Marks a Row, by the given rowid, as to delete by adding a style attribut
 * visibility by the value none to the parent tr Element. All fields
 * additionally will gets an Prefix DEL on the beginning of the Name: NewName =
 * DEL + oldName The Prefix DEL is necessary to identify deleted rows in further
 * processing performed by the python plugin
 */
function deleteRow(rowID) {
	if (rowID < 0)
		return;

	var row = $("#budgeting-row-" + rowID);
	row.hide();
	var rowElems = row.find("select , input");
	for ( var i in rowElems) {
		rowElems[i].name = "budgeting-"
				+ (rowElems[i].name + '').match(/\d+-\w+/) + "-delete";
	}

	// This logic ist responsible for hidding the complete tbody element, if no
	// further row ist visible or rather not deleted
	if ($('#budget_container tr[style!="display: none;"]').length == 0) {
		hideTable();
	}
}

function update(field) {
	$("[name='" + field + "']").attr('name', field + '-update');
}