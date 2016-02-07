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
