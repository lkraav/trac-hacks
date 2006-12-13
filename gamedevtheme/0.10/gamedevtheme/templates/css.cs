/* Main navigation bar */
#mainnav {
	background: #800;
	border: 0;
	margin-top: 8px;
	margin-bottom: 0px;
	padding-top: 4px;
	padding-bottom: 4px;
	padding-right: 16px;
}
#mainnav li {
	background: blue
	border: 4px solid #800;
	margin: 2px;
}
#mainnav :link, #mainnav :visited {
	background: #fff;
	/* border: 2px solid #800; */
	border: 0px;
}
#mainnav :link:hover, #mainnav :visited:hover {
	background: gray;
	/* border: 2px solid #800; */
	border: 0px;
}
#mainnav .active :link, #mainnav .active :visited {
	background: #ff8000;
	/* border: 2px solid #800; */
	border: 0px;
}
#mainnav .active :link:hover, #mainnav .active :visited:hover {
	background: #ccc;
	/* border: 2px solid #800; */
	border: 0px;
}

div.poll {
	/* float: right;*/
	/* width: 30%; */
}

#main {
	background-image: url(<?cs var:chrome.href ?>/theme/background.jpg);
	background-repeat: no-repeat;
	padding: 0px;
}

#ctxtnav {
	padding-top: 4px;
}

#content {
	padding-left: 10px;
	padding-right: 10px;
}

a.subversion {
        font-size: small;
        border-bottom-style: dotted;
        border-bottom-width: 1px;
        text-decoration: none;
}

#sitenav {
	background: #800;
	width: 100%;
	padding: 2px;
}

#sitenav a {
	background: transparent;
	color: white;
	margin: 4px;
}

#sitenav a:hover {
	background: transparent;
	color: gray;
}
