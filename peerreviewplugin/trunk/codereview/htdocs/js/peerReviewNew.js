var GLOBAL_lineStart = -1;
var GLOBAL_lineEnd = -1;

//Colorizes the tables according to Trac standards
function colorTable(txt){
    var table = document.getElementById(txt);
    var loop = 0;
    for (; loop < table.rows.length; loop++) {
        var row = table.rows[loop];
        if (loop % 2 == 0) {
            row.className = 'odd';
        } else {
            row.className = 'even';
        }
    }
}

//adds a row to the table with txt as the text in the row
function addrow(txt)
{
    var tbl = document.getElementById('myuserbody');
    var lastRow = tbl.rows.length;
    var row = tbl.insertRow(lastRow);

    // We will append the new username to the ReviewersSelected hidden input
    var users = document.getElementById('ReviewersSelected');
    //document.setElementByName('ReviewersSelected', users + "#" + txt);
    users.setAttribute('value', users.value + txt + "#");

    row.id = txt + 'id';
    var cellLeft = row.insertCell(0);
    cellLeft.setAttribute('value', txt);
    cellLeft.innerHTML = "<" + "a href=\"javascript:removeuser('" + txt + "')\">" + txt + "</a>";
    row.appendChild(cellLeft);
}

//takes a user from the dropdown, adds them to the table, and deletes from the dropdown
function adduser()
{
    var dropdown = document.getElementById('Reviewers');
    var tbl = document.getElementById('myuserbody');

    if((tbl.rows.length == 1) && (tbl.rows[0].getAttribute("id") == "No Users"))
        checkEmpty(1, 'myuserbody');

    addrow(dropdown.options[dropdown.selectedIndex].text);
    dropdown.options[dropdown.selectedIndex] = null;

    if (dropdown.options.length == 0) {
        // No users left
        dropdown.options[0] = new Option('--All users exhausted--','-1');
        document.getElementById("adduserbutton").disabled = true;
        document.getElementById("adduserbutton").style.color = "";
    }

    colorTable('myuserbody');
}

//takes a user from the table, adds them to the dropbox, and deletes from the table
function removeuser(txt) {
    var dropdown = document.getElementById('Reviewers');

    if (dropdown.options[0].value == '-1') {
        dropdown.options[0] = new Option(txt, '0');
        document.getElementById("adduserbutton").disabled = false;
        document.getElementById("adduserbutton").style.color = "#000000";
    } else {
        dropdown.options[dropdown.options.length] = new Option(txt, '0');
    }

    //remove the user from the post value
    var users = document.getElementById('ReviewersSelected');
    var tokens = users.value.split("#");
    var newusers = "";
    for (var i=0; i < tokens.length-1; i++) {
        if (tokens[i] == txt)
            continue;
        newusers += tokens[i] + "#";
    }

    users.setAttribute('value', newusers);

    // delete the row containing the txt from the table
    var table = document.getElementById('myuserbody');

    // remove row
    var loop = 0;
    for (loop = 0; loop < table.rows.length; loop++) {

        var row = table.rows[loop];
        var cell = row.cells[0];
        if (row.id == txt + 'id') {
            table.deleteRow(loop);
            loop--;
            break;
        }
    }

    colorTable('myuserbody');

    if (table.rows.length == 0)
        checkEmpty(0, 'myuserbody');
}

//Checks for an empty table to label it as such
function checkEmpty(num, itemID) {
    var table = document.getElementById(itemID);

    switch (num) {
    case 0:
        //Table is now empty
        table.insertRow(0);
        table.rows[0].setAttribute('id', "No Users");
        table.rows[0].className = 'even';
        var cellLeft = table.rows[0].insertCell(0);
        cellLeft.innerHTML = "No users have been added to the code review.";
        table.rows[0].appendChild(cellLeft);
        break;
    case 1:
        //Need to add things to the table, get rid of No Users row
        table.deleteRow(0);
        break;
    default :
        alert("Error in CheckEmpty function");
    }
}

function validateInput(form) {
    if (form.Name.value == "") {
        alert("You must specify a code review name.");
        return false;
    }

    if (form.FilesSelected.value == "") {
        alert("You must select at least one file.");
        return false;
    }

    if (form.ReviewersSelected.value == "") {
        alert("You must select at least one user.");
        return false;
    }

    return true;
}

function lineEnter(e)
{
    if(e.keyCode == 13 || e.keyCode == 3)
    {
        addButtonEnable();
        if(e.stopPropagation)
            e.stopPropagation();
        if(e.preventDefault)
            e.preventDefault();
        e.cancelBubble = true;
        event.returnValue = false;
        event.cancel = true;
    }
}

//Sets the line number ranges in the file browser
function setLineNum(num)
{
    var box1 = document.getElementById('lineBox1');
    var box2 = document.getElementById('lineBox2');
    if(box1 == null || box2 == null)
        return;
    if(lastPick == null)
    {
        box1.value = num;
    }
    else if(lastPick >= num)
    {
        box1.value = num;
        box2.value = lastPick;
    }
    else if(lastPick < num)
    {
        box1.value = lastPick;
        box2.value = num;
    }
    lastPick = num;
    addButtonEnable();
}


//Enable the Add File button when a correct file, revision, and line number range is chosen

function addButtonEnable()
{
    var i = 1;
    var temp = null;
    var box1 = document.getElementById('lineBox1');
    var box2 = document.getElementById('lineBox2');
    var addButton = document.getElementById('addFileButton');

    if(box1 == null || box2 == null || addButton == null)
        return;

    addButton.disabled = true;
    addButton.style.color = "";

    if(GLOBAL_lineStart != -1 && GLOBAL_lineEnd != -1)
    {
        for(i = GLOBAL_lineStart; i <= GLOBAL_lineEnd; i++)
        {
            temp = document.getElementById('L' + i);
            if(temp != null)
                temp.innerHTML = "<" + "a href=\"javascript:setLineNum(" + i + ")\">" + i + "</a>";
        }
    }

    GLOBAL_lineStart = -1;
    GLOBAL_lineEnd = -1;

    if(box1.value == "" || box2.value == "" || isNaN(box1.value) || isNaN(box2.value))
        return;

    var start = parseInt(box1.value);
    var end = parseInt(box2.value);
    if(start < 1)
        start = 1;
    if(end < 1)
        end = 1;
    if(start > end)
    {
        i = start;
        start = end;
        end = i;
    }

    if(document.getElementById('L' + start) == null)
        return;

    for(i=start; i <= end; i++)
    {
        temp = document.getElementById('L' + i);
        if(temp != null)
        {
            temp.innerHTML = "<" + "a href=\"javascript:setLineNum(" + i + ")\"><font color=red><b>" + i + "</b></font></a>"
        }
        else
        {
            end = i-1;
        }
    }

    GLOBAL_lineStart = start;
    GLOBAL_lineEnd = end;

    box1.value = start;
    box2.value = end;

    addButton.disabled = false;
    addButton.style.color = "#000000";
}
