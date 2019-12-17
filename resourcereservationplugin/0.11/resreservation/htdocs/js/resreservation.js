/*- coding: utf-8
 *
 * Copyright (C) 2010 Roberto Longopbardi - seccanj@gmail.com
 *
 * This software is licensed as described in the file COPYING, which
 * you should have received as part of this distribution.
 */

function editResourceReservation(evt) {
    var evtTarget = getEventTarget(evt);
    var resDate = evtTarget.getAttribute('name');
    
    /* Avoid the first cell, the one with the resource name */
    if (resDate !== 'resourceNameCell') {
        var currAssignee = evtTarget.title ? evtTarget.title : '';
        var resourceName = evtTarget.parentNode.getAttribute('name');

        var needChange = true;
        if (currAssignee && currAssignee.length > 0 && currAssignee != currUser) {
            if (override) {
                newAssignee = currUser;
                newClass = 'resOwned';
            } else {
                needChange = false;
            }
        } else {
            if (!currAssignee || currAssignee.length == 0) {
                newAssignee = currUser;
                newClass = 'resOwned';
            } else { /* currAssignee == currUser */
                newAssignee = '';
                newClass = '';
            }
        }
        
        if (needChange) {
            changeReservation(evtTarget, resourceName, resDate, currAssignee, newAssignee, newClass);
        }
        
        /* setTimeout('window.location="'+window.location+'"', 500); */
    }
}

function changeReservation(node, resourceName, resDate, currAssignee, newAssignee, newClass) {
    xmlhttp = getXmlHttp();

    var url = baseLocation+'/resreservation?command=assignresource&resourceType='+resourceType+'&resourceName='+resourceName+
        '&resDate='+resDate+'&currAssignee='+currAssignee+'&newAssignee='+newAssignee+'&override='+override;
    
    xmlhttp.open("GET", url, false);
    xmlhttp.send(null);
    var responseText = xmlhttp.responseText;
    
    var jsonString = responseText.substring(responseText.indexOf('<div id="response">')+'<div id="response">'.length, 
        responseText.indexOf("</div>"));

    var resultObj = eval("("+jsonString+")");
    
    if (resultObj['result']) {
        node.className = newClass;
        node.title = newAssignee;
    }
}

function addResource() {
    xmlhttp = getXmlHttp();

    var resName = document.getElementById('resName').value;
    if (!resName || resName.length == 0) {
		document.getElementById('errorMsgSpan').innerHTML = messages['name_help'];
    } else {
    	resName = stripLessSpecialChars(resName); 
    	
    	if (resName.length > 30 || resName.length < 4) {
    		document.getElementById('errorMsgSpan').innerHTML = messages['length_error'];
    	} else {
            var url = baseLocation+'/resreservation?command=addresource&resourceType='+resourceType+'&resourceName='+resName;
        
            xmlhttp.open("GET", url, false);
            xmlhttp.send(null);
            var responseText = xmlhttp.responseText;
    
            setTimeout('window.location="'+window.location+'"', 500);
        }
    }
}

function getXmlHttp() {
    if (window.XMLHttpRequest) {
        /* code for IE7+, Firefox, Chrome, Opera, Safari */
        xmlhttp = new XMLHttpRequest();
    } else {
        /* code for IE6, IE5 */
        xmlhttp = new ActiveXObject("Microsoft.XMLHTTP");
    }
    
    return xmlhttp;
}

function stripLessSpecialChars(str) {
    result = str.replace(/[;#&\?]/g, '');
    return result;
}

function getEventTarget(evt) {
    evt = evt || window.event;
    var targ = evt.target || evt.srcElement;
    if (targ.nodeType == 3) // defeat Safari bug
        targ = targ.parentNode;
        
    return targ;
}
