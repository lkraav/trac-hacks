/*global document, window, event */

/*
@source: http://trac-hacks.org/wiki/CcSelectorPlugin

@licstart  The following is the entire license notice for the
JavaScript code in this page.

Copyright (C) 2009 Vladislav Naumov
Copyright (C) 2010 Steffen Hoffmann

The JavaScript code in this page is free software: you can
redistribute it and/or modify it under the terms of the GNU
General Public License (GNU GPL) as published by the Free Software
Foundation, either version 3 of the License, or (at your option)
any later version.  The code is distributed WITHOUT ANY WARRANTY;
without even the implied warranty of MERCHANTABILITY or FITNESS
FOR A PARTICULAR PURPOSE.  See the GNU GPL for more details.

As additional permission under GNU GPL version 3 section 7, you
may distribute non-source (e.g., minimized or compacted) forms of
that code without the copy of the GNU GPL normally required by
section 4, provided you include this license notice and a URL
through which recipients can access the Corresponding Source.

@licend  The above is the entire license notice
for the JavaScript code in this page.
*/

// automatically add button on load:
jQuery(function($) {
  // populate the list of default developers that should always be there
  function get_default_devs() {
    var retval = new Array();
    var devs = new Array();

    var devs_list=document.getElementById('cc_developers');
    for (var i=0; i<devs_list.childNodes.length; i++) {
      var d = devs_list.childNodes[i];
      if (d.title) {
        var dev = new Array()
        dev.title = d.title
        dev.name = d.getAttribute("data-name")
        dev.email = d.getAttribute("data-email")
        devs.push(dev);
      }
    }

    for (i in devs) {
      if (devs.hasOwnProperty(i)) {
        devs[i].selected = false;  // start as unchecked
        retval[devs[i].title] = devs[i]
      }
    }

    return retval;
  }


  // this function shows selection pop-up
  function show_selection(event) {
    var thisurl = document.location.href;

    var nurl = thisurl.split('/');
    if ( nurl.pop().indexOf('newticket') !== 0) {
      // remove one more component, unless we're doing "new ticket"
      nurl.pop();
    }
    nurl = nurl.join('/');
    nurl = nurl + "/cc_selector";

    window.open(nurl,
      "cc_selector",
      "width=300,height=400,location=no,scrollbars=yes,resizable=yes,left="
        + event.screenX + ",top=" + event.screenY
    );
    return;
  }


  function guess_cc_field() {
    var doc = document;

    // are we in the popup?
    if (window.opener && ! window.opener.closed &&
        document.getElementById('cc_developers')) {
      doc = window.opener.document;
    }

    var cc_field = "cc";
    if (doc.getElementById(cc_field)) {
      return cc_field;
    }

    cc_field = "field-cc";
    if (doc.getElementById(cc_field)) {
      return cc_field;
    }
  }

  // split Cc string into object
  function split_field(fieldid) {
    var retval = get_default_devs();

    var f = document.getElementById(fieldid);
    if ( ! f ) {
      // find parent window
      f = window.opener.document.getElementById(fieldid);
    }
    var str = f.value;
    str = str.replace(/,\s*/g, ' ');
    str = str.replace(/\s+/g, ' ');

    var arr = str.split(' ');

    for (var w in arr) {
      if (arr.hasOwnProperty(w) && arr[w].length ) {
        if (retval.hasOwnProperty(arr[w])) {
          retval[arr[w]].selected = true;
        } else {
          retval[arr[w]] = new Object();
          retval[arr[w]].selected = true;
          retval[arr[w]].title = arr[w];
        }
      }
    }
    return retval;
  }


  // checkbox onclick reaction - set Cc value
  function cc_toggle(field, ckbox) {
    var name = ckbox.name;
    var checked = ckbox.checked;
    var devs = split_field(field);

    // we now need to create object if it doesn't exist
    // (was removed from line manually?)
    if (devs.hasOwnProperty(name)) {
      devs[name].selected = checked;
    }
    else {
      devs[name] = new Object();
      devs[name].selected = checked;
      devs[name].title = name;
    }
    // generate new value

    var activedevs = [];
    for (var d in devs) {
      if (devs[d].selected) {
        activedevs.push(devs[d].title);
      }
    }
    var newval = activedevs.join(', ');

    var target = document.getElementById(field);
    if ( !target ){
      // find target in parent window
      target = window.opener.document.getElementById(field);
    }
    target.value = newval;
  }


  // Fill given div with Cc field contents
  function split_into_checkboxes(fromid, toid) {
    var t = document.getElementById(toid);

    var devs = split_field(fromid);

    // per list item text prepended once per list
    var cc_to = document.getElementById('cc_to').getAttribute('title');

    for (var w in devs) {
      if (!devs.hasOwnProperty(w)) {
        continue;
      }

      var dev = devs[w];

      var id_ck = "cc_" + w
      var ck = document.createElement('input')
      var lb = document.createElement('label')

      ck.setAttribute("type", "checkbox");
      ck.setAttribute("id", id_ck);
      ck.setAttribute("name", w);
      ck.onclick = function () { cc_toggle(fromid, this); };
      if (dev.selected) {
          ck.setAttribute('checked', true );
          ck.setAttribute('defaultChecked', true );
      }

      lb.setAttribute("for", id_ck);

      // make title / mailto: link / pop-up text
      lb.appendChild(document.createTextNode(' ' + cc_to + ' '));

      var link;
      if (dev.email) {
        // got email? make href
        link = document.createElement('A');
        link.setAttribute('href', 'mailto:' + dev.email);
      }
      else {
        // otherwise, plain span
        link = document.createElement('SPAN');
      }

      var label_name = dev.title;
      if (dev.name) {
        // if also have a full name, show it ...
        // ... on mouse-over
        var tip_name = dev.name;
        if (document.getElementById('show_fullname')) {
          // ... as list element
          label_name = dev.name;
          tip_name = dev.title;
        }
        link.setAttribute("title", tip_name);
      }
      link.appendChild(document.createTextNode(label_name));

      lb.appendChild(link);

      t.appendChild(document.createElement('br'));
      t.appendChild(ck);
      t.appendChild(lb);
    }
  }

  // onload function. Used in both ticket window and in pop-up.
  function afterLoad() {
    // guess fromid (possible values: cc, from-cc)
    var cc_field = guess_cc_field();

    var nurl = document.location.href.split('/');
    if ( document.getElementById('cc_developers') ) {
      // we're in pop-up window
      // create checkboxes
      split_into_checkboxes(cc_field, 'ccdiv');
    }
    else {
      // we're on ticket window
      var p = document.getElementById(cc_field);

      if ( ! p ) {
        // only act in editor mode, that is not always available,
        // i.e. without proper permission/before authentication
        return;
      }

      if (p.type != "text") {
        // we only want to show button for text fields
        // (there also is a checkbox variant)
        return;
      }

      p = p.parentNode;

      // create button
      var ccb = document.createElement('input');
      var ccb_label = _("Extended Cc selection");
      ccb.setAttribute("type", "button");
      ccb.setAttribute("id", "ccbutton");
      ccb.setAttribute("name", "ccbutton");
      ccb.setAttribute("value", ">");
      ccb.setAttribute("alt", ccb_label);
      ccb.setAttribute("title", ccb_label);
      p.appendChild(ccb);
    }
  }

  // multiple browser compliant 'onload' trigger
  afterLoad();

  // custom 'click' event (for getting position to put pop-up there)
  $('#ccbutton').click(function(event) {
    show_selection(event);
  });
});
