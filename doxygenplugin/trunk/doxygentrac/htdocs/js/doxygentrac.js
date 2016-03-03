function toggle_display_next(node) {
    var n = node.nextElementSibling.style;
    n.display = n.display=='none' ? 'block' : 'none'
}

function check_dir(form, name) {
        var d = form.elements[name]
        var def = d.previousElementSibling
        // check for a prefix default value
        if (def.tagName == 'SPAN') {
      		// add it in front, except if already there
		var r = new RegExp('^' + def.firstChild.data)
		if (!r.test(d.value)) {
			d.value = def.firstChild.data + d.value;
		}
	}
        if (/[.][.]/.test(d.value) || !d.value) {
      		alert("'" + d.value + "': incorrect value for " + name)
      		return false
        }
	return true
}
