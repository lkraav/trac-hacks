<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en">
<head>
<script type="text/javascript">
//<![CDATA[
var version = {major: 2, minor: 1, revision: 3, date: new Date("Nov 3, 2006"), extensions: {}};
//]]>
</script>
<!--
TiddlyWiki 2.1.3 by Jeremy Ruston, (jeremy [at] osmosoft [dot] com)

Copyright (c) Osmosoft Limited 2004-2006

Redistribution and use in source and binary forms, with or without modification,
are permitted provided that the following conditions are met:

Redistributions of source code must retain the above copyright notice, this
list of conditions and the following disclaimer.

Redistributions in binary form must reproduce the above copyright notice, this
list of conditions and the following disclaimer in the documentation and/or other
materials provided with the distribution.

Neither the name of the Osmosoft Limited nor the names of its contributors may be
used to endorse or promote products derived from this software without specific
prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY
EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES
OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT
SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED
TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH
DAMAGE.
-->
<meta http-equiv="Content-Type" content="text/html;charset=utf-8"/>
<!--PRE-HEAD-START-->
<link rel='alternate' type='application/rss+xml' title='RSS' href='index.xml'/>
<!--PRE-HEAD-END-->
<title> TiddlyWiki - a reusable non-linear personal web notebook </title>
<script type="text/javascript">
//<![CDATA[
// ---------------------------------------------------------------------------------
// Configuration repository
// ---------------------------------------------------------------------------------

// Miscellaneous options
var config = {
	numRssItems: 20, // Number of items in the RSS feed
	animFast: 0.12, // Speed for animations (lower == slower)
	animSlow: 0.01, // Speed for EasterEgg animations
	cascadeFast: 20, // Speed for cascade animations (higher == slower)
	cascadeSlow: 60, // Speed for EasterEgg cascade animations
	cascadeDepth: 5, // Depth of cascade animation
	displayStartupTime: false // Whether to display startup time
	};

// Messages
config.messages = {
	messageClose: {},
	dates: {}
};

// Options that can be set in the options panel and/or cookies
config.options = {
	chkRegExpSearch: false,
	chkCaseSensitiveSearch: false,
	chkAnimate: true,
	chkSaveBackups: true,
	chkAutoSave: false,
	chkGenerateAnRssFeed: false,
	chkSaveEmptyTemplate: false,
	chkOpenInNewWindow: true,
	chkToggleLinks: false,
	chkHttpReadOnly: true,
	chkForceMinorUpdate: false,
	chkConfirmDelete: true,
	chkInsertTabs: false,
	txtBackupFolder: "",
	txtMainTab: "tabTimeline",
	txtMoreTab: "moreTabAll",
	txtMaxEditRows: "30"
	};
	
// List of notification functions to be called when certain tiddlers are changed or deleted
config.notifyTiddlers = [
	{name: "StyleSheetLayout", notify: refreshStyles},
	{name: "StyleSheetColors", notify: refreshStyles},
	{name: "StyleSheet", notify: refreshStyles},
	{name: "StyleSheetPrint", notify: refreshStyles},
	{name: "PageTemplate", notify: refreshPageTemplate},
	{name: "SiteTitle", notify: refreshPageTitle},
	{name: "SiteSubtitle", notify: refreshPageTitle},
	{name: "ColorPalette", notify: refreshColorPalette},
	{name: null, notify: refreshDisplay}
	];

// Default tiddler templates
var DEFAULT_VIEW_TEMPLATE = 1;
var DEFAULT_EDIT_TEMPLATE = 2;
config.tiddlerTemplates = {
	1: "ViewTemplate",
	2: "EditTemplate"
	};

// More messages (rather a legacy layout that shouldn't really be like this)
config.views = {
	wikified: {
		tag: {}
		},
	editor: {
		tagChooser: {}
		}
	};

// Macros; each has a 'handler' member that is inserted later
config.macros = {
	today: {},
	version: {},
	search: {sizeTextbox: 15},
	tiddler: {},
	tag: {},
	tags: {},
	tagging: {},
	timeline: {},
	allTags: {},
	list: {
		all: {},
		missing: {},
		orphans: {},
		shadowed: {}
		},
	closeAll: {},
	permaview: {},
	saveChanges: {},
	slider: {},
	option: {},
	newTiddler: {},
	newJournal: {},
	sparkline: {},
	tabs: {},
	gradient: {},
	message: {},
	view: {},
	edit: {},
	tagChooser: {},
	toolbar: {},
	br: {},
	plugins: {},
	refreshDisplay: {},
	importTiddlers: {}
	};

// Commands supported by the toolbar macro
config.commands = {
	closeTiddler: {},
	closeOthers: {},
	editTiddler: {},
	saveTiddler: {hideReadOnly: true},
	cancelTiddler: {},
	deleteTiddler: {hideReadOnly: true},
	permalink: {},
	references: {},
	jump: {}
	};

// Browser detection... In a very few places, there's nothing else for it but to
// know what browser we're using.
config.userAgent = navigator.userAgent.toLowerCase();
config.browser = {
	isIE: config.userAgent.indexOf("msie") != -1 && config.userAgent.indexOf("opera") == -1,
	ieVersion: /MSIE (\d.\d)/i.exec(config.userAgent), // config.browser.ieVersion[1], if it exists, will be the IE version string, eg "6.0"
	isSafari: config.userAgent.indexOf("applewebkit") != -1,
	isBadSafari: !((new RegExp("[\u0150\u0170]","g")).test("\u0150")),
	firefoxDate: /Gecko\/(\d{8})/i.exec(config.userAgent), // config.browser.firefoxDate[1], if it exists, will be Firefox release date as "YYYYMMDD"
	isOpera: config.userAgent.indexOf("opera") != -1,
	isLinux: config.userAgent.indexOf("linux") != -1,
	isUnix: config.userAgent.indexOf("x11") != -1,
	isMac: config.userAgent.indexOf("mac") != -1,
	isWindows: config.userAgent.indexOf("win") != -1
	};

// Basic regular expressions
config.textPrimitives = {
	upperLetter: "[A-Z\u00c0-\u00de\u0150\u0170]",
	lowerLetter: "[a-z0-9_\\-\u00df-\u00ff\u0151\u0171]",
	anyLetter:   "[A-Za-z0-9_\\-\u00c0-\u00de\u00df-\u00ff\u0150\u0170\u0151\u0171]",
	anyLetterStrict: "[A-Za-z0-9\u00c0-\u00de\u00df-\u00ff\u0150\u0170\u0151\u0171]"
	};
if(config.browser.isBadSafari)
	config.textPrimitives = {
		upperLetter: "[A-Z\u00c0-\u00de]",
		lowerLetter: "[a-z0-9_\\-\u00df-\u00ff]",
		anyLetter:   "[A-Za-z0-9_\\-\u00c0-\u00de\u00df-\u00ff]",
		anyLetterStrict: "[A-Za-z0-9\u00c0-\u00de\u00df-\u00ff]"
		}
config.textPrimitives.sliceSeparator = "::";
config.textPrimitives.urlPattern = "[a-z]{3,8}:[^\\s:'\"][^\\s'\"]*(?:/|\\b)";
config.textPrimitives.unWikiLink = "~";
config.textPrimitives.wikiLink = "(?:(?:" + config.textPrimitives.upperLetter + "+" +
												config.textPrimitives.lowerLetter + "+" +
												config.textPrimitives.upperLetter +
												config.textPrimitives.anyLetter + "*)|(?:" +
												config.textPrimitives.upperLetter + "{2,}" +
												config.textPrimitives.lowerLetter + "+))";

config.textPrimitives.cssLookahead = "(?:(" + config.textPrimitives.anyLetter + "+)\\(([^\\)\\|\\n]+)(?:\\):))|(?:(" + config.textPrimitives.anyLetter + "+):([^;\\|\\n]+);)";
config.textPrimitives.cssLookaheadRegExp = new RegExp(config.textPrimitives.cssLookahead,"mg");

config.textPrimitives.brackettedLink = "\\[\\[([^\\]]+)\\]\\]";
config.textPrimitives.titledBrackettedLink = "\\[\\[([^\\[\\]\\|]+)\\|([^\\[\\]\\|]+)\\]\\]";
config.textPrimitives.tiddlerForcedLinkRegExp = new RegExp("(?:" + config.textPrimitives.titledBrackettedLink + ")|(?:" +
	config.textPrimitives.brackettedLink + ")|(?:" + 
	config.textPrimitives.urlPattern + ")","mg");
config.textPrimitives.tiddlerAnyLinkRegExp = new RegExp("("+ config.textPrimitives.wikiLink + ")|(?:" +
	config.textPrimitives.titledBrackettedLink + ")|(?:" +
	config.textPrimitives.brackettedLink + ")|(?:" +
	config.textPrimitives.urlPattern + ")","mg");

// ---------------------------------------------------------------------------------
// Shadow tiddlers
// ---------------------------------------------------------------------------------

config.shadowTiddlers = {
	ColorPalette: "Background: #fff\n" + 
				  "Foreground: #000\n" +
				  "PrimaryPale: #8cf\n" +
				  "PrimaryLight: #18f\n" +
				  "PrimaryMid: #04b\n" +
				  "PrimaryDark: #014\n" +
				  "SecondaryPale: #ffc\n" +
				  "SecondaryLight: #fe8\n" +
				  "SecondaryMid: #db4\n" +
				  "SecondaryDark: #841\n" +
				  "TertiaryPale: #eee\n" +
				  "TertiaryLight: #ccc\n" +
				  "TertiaryMid: #999\n" +
				  "TertiaryDark: #666\n" +
				  "Error: #f88\n",
	StyleSheet: "",
	StyleSheetColors: "/*{{{*/\nbody {\n	background: [[ColorPalette::Background]];\n	color: [[ColorPalette::Foreground]];\n}\n\na{\n	color: [[ColorPalette::PrimaryMid]];\n}\n\na:hover{\n	background: [[ColorPalette::PrimaryMid]];\n	color: [[ColorPalette::Background]];\n}\n\na img{\n	border: 0;\n}\n\nh1,h2,h3,h4,h5 {\n	color: [[ColorPalette::SecondaryDark]];\n	background: [[ColorPalette::PrimaryPale]];\n}\n\n.button {\n	color: [[ColorPalette::PrimaryDark]];\n	border: 1px solid [[ColorPalette::Background]];\n}\n\n.button:hover {\n	color: [[ColorPalette::PrimaryDark]];\n	background: [[ColorPalette::SecondaryLight]];\n	border-color: [[ColorPalette::SecondaryMid]];\n}\n\n.button:active {\n	color: [[ColorPalette::Background]];\n	background: [[ColorPalette::SecondaryMid]];\n	border: 1px solid [[ColorPalette::SecondaryDark]];\n}\n\n.header {\n	background: [[ColorPalette::PrimaryMid]];\n}\n\n.headerShadow {\n	color: [[ColorPalette::Foreground]];\n}\n\n.headerShadow a {\n	font-weight: normal;\n	color: [[ColorPalette::Foreground]];\n}\n\n.headerForeground {\n	color: [[ColorPalette::Background]];\n}\n\n.headerForeground a {\n	font-weight: normal;\n	color: [[ColorPalette::PrimaryPale]];\n}\n\n.tabSelected{\n	color: [[ColorPalette::PrimaryDark]];\n	background: [[ColorPalette::TertiaryPale]];\n	border-left: 1px solid [[ColorPalette::TertiaryLight]];\n	border-top: 1px solid [[ColorPalette::TertiaryLight]];\n	border-right: 1px solid [[ColorPalette::TertiaryLight]];\n}\n\n.tabUnselected {\n	color: [[ColorPalette::Background]];\n	background: [[ColorPalette::TertiaryMid]];\n}\n\n.tabContents {\n	color: [[ColorPalette::PrimaryDark]];\n	background: [[ColorPalette::TertiaryPale]];\n	border: 1px solid [[ColorPalette::TertiaryLight]];\n}\n\n.tabContents .button {\n	 border: 0;}\n\n#sidebar {\n}\n\n#sidebarOptions input {\n	border: 1px solid [[ColorPalette::PrimaryMid]];\n}\n\n#sidebarOptions .sliderPanel {\n	background: [[ColorPalette::PrimaryPale]];\n}\n\n#sidebarOptions .sliderPanel a {\n	border: none;\n	color: [[ColorPalette::PrimaryMid]];\n}\n\n#sidebarOptions .sliderPanel a:hover {\n	color: [[ColorPalette::Background]];\n	background: [[ColorPalette::PrimaryMid]];\n}\n\n#sidebarOptions .sliderPanel a:active {\n	color: [[ColorPalette::PrimaryMid]];\n	background: [[ColorPalette::Background]];\n}\n\n.wizard {\n	background: [[ColorPalette::SecondaryLight]];\n	border-top: 1px solid [[ColorPalette::SecondaryMid]];\n	border-left: 1px solid [[ColorPalette::SecondaryMid]];\n}\n\n.wizard h1 {\n	color: [[ColorPalette::SecondaryDark]];\n}\n\n.wizard h2 {\n	color: [[ColorPalette::Foreground]];\n}\n\n.wizardStep {\n	background: [[ColorPalette::Background]];\n	border-top: 1px solid [[ColorPalette::SecondaryMid]];\n	border-bottom: 1px solid [[ColorPalette::SecondaryMid]];\n	border-left: 1px solid [[ColorPalette::SecondaryMid]];\n}\n\n.wizard .button {\n	color: [[ColorPalette::Background]];\n	background: [[ColorPalette::PrimaryMid]];\n	border-top: 1px solid [[ColorPalette::PrimaryLight]];\n	border-right: 1px solid [[ColorPalette::PrimaryDark]];\n	border-bottom: 1px solid [[ColorPalette::PrimaryDark]];\n	border-left: 1px solid [[ColorPalette::PrimaryLight]];\n}\n\n.wizard .button:hover {\n	color: [[ColorPalette::PrimaryLight]];\n	background: [[ColorPalette::PrimaryDark]];\n	border-color: [[ColorPalette::PrimaryLight]];\n}\n\n.wizard .button:active {\n	color: [[ColorPalette::Background]];\n	background: [[ColorPalette::PrimaryMid]];\n	border-top: 1px solid [[ColorPalette::PrimaryLight]];\n	border-right: 1px solid [[ColorPalette::PrimaryDark]];\n	border-bottom: 1px solid [[ColorPalette::PrimaryDark]];\n	border-left: 1px solid [[ColorPalette::PrimaryLight]];\n}\n\n#messageArea {\n	border: 1px solid [[ColorPalette::SecondaryDark]];\n	background: [[ColorPalette::SecondaryMid]];\n	color: [[ColorPalette::PrimaryDark]];\n}\n\n#messageArea .button {\n	padding: 0.2em 0.2em 0.2em 0.2em;\n	color: [[ColorPalette::PrimaryDark]];\n	background: [[ColorPalette::Background]];\n}\n\n.popup {\n	background: [[ColorPalette::PrimaryLight]];\n	border: 1px solid [[ColorPalette::PrimaryMid]];\n}\n\n.popup hr {\n	color: [[ColorPalette::PrimaryDark]];\n	background: [[ColorPalette::PrimaryDark]];\n	border-bottom: 1px;\n}\n\n.listBreak div{\n	border-bottom: 1px solid [[ColorPalette::PrimaryDark]];\n}\n\n.popup li.disabled {\n	color: [[ColorPalette::PrimaryMid]];\n}\n\n.popup li a, .popup li a:visited {\n	color: [[ColorPalette::TertiaryPale]];\n	border: none;\n}\n\n.popup li a:hover {\n	background: [[ColorPalette::PrimaryDark]];\n	color: [[ColorPalette::Background]];\n	border: none;\n}\n\n.tiddler .defaultCommand {\n font-weight: bold;\n}\n\n.shadow .title {\n	color: [[ColorPalette::TertiaryDark]];\n}\n\n.title {\n	color: [[ColorPalette::SecondaryDark]];\n}\n\n.subtitle {\n	color: [[ColorPalette::TertiaryDark]];\n}\n\n.toolbar {\n	color: [[ColorPalette::PrimaryMid]];\n}\n\n.tagging, .tagged {\n	border: 1px solid [[ColorPalette::TertiaryPale]];\n	background-color: [[ColorPalette::TertiaryPale]];\n}\n\n.selected .tagging, .selected .tagged {\n	background-color: [[ColorPalette::TertiaryLight]];\n	border: 1px solid [[ColorPalette::TertiaryMid]];\n}\n\n.tagging .listTitle, .tagged .listTitle {\n	color: [[ColorPalette::PrimaryDark]];\n}\n\n.tagging .button, .tagged .button {\n		border: none;\n}\n\n.footer {\n	color: [[ColorPalette::TertiaryLight]];\n}\n\n.selected .footer {\n	color: [[ColorPalette::TertiaryMid]];\n}\n\n.sparkline {\n	background: [[ColorPalette::PrimaryPale]];\n	border: 0;\n}\n\n.sparktick {\n	background: [[ColorPalette::PrimaryDark]];\n}\n\n.error, .errorButton {\n	color: [[ColorPalette::Foreground]];\n	background: [[ColorPalette::Error]];\n}\n\n.warning {\n	color: [[ColorPalette::Foreground]];\n	background: [[ColorPalette::SecondaryPale]];\n}\n\n.cascade {\n	background: [[ColorPalette::TertiaryPale]];\n	color: [[ColorPalette::TertiaryMid]];\n	border: 1px solid [[ColorPalette::TertiaryMid]];\n}\n\n.imageLink, #displayArea .imageLink {\n	background: transparent;\n}\n\n.viewer .listTitle {list-style-type: none; margin-left: -2em;}\n\n.viewer .button {\n	border: 1px solid [[ColorPalette::SecondaryMid]];\n}\n\n.viewer blockquote {\n	border-left: 3px solid [[ColorPalette::TertiaryDark]];\n}\n\n.viewer table {\n	border: 2px solid [[ColorPalette::TertiaryDark]];\n}\n\n.viewer th, thead td {\n	background: [[ColorPalette::SecondaryMid]];\n	border: 1px solid [[ColorPalette::TertiaryDark]];\n	color: [[ColorPalette::Background]];\n}\n\n.viewer td, .viewer tr {\n	border: 1px solid [[ColorPalette::TertiaryDark]];\n}\n\n.viewer pre {\n	border: 1px solid [[ColorPalette::SecondaryLight]];\n	background: [[ColorPalette::SecondaryPale]];\n}\n\n.viewer code {\n	color: [[ColorPalette::SecondaryDark]];\n}\n\n.viewer hr {\n	border: 0;\n	border-top: dashed 1px [[ColorPalette::TertiaryDark]];\n	color: [[ColorPalette::TertiaryDark]];\n}\n\n.highlight, .marked {\n	background: [[ColorPalette::SecondaryLight]];\n}\n\n.editor input {\n	border: 1px solid [[ColorPalette::PrimaryMid]];\n}\n\n.editor textarea {\n	border: 1px solid [[ColorPalette::PrimaryMid]];\n	width: 100%;\n}\n\n.editorFooter {\n	color: [[ColorPalette::TertiaryMid]];\n}\n\n/*}}}*/",
	StyleSheetLayout: "/*{{{*/\n* html .tiddler {\n    height: 1%;\n}\n\nbody {\n	font-size: .75em;\n	font-family: arial,helvetica;\n	margin: 0;\n	padding: 0;\n}\n\nh1,h2,h3,h4,h5 {\n	font-weight: bold;\n	text-decoration: none;\n	padding-left: 0.4em;\n}\n\nh1 {font-size: 1.35em;}\nh2 {font-size: 1.25em;}\nh3 {font-size: 1.1em;}\nh4 {font-size: 1em;}\nh5 {font-size: .9em;}\n\nhr {\n	height: 1px;\n}\n\na{\n	text-decoration: none;\n}\n\ndt {font-weight: bold;}\n\nol { list-style-type: decimal }\nol ol { list-style-type: lower-alpha }\nol ol ol { list-style-type: lower-roman }\nol ol ol ol { list-style-type: decimal }\nol ol ol ol ol { list-style-type: lower-alpha }\nol ol ol ol ol ol { list-style-type: lower-roman }\nol ol ol ol ol ol ol { list-style-type: decimal }\n\n.txtOptionInput {\n	width: 11em;\n}\n\n#contentWrapper .chkOptionInput {\n	border: 0;\n}\n\n.externalLink {\n	text-decoration: underline;\n}\n\n.indent {margin-left:3em;}\n.outdent {margin-left:3em; text-indent:-3em;}\ncode.escaped {white-space:nowrap;}\n\n.tiddlyLinkExisting {\n	font-weight: bold;\n}\n\n.tiddlyLinkNonExisting {\n	font-style: italic;\n}\n\n/* the 'a' is required for IE, otherwise it renders the whole tiddler a bold */\na.tiddlyLinkNonExisting.shadow {\n	font-weight: bold;\n}\n\n#mainMenu .tiddlyLinkExisting, \n#mainMenu .tiddlyLinkNonExisting,\n#sidebarTabs .tiddlyLinkNonExisting{\n font-weight: normal;\n font-style: normal;\n}\n\n#sidebarTabs .tiddlyLinkExisting {\n font-weight: bold;\n font-style: normal;\n}\n\n.header {\n		position: relative;\n}\n\n.header a:hover {\n	background: transparent;\n}\n\n.headerShadow {\n	position: relative;\n	padding: 4.5em 0em 1em 1em;\n	left: -1px;\n	top: -1px;\n}\n\n.headerForeground {\n	position: absolute;\n	padding: 4.5em 0em 1em 1em;\n	left: 0px;\n	top: 0px;\n}\n\n.siteTitle {\n	font-size: 3em;\n}\n\n.siteSubtitle {\n	font-size: 1.2em;\n}\n\n#mainMenu {\n	position: absolute;\n	left: 0;\n	width: 10em;\n	text-align: right;\n	line-height: 1.6em;\n	padding: 1.5em 0.5em 0.5em 0.5em;\n	font-size: 1.1em;\n}\n\n#sidebar {\n	position: absolute;\n	right: 3px;\n	width: 16em;\n	font-size: .9em;\n}\n\n#sidebarOptions {\n	padding-top: 0.3em;\n}\n\n#sidebarOptions a {\n	margin: 0em 0.2em;\n	padding: 0.2em 0.3em;\n	display: block;\n}\n\n#sidebarOptions input {\n	margin: 0.4em 0.5em;\n}\n\n#sidebarOptions .sliderPanel {\n	margin-left: 1em;\n	padding: 0.5em;\n	font-size: .85em;\n}\n\n#sidebarOptions .sliderPanel a {\n	font-weight: bold;\n	display: inline;\n	padding: 0;\n}\n\n#sidebarOptions .sliderPanel input {\n	margin: 0 0 .3em 0;\n}\n\n#sidebarTabs .tabContents {\n	width: 15em;\n	overflow: hidden;\n}\n\n.wizard {\n	padding: 0.1em 0em 0em 2em;\n}\n\n.wizard h1 {\n	font-size: 2em;\n	font-weight: bold;\n	background: none;\n	padding: 0em 0em 0em 0em;\n	margin: 0.4em 0em 0.2em 0em;\n}\n\n.wizard h2 {\n	font-size: 1.2em;\n	font-weight: bold;\n	background: none;\n	padding: 0em 0em 0em 0em;\n	margin: 0.2em 0em 0.2em 0em;\n}\n\n.wizardStep {\n	padding: 1em 1em 1em 1em;\n}\n\n.wizard .button {\n	margin: 0.5em 0em 0em 0em;\n	font-size: 1.2em;\n}\n\n#messageArea {\nposition:absolute; top:0; right:0; margin: 0.5em; padding: 0.5em;\n}\n\n*[id='messageArea'] {\nposition:fixed !important; z-index:99;}\n\n.messageToolbar {\ndisplay: block;\ntext-align: right;\n}\n\n#messageArea a{\n	text-decoration: underline;\n}\n\n.popup {\n	font-size: .9em;\n	padding: 0.2em;\n	list-style: none;\n	margin: 0;\n}\n\n.popup hr {\n	display: block;\n	height: 1px;\n	width: auto;\n	padding: 0;\n	margin: 0.2em 0em;\n}\n\n.listBreak {\n	font-size: 1px;\n	line-height: 1px;\n}\n\n.listBreak div {\n	margin: 2px 0;\n}\n\n.popup li.disabled {\n	padding: 0.2em;\n}\n\n.popup li a{\n	display: block;\n	padding: 0.2em;\n}\n\n.tabset {\n	padding: 1em 0em 0em 0.5em;\n}\n\n.tab {\n	margin: 0em 0em 0em 0.25em;\n	padding: 2px;\n}\n\n.tabContents {\n	padding: 0.5em;\n}\n\n.tabContents ul, .tabContents ol {\n	margin: 0;\n	padding: 0;\n}\n\n.txtMainTab .tabContents li {\n	list-style: none;\n}\n\n.tabContents li.listLink {\n	 margin-left: .75em;\n}\n\n#displayArea {\n	margin: 1em 17em 0em 14em;\n}\n\n\n.toolbar {\n	text-align: right;\n	font-size: .9em;\n	visibility: hidden;\n}\n\n.selected .toolbar {\n	visibility: visible;\n}\n\n.tiddler {\n	padding: 1em 1em 0em 1em;\n}\n\n.missing .viewer,.missing .title {\n	font-style: italic;\n}\n\n.title {\n	font-size: 1.6em;\n	font-weight: bold;\n}\n\n.missing .subtitle {\n display: none;\n}\n\n.subtitle {\n	font-size: 1.1em;\n}\n\n.tiddler .button {\n	padding: 0.2em 0.4em;\n}\n\n.tagging {\nmargin: 0.5em 0.5em 0.5em 0;\nfloat: left;\ndisplay: none;\n}\n\n.isTag .tagging {\ndisplay: block;\n}\n\n.tagged {\nmargin: 0.5em;\nfloat: right;\n}\n\n.tagging, .tagged {\nfont-size: 0.9em;\npadding: 0.25em;\n}\n\n.tagging ul, .tagged ul {\nlist-style: none;margin: 0.25em;\npadding: 0;\n}\n\n.tagClear {\nclear: both;\n}\n\n.footer {\n	font-size: .9em;\n}\n\n.footer li {\ndisplay: inline;\n}\n\n* html .viewer pre {\n	width: 99%;\n	padding: 0 0 1em 0;\n}\n\n.viewer {\n	line-height: 1.4em;\n	padding-top: 0.5em;\n}\n\n.viewer .button {\n	margin: 0em 0.25em;\n	padding: 0em 0.25em;\n}\n\n.viewer blockquote {\n	line-height: 1.5em;\n	padding-left: 0.8em;\n	margin-left: 2.5em;\n}\n\n.viewer ul, .viewer ol{\n	margin-left: 0.5em;\n	padding-left: 1.5em;\n}\n\n.viewer table {\n	border-collapse: collapse;\n	margin: 0.8em 1.0em;\n}\n\n.viewer th, .viewer td, .viewer tr,.viewer caption{\n	padding: 3px;\n}\n\n.viewer table.listView {\n	font-size: 0.85em;\n	margin: 0.8em 1.0em;\n}\n\n.viewer table.listView th, .viewer table.listView td, .viewer table.listView tr {\n	padding: 0px 3px 0px 3px;\n}\n\n.viewer pre {\n	padding: 0.5em;\n	margin-left: 0.5em;\n	font-size: 1.2em;\n	line-height: 1.4em;\n	overflow: auto;\n}\n\n.viewer code {\n	font-size: 1.2em;\n	line-height: 1.4em;\n}\n\n.editor {\nfont-size: 1.1em;\n}\n\n.editor input, .editor textarea {\n	display: block;\n	width: 100%;\n	font: inherit;\n}\n\n.editorFooter {\n	padding: 0.25em 0em;\n	font-size: .9em;\n}\n\n.editorFooter .button {\npadding-top: 0px; padding-bottom: 0px;}\n\n.fieldsetFix {border: 0;\npadding: 0;\nmargin: 1px 0px 1px 0px;\n}\n\n.sparkline {\n	line-height: 1em;\n}\n\n.sparktick {\n	outline: 0;\n}\n\n.zoomer {\n	font-size: 1.1em;\n	position: absolute;\n	padding: 1em;\n}\n\n.cascade {\n	font-size: 1.1em;\n	position: absolute;\n	overflow: hidden;\n}\n/*}}}*/",
	StyleSheetPrint: "/*{{{*/\n@media print {\n#mainMenu, #sidebar, #messageArea, .toolbar {display: none ! important;}\n#displayArea {margin: 1em 1em 0em 1em;}\n/* Fixes a feature in Firefox 1.5.0.2 where print preview displays the noscript content */\nnoscript {display:none;}\n}\n/*}}}*/",
	PageTemplate: "<!--{{{-->\n<div class='header' macro='gradient vert [[ColorPalette::PrimaryLight]] [[ColorPalette::PrimaryMid]]'>\n<div class='headerShadow'>\n<span class='siteTitle' refresh='content' tiddler='SiteTitle'></span>&nbsp;\n<span class='siteSubtitle' refresh='content' tiddler='SiteSubtitle'></span>\n</div>\n<div class='headerForeground'>\n<span class='siteTitle' refresh='content' tiddler='SiteTitle'></span>&nbsp;\n<span class='siteSubtitle' refresh='content' tiddler='SiteSubtitle'></span>\n</div>\n</div>\n<div id='mainMenu' refresh='content' tiddler='MainMenu'></div>\n<div id='sidebar'>\n<div id='sidebarOptions' refresh='content' tiddler='SideBarOptions'></div>\n<div id='sidebarTabs' refresh='content' force='true' tiddler='SideBarTabs'></div>\n</div>\n<div id='displayArea'>\n<div id='messageArea'></div>\n<div id='tiddlerDisplay'></div>\n</div>\n<!--}}}-->",
	ViewTemplate: "<!--{{{-->\n<div class='toolbar' macro='toolbar closeTiddler closeOthers +editTiddler permalink references jump'></div>\n<div class='title' macro='view title'></div>\n<div class='subtitle'><span macro='view modifier link'></span>, <span macro='view modified date [[DD MMM YYYY]]'></span> (<span macro='message views.wikified.createdPrompt'></span> <span macro='view created date [[DD MMM YYYY]]'></span>)</div>\n<div class='tagging' macro='tagging'></div>\n<div class='tagged' macro='tags'></div>\n<div class='viewer' macro='view text wikified'></div>\n<div class='tagClear'></div>\n<!--}}}-->",
	EditTemplate: "<!--{{{-->\n<div class='toolbar' macro='toolbar +saveTiddler -cancelTiddler deleteTiddler'></div>\n<div class='title' macro='view title'></div>\n<div class='editor' macro='edit title'></div>\n<div class='editor' macro='edit text'></div>\n<div class='editor' macro='edit tags'></div><div class='editorFooter'><span macro='message views.editor.tagPrompt'></span><span macro='tagChooser'></span></div>\n<!--}}}-->",
	MarkupPreHead: "<!--{{{-->\n<link rel='alternate' type='application/rss+xml' title='RSS' href='index.xml'/>\n<!--}}}-->",
	MarkupPostHead: "",
	MarkupPreBody: "",
	MarkupPostBody: ""
	};

// ---------------------------------------------------------------------------------
// Translateable strings
// ---------------------------------------------------------------------------------

// Strings in "double quotes" should be translated; strings in 'single quotes' should be left alone

merge(config.options,{
	txtUserName: "YourName"});

merge(config.messages,{
	customConfigError: "Problems were encountered loading plugins. See PluginManager for details",
	pluginError: "Error: %0",
	pluginDisabled: "Not executed because disabled via 'systemConfigDisable' tag",
	pluginForced: "Executed because forced via 'systemConfigForce' tag",
	pluginVersionError: "Not executed because this plugin needs a newer version of TiddlyWiki",
	nothingSelected: "Nothing is selected. You must select one or more items first",
	savedSnapshotError: "It appears that this TiddlyWiki has been incorrectly saved. Please see http://www.tiddlywiki.com/#DownloadSoftware for details",
	subtitleUnknown: "(unknown)",
	undefinedTiddlerToolTip: "The tiddler '%0' doesn't yet exist",
	shadowedTiddlerToolTip: "The tiddler '%0' doesn't yet exist, but has a pre-defined shadow value",
	tiddlerLinkTooltip: "%0 - %1, %2",
	externalLinkTooltip: "External link to %0",
	noTags: "There are no tagged tiddlers",
	notFileUrlError: "You need to save this TiddlyWiki to a file before you can save changes",
	cantSaveError: "It's not possible to save changes. This could be because your browser doesn't support saving (instead, use FireFox if you can), or because the pathname to your TiddlyWiki file contains illegal characters",
	invalidFileError: "The original file '%0' does not appear to be a valid TiddlyWiki",
	backupSaved: "Backup saved",
	backupFailed: "Failed to save backup file",
	rssSaved: "RSS feed saved",
	rssFailed: "Failed to save RSS feed file",
	emptySaved: "Empty template saved",
	emptyFailed: "Failed to save empty template file",
	mainSaved: "Main TiddlyWiki file saved",
	mainFailed: "Failed to save main TiddlyWiki file. Your changes have not been saved",
	macroError: "Error in macro <<%0>>",
	macroErrorDetails: "Error while executing macro <<%0>>:\n%1",
	missingMacro: "No such macro",
	overwriteWarning: "A tiddler named '%0' already exists. Choose OK to overwrite it",
	unsavedChangesWarning: "WARNING! There are unsaved changes in TiddlyWiki\n\nChoose OK to save\nChoose CANCEL to discard",
	confirmExit: "--------------------------------\n\nThere are unsaved changes in TiddlyWiki. If you continue you will lose those changes\n\n--------------------------------",
	saveInstructions: "SaveChanges",
	unsupportedTWFormat: "Unsupported TiddlyWiki format '%0'",
	tiddlerSaveError: "Error when saving tiddler '%0'",
	tiddlerLoadError: "Error when loading tiddler '%0'",
	wrongSaveFormat: "Cannot save with storage format '%0'. Using standard format for save.",
	invalidFieldName: "Invalid field name %0",
	fieldCannotBeChanged: "Field '%0' cannot be changed"});

merge(config.messages.messageClose,{
	text: "close",
	tooltip: "close this message area"});

config.messages.dates.months = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November","December"];
config.messages.dates.days = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"];
config.messages.dates.shortMonths = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
config.messages.dates.shortDays = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];

merge(config.views.wikified.tag,{
	labelNoTags: "no tags",
	labelTags: "tags: ",
	openTag: "Open tag '%0'",
	tooltip: "Show tiddlers tagged with '%0'",
	openAllText: "Open all",
	openAllTooltip: "Open all of these tiddlers",
	popupNone: "No other tiddlers tagged with '%0'"});

merge(config.views.wikified,{
	defaultText: "The tiddler '%0' doesn't yet exist. Double-click to create it",
	defaultModifier: "(missing)",
	shadowModifier: "(built-in shadow tiddler)",
	createdPrompt: "created"});

merge(config.views.editor,{
	tagPrompt: "Type tags separated with spaces, [[use double square brackets]] if necessary, or add existing",
	defaultText: "Type the text for '%0'"});

merge(config.views.editor.tagChooser,{
	text: "tags",
	tooltip: "Choose existing tags to add to this tiddler",
	popupNone: "There are no tags defined",
	tagTooltip: "Add the tag '%0'"});

merge(config.macros.search,{
	label: "search",
	prompt: "Search this TiddlyWiki",
	accessKey: "F",
	successMsg: "%0 tiddlers found matching %1",
	failureMsg: "No tiddlers found matching %0"});

merge(config.macros.tagging,{
	label: "tagging: ",
	labelNotTag: "not tagging",
	tooltip: "List of tiddlers tagged with '%0'"});

merge(config.macros.timeline,{
	dateFormat: "DD MMM YYYY"});

merge(config.macros.allTags,{
	tooltip: "Show tiddlers tagged with '%0'",
	noTags: "There are no tagged tiddlers"});

config.macros.list.all.prompt = "All tiddlers in alphabetical order";
config.macros.list.missing.prompt = "Tiddlers that have links to them but are not defined";
config.macros.list.orphans.prompt = "Tiddlers that are not linked to from any other tiddlers";
config.macros.list.shadowed.prompt = "Tiddlers shadowed with default contents";

merge(config.macros.closeAll,{
	label: "close all",
	prompt: "Close all displayed tiddlers (except any that are being edited)"});

merge(config.macros.permaview,{
	label: "permaview",
	prompt: "Link to an URL that retrieves all the currently displayed tiddlers"});

merge(config.macros.saveChanges,{
	label: "save changes",
	prompt: "Save all tiddlers to create a new TiddlyWiki",
	accessKey: "S"});

merge(config.macros.newTiddler,{
	label: "new tiddler",
	prompt: "Create a new tiddler",
	title: "New Tiddler",
	accessKey: "N"});

merge(config.macros.newJournal,{
	label: "new journal",
	prompt: "Create a new tiddler from the current date and time",
	accessKey: "J"});

merge(config.macros.plugins,{
	skippedText: "(This plugin has not been executed because it was added since startup)",
	noPluginText: "There are no plugins installed",
	confirmDeleteText: "Are you sure you want to delete these tiddlers:\n\n%0",
	listViewTemplate : {
		columns: [
			{name: 'Selected', field: 'Selected', rowName: 'title', type: 'Selector'},
			{name: 'Title', field: 'title', tiddlerLink: 'title', title: "Title", type: 'TiddlerLink'},
			{name: 'Forced', field: 'forced', title: "Forced", tag: 'systemConfigForce', type: 'TagCheckbox'},
			{name: 'Disabled', field: 'disabled', title: "Disabled", tag: 'systemConfigDisable', type: 'TagCheckbox'},
			{name: 'Executed', field: 'executed', title: "Loaded", type: 'Boolean', trueText: "Yes", falseText: "No"},
			{name: 'Error', field: 'error', title: "Status", type: 'Boolean', trueText: "Error", falseText: "OK"},
			{name: 'Log', field: 'log', title: "Log", type: 'StringList'}
			],
		rowClasses: [
			{className: 'error', field: 'error'},
			{className: 'warning', field: 'warning'}
			],
		actions: [
			{caption: "More actions...", name: ''},
			{caption: "Remove systemConfig tag", name: 'remove'},
			{caption: "Delete these tiddlers forever", name: 'delete'}
			]}
	});

merge(config.macros.refreshDisplay,{
	label: "refresh",
	prompt: "Redraw the entire TiddlyWiki display"
	});

merge(config.macros.importTiddlers,{
	readOnlyWarning: "You cannot import tiddlers into a read-only TiddlyWiki. Try opening the TiddlyWiki file from a file:// URL",
	defaultPath: "http://www.tiddlywiki.com/index.html",
	fetchLabel: "fetch",
	fetchPrompt: "Fetch the tiddlywiki file",
	fetchError: "There were problems fetching the tiddlywiki file",
	confirmOverwriteText: "Are you sure you want to overwrite these tiddlers:\n\n%0",
	wizardTitle: "Import tiddlers from another TiddlyWiki file",
	step1: "Step 1: Locate the TiddlyWiki file",
	step1prompt: "Enter the URL or pathname here: ",
	step1promptFile: "...or browse for a file: ",
	step1promptFeeds: "...or select a pre-defined feed: ",
	step1feedPrompt: "Choose...",
	step2: "Step 2: Loading TiddlyWiki file",
	step2Text: "Please wait while the file is loaded from: %0",
	step3: "Step 3: Choose the tiddlers to import",
	step4: "%0 tiddler(s) imported",
	step5: "Done",
	listViewTemplate: {
		columns: [
			{name: 'Selected', field: 'Selected', rowName: 'title', type: 'Selector'},
			{name: 'Title', field: 'title', title: "Title", type: 'String'},
			{name: 'Snippet', field: 'text', title: "Snippet", type: 'String'},
			{name: 'Tags', field: 'tags', title: "Tags", type: 'Tags'}
			],
		rowClasses: [
			],
		actions: [
			{caption: "More actions...", name: ''},
			{caption: "Import these tiddlers", name: 'import'}
			]}
	});

merge(config.commands.closeTiddler,{
	text: "close",
	tooltip: "Close this tiddler"});

merge(config.commands.closeOthers,{
	text: "close others",
	tooltip: "Close all other tiddlers"});

merge(config.commands.editTiddler,{
	text: "edit",
	tooltip: "Edit this tiddler",
	readOnlyText: "view",
	readOnlyTooltip: "View the source of this tiddler"});

merge(config.commands.saveTiddler,{
	text: "done",
	tooltip: "Save changes to this tiddler"});

merge(config.commands.cancelTiddler,{
	text: "cancel",
	tooltip: "Undo changes to this tiddler",
	warning: "Are you sure you want to abandon your changes to '%0'?",
	readOnlyText: "done",
	readOnlyTooltip: "View this tiddler normally"});

merge(config.commands.deleteTiddler,{
	text: "delete",
	tooltip: "Delete this tiddler",
	warning: "Are you sure you want to delete '%0'?"});

merge(config.commands.permalink,{
	text: "permalink",
	tooltip: "Permalink for this tiddler"});

merge(config.commands.references,{
	text: "references",
	tooltip: "Show tiddlers that link to this one",
	popupNone: "No references"});

merge(config.commands.jump,{
	text: "jump",
	tooltip: "Jump to another open tiddler"});

merge(config.shadowTiddlers,{
	DefaultTiddlers: "GettingStarted",
	MainMenu: "GettingStarted",
	SiteTitle: "My TiddlyWiki",
	SiteSubtitle: "a reusable non-linear personal web notebook",
	SiteUrl: "http://www.tiddlywiki.com/",
	GettingStarted: "To get started with this blank TiddlyWiki, you'll need to modify the following tiddlers:\n* SiteTitle & SiteSubtitle: The title and subtitle of the site, as shown above (after saving, they will also appear in the browser title bar)\n* MainMenu: The menu (usually on the left)\n* DefaultTiddlers: Contains the names of the tiddlers that you want to appear when the TiddlyWiki is opened\nYou'll also need to enter your username for signing your edits: <<option txtUserName>>",
	SideBarOptions: "<<search>><<closeAll>><<permaview>><<newTiddler>><<newJournal 'DD MMM YYYY'>><<saveChanges>><<slider chkSliderOptionsPanel OptionsPanel 'options »' 'Change TiddlyWiki advanced options'>>",
	OptionsPanel: "These InterfaceOptions for customising TiddlyWiki are saved in your browser\n\nYour username for signing your edits. Write it as a WikiWord (eg JoeBloggs)\n\n<<option txtUserName>>\n<<option chkSaveBackups>> SaveBackups\n<<option chkAutoSave>> AutoSave\n<<option chkRegExpSearch>> RegExpSearch\n<<option chkCaseSensitiveSearch>> CaseSensitiveSearch\n<<option chkAnimate>> EnableAnimations\n\n----\nAdvancedOptions\nPluginManager\nImportTiddlers",
	AdvancedOptions: "<<option chkGenerateAnRssFeed>> GenerateAnRssFeed\n<<option chkOpenInNewWindow>> OpenLinksInNewWindow\n<<option chkSaveEmptyTemplate>> SaveEmptyTemplate\n<<option chkToggleLinks>> Clicking on links to tiddlers that are already open causes them to close\n^^(override with Control or other modifier key)^^\n<<option chkHttpReadOnly>> HideEditingFeatures when viewed over HTTP\n<<option chkForceMinorUpdate>> Treat edits as MinorChanges by preserving date and time\n^^(override with Shift key when clicking 'done' or by pressing Ctrl-Shift-Enter^^\n<<option chkConfirmDelete>> ConfirmBeforeDeleting\nMaximum number of lines in a tiddler edit box: <<option txtMaxEditRows>>\nFolder name for backup files: <<option txtBackupFolder>>\n<<option chkInsertTabs>> Use tab key to insert tab characters instead of jumping to next field",
	SideBarTabs: "<<tabs txtMainTab Timeline Timeline TabTimeline All 'All tiddlers' TabAll Tags 'All tags' TabTags More 'More lists' TabMore>>",
	TabTimeline: "<<timeline>>",
	TabAll: "<<list all>>",
	TabTags: "<<allTags>>",
	TabMore: "<<tabs txtMoreTab Missing 'Missing tiddlers' TabMoreMissing Orphans 'Orphaned tiddlers' TabMoreOrphans Shadowed 'Shadowed tiddlers' TabMoreShadowed>>",
	TabMoreMissing: "<<list missing>>",
	TabMoreOrphans: "<<list orphans>>",
	TabMoreShadowed: "<<list shadowed>>",
	PluginManager: "<<plugins>>",
	ImportTiddlers: "<<importTiddlers>>"});

// ---------------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------------

var params = null; // Command line parameters
var store = null; // TiddlyWiki storage
var story = null; // Main story
var formatter = null; // Default formatters for the wikifier
config.parsers = {}; // Hashmap of alternative parsers for the wikifier
var anim = new Animator(); // Animation engine
var readOnly = false; // Whether we're in readonly mode
var highlightHack = null; // Embarrassing hack department...
var hadConfirmExit = false; // Don't warn more than once
var safeMode = false; // Disable all plugins and cookies
var installedPlugins = []; // Information filled in when plugins are executed
var startingUp = false; // Whether we're in the process of starting up
var pluginInfo,tiddler; // Used to pass information to plugins in loadPlugins()

// Whether to use the JavaSaver applet
var useJavaSaver = config.browser.isSafari || config.browser.isOpera;

// Starting up
function main()
{
	var now, then = new Date();
	startingUp = true;
	window.onbeforeunload = function(e) {if(window.confirmExit) return confirmExit();};
	params = getParameters();
	if(params)
		params = params.parseParams("open",null,false);
	store = new TiddlyWiki();
	invokeParamifier(params,"oninit");
	story = new Story("tiddlerDisplay","tiddler");
	addEvent(document,"click",Popup.onDocumentClick);
	saveTest();
	loadOptionsCookie();
	for(var s=0; s<config.notifyTiddlers.length; s++)
		store.addNotification(config.notifyTiddlers[s].name,config.notifyTiddlers[s].notify);
	store.loadFromDiv("storeArea","store",true);
	invokeParamifier(params,"onload");
	var pluginProblem = loadPlugins();
	formatter = new Formatter(config.formatters);
	readOnly = (window.location.protocol == "file:") ? false : config.options.chkHttpReadOnly;
	invokeParamifier(params,"onconfig");
	store.notifyAll();
	restart();
	if(pluginProblem)
		{
		story.displayTiddler(null,"PluginManager");
		displayMessage(config.messages.customConfigError);
		}
	now = new Date();
	if(config.displayStartupTime)
		displayMessage("TiddlyWiki startup in " + (now-then)/1000 + " seconds");
	startingUp = false;
}

// Restarting
function restart()
{
	invokeParamifier(params,"onstart");
	if(story.isEmpty())
		{
		var defaultParams = store.getTiddlerText("DefaultTiddlers").parseParams("open",null,false);
		invokeParamifier(defaultParams,"onstart");
		}
	window.scrollTo(0,0);
}

function saveTest()
{
	var saveTest = document.getElementById("saveTest");
	if(saveTest.hasChildNodes())
		alert(config.messages.savedSnapshotError);
	saveTest.appendChild(document.createTextNode("savetest"));
}

function loadPlugins()
{
	if(safeMode)
		return false;
	var configTiddlers = store.getTaggedTiddlers("systemConfig");
	installedPlugins = [];
	var hadProblem = false;
	for(var t=0; t<configTiddlers.length; t++)
		{
		tiddler = configTiddlers[t];
		pluginInfo = getPluginInfo(tiddler);
		if(isPluginExecutable(pluginInfo))
			{
			pluginInfo.executed = true;
			pluginInfo.error = false;
			try
				{
				if(tiddler.text && tiddler.text != "")
					window.eval(tiddler.text);
				}
			catch(e)
				{
				pluginInfo.log.push(config.messages.pluginError.format([exceptionText(e)]));
				pluginInfo.error = true;
				hadProblem = true;
				}
			}
		else
			pluginInfo.warning = true;
		installedPlugins.push(pluginInfo);
		}
	return hadProblem;
}

function getPluginInfo(tiddler)
{
	var p = store.getTiddlerSlices(tiddler.title,["Name","Description","Version","CoreVersion","Date","Source","Author","License","Browsers"]);
	p.tiddler = tiddler;
	p.title = tiddler.title;
	p.log = [];
	return p;
}

// Check that a particular plugin is valid for execution
function isPluginExecutable(plugin)
{
	if(plugin.tiddler.isTagged("systemConfigDisable"))
		return verifyTail(plugin,false,config.messages.pluginDisabled);
	if(plugin.tiddler.isTagged("systemConfigForce"))
		return verifyTail(plugin,true,config.messages.pluginForced);
	if(plugin["CoreVersion"])
		{
		var coreVersion = plugin["CoreVersion"].split(".");
		var w = parseInt(coreVersion[0]) - version.major;
		if(w == 0 && coreVersion[1])
			w = parseInt(coreVersion[1]) - version.minor;
		if(w == 0 && coreVersion[2])
		 	w = parseInt(coreVersion[2]) - version.revision;
		if(w > 0)
			return verifyTail(plugin,false,config.messages.pluginVersionError);
		}
	return true;
}

function verifyTail(plugin,result,message)
{
	plugin.log.push(message);
	return result;
}

function invokeMacro(place,macro,params,wikifier,tiddler)
{
	try
		{
		var m = config.macros[macro];
		if(m && m.handler)
			m.handler(place,macro,params.readMacroParams(),wikifier,params,tiddler);
		else
			createTiddlyError(place,config.messages.macroError.format([macro]),config.messages.macroErrorDetails.format([macro,config.messages.missingMacro]));
		}
	catch(ex)
		{
		createTiddlyError(place,config.messages.macroError.format([macro]),config.messages.macroErrorDetails.format([macro,ex.toString()]));
		}
}

// ---------------------------------------------------------------------------------
// Paramifiers
// ---------------------------------------------------------------------------------

function getParameters()
{
	var p = null;
	if(window.location.hash)
		{
		p = decodeURI(window.location.hash.substr(1));
		if(config.browser.firefoxDate != null && config.browser.firefoxDate[1] < "20051111")
			p = convertUTF8ToUnicode(p);
		}
	return p;
}

function invokeParamifier(params,handler)
{
	if(!params || params.length == undefined || params.length <= 1)
		return;
	for(var t=1; t<params.length; t++)
		{
		var p = config.paramifiers[params[t].name];
		if(p && p[handler] instanceof Function)
			p[handler](params[t].value);
		}
}

config.paramifiers = {};

config.paramifiers.start = {
	oninit: function(v) {
		safeMode = v.toLowerCase() == "safe";
		}
};

config.paramifiers.open = {
	onstart: function(v) {
		story.displayTiddler("bottom",v,null,false,false);
		}
};

config.paramifiers.story = {
	onstart: function(v) {
		var list = store.getTiddlerText(v,"").parseParams("open",null,false);
		invokeParamifier(list,"onstart");
		}
};

config.paramifiers.search = {
	onstart: function(v) {
		story.search(v,false,false);
		}
};

config.paramifiers.searchRegExp = {
	onstart: function(v) {
		story.prototype.search(v,false,true);
		}
};

config.paramifiers.tag = {
	onstart: function(v) {
		var tagged = store.getTaggedTiddlers(v,"title");
		for(var t=0; t<tagged.length; t++)
			story.displayTiddler("bottom",tagged[t].title,null,false,false);
		}
};

config.paramifiers.newTiddler = {
	onstart: function(v) {
		if(!readOnly)
			{
			story.displayTiddler(null,v,DEFAULT_EDIT_TEMPLATE);
			story.focusTiddler(v,"text");
			}
		}
};

config.paramifiers.newJournal = {
	onstart: function(v) {
		if(!readOnly)
			{
			var now = new Date();
			var title = now.formatString(v.trim());
			story.displayTiddler(null,title,DEFAULT_EDIT_TEMPLATE);
			story.focusTiddler(title,"text");
			}
		}
};

// ---------------------------------------------------------------------------------
// Formatter helpers
// ---------------------------------------------------------------------------------

function Formatter(formatters)
{
	this.formatters = [];
	var pattern = [];
	for(var n=0; n<formatters.length; n++)
		{
		pattern.push("(" + formatters[n].match + ")");
		this.formatters.push(formatters[n]);
		}
	this.formatterRegExp = new RegExp(pattern.join("|"),"mg");
}

config.formatterHelpers = {

	createElementAndWikify: function(w)
	{
		w.subWikifyTerm(createTiddlyElement(w.output,this.element),this.termRegExp);
	},
	
	inlineCssHelper: function(w)
	{
		var styles = [];
		config.textPrimitives.cssLookaheadRegExp.lastIndex = w.nextMatch;
		var lookaheadMatch = config.textPrimitives.cssLookaheadRegExp.exec(w.source);
		while(lookaheadMatch && lookaheadMatch.index == w.nextMatch)
			{
			var s,v;
			if(lookaheadMatch[1])
				{
				s = lookaheadMatch[1].unDash();
				v = lookaheadMatch[2];
				}
			else
				{
				s = lookaheadMatch[3].unDash();
				v = lookaheadMatch[4];
				}
			if (s=="bgcolor")
				s = "backgroundColor";
			styles.push({style: s, value: v});
			w.nextMatch = lookaheadMatch.index + lookaheadMatch[0].length;
			config.textPrimitives.cssLookaheadRegExp.lastIndex = w.nextMatch;
			lookaheadMatch = config.textPrimitives.cssLookaheadRegExp.exec(w.source);
			}
		return styles;
	},

	applyCssHelper: function(e,styles)
	{
		for(var t=0; t< styles.length; t++)
			{
			try
				{
				e.style[styles[t].style] = styles[t].value;
				}
			catch (ex)
				{
				}
			}
	},

	enclosedTextHelper: function(w)
	{
		this.lookaheadRegExp.lastIndex = w.matchStart;
		var lookaheadMatch = this.lookaheadRegExp.exec(w.source);
		if(lookaheadMatch && lookaheadMatch.index == w.matchStart)
			{
			var text = lookaheadMatch[1];
			if(config.browser.isIE)
				text = text.replace(/\n/g,"\r");
			createTiddlyElement(w.output,this.element,null,null,text);
			w.nextMatch = lookaheadMatch.index + lookaheadMatch[0].length;
			}
	},

	isExternalLink: function(link)
	{
		if(store.tiddlerExists(link) || store.isShadowTiddler(link))
			{
			//# Definitely not an external link
			return false;
			}
		var urlRegExp = new RegExp(config.textPrimitives.urlPattern,"mg");
		if(urlRegExp.exec(link))
			{
			// Definitely an external link
			return true;
			}
		if (link.indexOf(".")!=-1 || link.indexOf("\\")!=-1 || link.indexOf("/")!=-1)
			{
			//# Link contains . / or \ so is probably an external link
			return true;
			}
		//# Otherwise assume it is not an external link
		return false;
	}

};

// ---------------------------------------------------------------------------------
// Standard formatters
// ---------------------------------------------------------------------------------

config.formatters = [
{
	name: "table",
	match: "^\\|(?:[^\\n]*)\\|(?:[fhck]?)$",
	lookaheadRegExp: /^\|([^\n]*)\|([fhck]?)$/mg,
	rowTermRegExp: /(\|(?:[fhck]?)$\n?)/mg,
	cellRegExp: /(?:\|([^\n\|]*)\|)|(\|[fhck]?$\n?)/mg,
	cellTermRegExp: /((?:\x20*)\|)/mg,
	rowTypes: {"c":"caption", "h":"thead", "":"tbody", "f":"tfoot"},

	handler: function(w)
	{
		var table = createTiddlyElement(w.output,"table");
		var prevColumns = [];
		var currRowType = null;
		var rowContainer;
		var rowCount = 0;
		w.nextMatch = w.matchStart;
		this.lookaheadRegExp.lastIndex = w.nextMatch;
		var lookaheadMatch = this.lookaheadRegExp.exec(w.source);
		while(lookaheadMatch && lookaheadMatch.index == w.nextMatch)
			{
			var nextRowType = lookaheadMatch[2];
			if(nextRowType == "k")
				{
				table.className = lookaheadMatch[1];
				w.nextMatch += lookaheadMatch[0].length+1;
				}
			else
				{
				if(nextRowType != currRowType)
					{
					rowContainer = createTiddlyElement(table,this.rowTypes[nextRowType]);
					currRowType = nextRowType;
					}
				if(currRowType == "c")
					{
					// Caption
					w.nextMatch++;
					if(rowContainer != table.firstChild)
						table.insertBefore(rowContainer,table.firstChild);
					rowContainer.setAttribute("align",rowCount == 0?"top":"bottom");
					w.subWikifyTerm(rowContainer,this.rowTermRegExp);
					}
				else
					{
					this.rowHandler(w,createTiddlyElement(rowContainer,"tr",null,(rowCount&1)?"oddRow":"evenRow"),prevColumns);
					rowCount++;
					}
				}
			this.lookaheadRegExp.lastIndex = w.nextMatch;
			lookaheadMatch = this.lookaheadRegExp.exec(w.source);
			}
	},
	rowHandler: function(w,e,prevColumns)
	{
		var col = 0;
		var colSpanCount = 1;
		var prevCell = null;
		this.cellRegExp.lastIndex = w.nextMatch;
		var cellMatch = this.cellRegExp.exec(w.source);
		while(cellMatch && cellMatch.index == w.nextMatch)
			{
			if(cellMatch[1] == "~")
				{
				// Rowspan
				var last = prevColumns[col];
				if(last)
					{
					last.rowSpanCount++;
					last.element.setAttribute("rowspan",last.rowSpanCount);
					last.element.setAttribute("rowSpan",last.rowSpanCount); // Needed for IE
					last.element.valign = "center";
					}
				w.nextMatch = this.cellRegExp.lastIndex-1;
				}
			else if(cellMatch[1] == ">")
				{
				// Colspan
				colSpanCount++;
				w.nextMatch = this.cellRegExp.lastIndex-1;
				}
			else if(cellMatch[2])
				{
				// End of row
				if(prevCell && colSpanCount > 1)
					{
					prevCell.setAttribute("colspan",colSpanCount);
					prevCell.setAttribute("colSpan",colSpanCount); // Needed for IE
					}
				w.nextMatch = this.cellRegExp.lastIndex;
				break;
				}
			else
				{
				// Cell
				w.nextMatch++;
				var styles = config.formatterHelpers.inlineCssHelper(w);
				var spaceLeft = false;
				var chr = w.source.substr(w.nextMatch,1);
				while(chr == " ")
					{
					spaceLeft = true;
					w.nextMatch++;
					chr = w.source.substr(w.nextMatch,1);
					}
				var cell;
				if(chr == "!")
					{
					cell = createTiddlyElement(e,"th");
					w.nextMatch++;
					}
				else
					cell = createTiddlyElement(e,"td");
				prevCell = cell;
				prevColumns[col] = {rowSpanCount:1, element:cell};
				if(colSpanCount > 1)
					{
					cell.setAttribute("colspan",colSpanCount);
					cell.setAttribute("colSpan",colSpanCount); // Needed for IE
					colSpanCount = 1;
					}
				config.formatterHelpers.applyCssHelper(cell,styles);
				w.subWikifyTerm(cell,this.cellTermRegExp);
				if(w.matchText.substr(w.matchText.length-2,1) == " ") // spaceRight
					cell.align = spaceLeft ? "center" : "left";
				else if(spaceLeft)
					cell.align = "right";
				w.nextMatch--;
				}
			col++;
			this.cellRegExp.lastIndex = w.nextMatch;
			cellMatch = this.cellRegExp.exec(w.source);
			}
	}
},

{
	name: "heading",
	match: "^!{1,5}",
	termRegExp: /(\n)/mg,
	handler: function(w)
	{
		w.subWikifyTerm(createTiddlyElement(w.output,"h" + w.matchLength),this.termRegExp);
	}
},

{
	name: "list",
	match: "^(?:(?:(?:\\*)|(?:#)|(?:;)|(?::))+)",
	lookaheadRegExp: /^(?:(?:(\*)|(#)|(;)|(:))+)/mg,
	termRegExp: /(\n)/mg,
	handler: function(w)
	{
		var placeStack = [w.output];
		var currLevel = 0, currType = null;
		var listLevel, listType, itemType;
		w.nextMatch = w.matchStart;
		this.lookaheadRegExp.lastIndex = w.nextMatch;
		var lookaheadMatch = this.lookaheadRegExp.exec(w.source);
		while(lookaheadMatch && lookaheadMatch.index == w.nextMatch)
			{
			if(lookaheadMatch[1])
				{
				listType = "ul";
				itemType = "li";
				}
			else if(lookaheadMatch[2])
				{
				listType = "ol";
				itemType = "li";
				}
			else if(lookaheadMatch[3])
				{
				listType = "dl";
				itemType = "dt";
				}
			else if(lookaheadMatch[4])
				{
				listType = "dl";
				itemType = "dd";
				}
			listLevel = lookaheadMatch[0].length;
			w.nextMatch += lookaheadMatch[0].length;
			if(listLevel > currLevel)
				{
				for(var t=currLevel; t<listLevel; t++)
					placeStack.push(createTiddlyElement(placeStack[placeStack.length-1],listType));
				}
			else if(listLevel < currLevel)
				{
				for(var t=currLevel; t>listLevel; t--)
					placeStack.pop();
				}
			else if(listLevel == currLevel && listType != currType)
				{
				placeStack.pop();
				placeStack.push(createTiddlyElement(placeStack[placeStack.length-1],listType));
				}
			currLevel = listLevel;
			currType = listType;
			var e = createTiddlyElement(placeStack[placeStack.length-1],itemType);
			w.subWikifyTerm(e,this.termRegExp);
			this.lookaheadRegExp.lastIndex = w.nextMatch;
			lookaheadMatch = this.lookaheadRegExp.exec(w.source);
		}
	}
},

{
	name: "quoteByBlock",
	match: "^<<<\\n",
	termRegExp: /(^<<<(\n|$))/mg,
	element: "blockquote",
	handler: config.formatterHelpers.createElementAndWikify
},

{
	name: "quoteByLine",
	match: "^>+",
	lookaheadRegExp: /^>+/mg,
	termRegExp: /(\n)/mg,
	element: "blockquote",
	handler: function(w)
	{
		var placeStack = [w.output];
		var currLevel = 0;
		var newLevel = w.matchLength;
		var t;
		do {
			if(newLevel > currLevel)
				{
				for(t=currLevel; t<newLevel; t++)
					placeStack.push(createTiddlyElement(placeStack[placeStack.length-1],this.element));
				}
			else if(newLevel < currLevel)
				{
				for(t=currLevel; t>newLevel; t--)
					placeStack.pop();
				}
			currLevel = newLevel;
			w.subWikifyTerm(placeStack[placeStack.length-1],this.termRegExp);
			createTiddlyElement(placeStack[placeStack.length-1],"br");
			this.lookaheadRegExp.lastIndex = w.nextMatch;
			var lookaheadMatch = this.lookaheadRegExp.exec(w.source);
			var matched = lookaheadMatch && lookaheadMatch.index == w.nextMatch;
			if(matched)
				{
				newLevel = lookaheadMatch[0].length;
				w.nextMatch += lookaheadMatch[0].length;
				}
		} while(matched);
	}
},

{
	name: "rule",
	match: "^----+$\\n?",
	handler: function(w)
	{
		createTiddlyElement(w.output,"hr");
	}
},

{
	name: "monospacedByLine",
	match: "^\\{\\{\\{\\n",
	lookaheadRegExp: /^\{\{\{\n((?:^[^\n]*\n)+?)(^\}\}\}$\n?)/mg,
	element: "pre",
	handler: config.formatterHelpers.enclosedTextHelper
},

{
	name: "monospacedByLineForCSS",
	match: "^/\\*[\\{]{3}\\*/\\n",
	lookaheadRegExp: /\/\*[\{]{3}\*\/\n*((?:^[^\n]*\n)+?)(\n*^\/\*[\}]{3}\*\/$\n?)/mg,
	element: "pre",
	handler: config.formatterHelpers.enclosedTextHelper
},

{
	name: "monospacedByLineForPlugin",
	match: "^//\\{\\{\\{\\n",
	lookaheadRegExp: /^\/\/\{\{\{\n\n*((?:^[^\n]*\n)+?)(\n*^\/\/\}\}\}$\n?)/mg,
	element: "pre",
	handler: config.formatterHelpers.enclosedTextHelper
},

{
	name: "monospacedByLineForTemplate",
	match: "^<!--[\\{]{3}-->\\n",
	lookaheadRegExp: /<!--[\{]{3}-->\n*((?:^[^\n]*\n)+?)(\n*^<!--[\}]{3}-->$\n?)/mg, 
	element: "pre",
	handler: config.formatterHelpers.enclosedTextHelper
},

{
	name: "wikifyCommentForPlugin", 
	match: "^/\\*\\*\\*\\n",
	termRegExp: /(^\*\*\*\/\n)/mg,
	handler: function(w)
	{
		w.subWikifyTerm(w.output,this.termRegExp);
	}
},

{
	name: "wikifyCommentForTemplate", 
	match: "^<!---\\n",
	termRegExp: /(^--->\n)/mg,
	handler: function(w) 
	{
		w.subWikifyTerm(w.output,this.termRegExp);
	}
},

{
	name: "macro",
	match: "<<",
	lookaheadRegExp: /<<([^>\s]+)(?:\s*)((?:[^>]|(?:>(?!>)))*)>>/mg,
	handler: function(w)
	{
		this.lookaheadRegExp.lastIndex = w.matchStart;
		var lookaheadMatch = this.lookaheadRegExp.exec(w.source);
		if(lookaheadMatch && lookaheadMatch.index == w.matchStart && lookaheadMatch[1])
			{
			w.nextMatch = this.lookaheadRegExp.lastIndex;
			invokeMacro(w.output,lookaheadMatch[1],lookaheadMatch[2],w,w.tiddler);
			}
	}
},

{
	name: "prettyLink",
	match: "\\[\\[",
	lookaheadRegExp: /\[\[(.*?)(?:\|(~)?(.*?))?\]\]/mg,
	handler: function(w)
	{
		this.lookaheadRegExp.lastIndex = w.matchStart;
		var lookaheadMatch = this.lookaheadRegExp.exec(w.source);
		if(lookaheadMatch && lookaheadMatch.index == w.matchStart)
			{
			var e;
			var text = lookaheadMatch[1];
			if(lookaheadMatch[3])
				{
				// Pretty bracketted link
				var link = lookaheadMatch[3];
				e = (!lookaheadMatch[2] && config.formatterHelpers.isExternalLink(link))
						? createExternalLink(w.output,link)
						: createTiddlyLink(w.output,link,false,null,w.isStatic);
				}
			else
				{
				// Simple bracketted link
				e = createTiddlyLink(w.output,text,false,null,w.isStatic);
				}
			createTiddlyText(e,text);
			w.nextMatch = this.lookaheadRegExp.lastIndex;
			}
	}
},

{
	name: "unWikiLink",
	match: config.textPrimitives.unWikiLink+config.textPrimitives.wikiLink,
	handler: function(w)
	{
		w.outputText(w.output,w.matchStart+1,w.nextMatch);
	}
},

{
	name: "wikiLink",
	match: config.textPrimitives.wikiLink,
	handler: function(w)
	{
		if(w.matchStart > 0)
			{
			var preRegExp = new RegExp(config.textPrimitives.anyLetterStrict,"mg");
			preRegExp.lastIndex = w.matchStart-1;
			var preMatch = preRegExp.exec(w.source);
			if(preMatch.index == w.matchStart-1)
				{
				w.outputText(w.output,w.matchStart,w.nextMatch);
				return;
				}
			}
		if(w.autoLinkWikiWords == true || store.isShadowTiddler(w.matchText))
			{
			var link = createTiddlyLink(w.output,w.matchText,false,null,w.isStatic);
			w.outputText(link,w.matchStart,w.nextMatch);
			}
		else
			{
			w.outputText(w.output,w.matchStart,w.nextMatch);
			}
	}
},

{
	name: "urlLink",
	match: config.textPrimitives.urlPattern,
	handler: function(w)
	{
		w.outputText(createExternalLink(w.output,w.matchText),w.matchStart,w.nextMatch);
	}
},

{
	name: "image",
	match: "\\[[<>]?[Ii][Mm][Gg]\\[",
	lookaheadRegExp: /\[(<?)(>?)[Ii][Mm][Gg]\[(?:([^\|\]]+)\|)?([^\[\]\|]+)\](?:\[([^\]]*)\])?\]/mg,
	handler: function(w)
	{
		this.lookaheadRegExp.lastIndex = w.matchStart;
		var lookaheadMatch = this.lookaheadRegExp.exec(w.source);
		if(lookaheadMatch && lookaheadMatch.index == w.matchStart) // Simple bracketted link
			{
			var e = w.output;
			if(lookaheadMatch[5])
				{
				var link = lookaheadMatch[5];
				e = config.formatterHelpers.isExternalLink(link) ? createExternalLink(w.output,link) : createTiddlyLink(w.output,link,false,null,w.isStatic);
				addClass(e,"imageLink");
				}
			var img = createTiddlyElement(e,"img");
			if(lookaheadMatch[1])
				img.align = "left";
			else if(lookaheadMatch[2])
				img.align = "right";
			if(lookaheadMatch[3])
				img.title = lookaheadMatch[3];
			img.src = lookaheadMatch[4];
			w.nextMatch = this.lookaheadRegExp.lastIndex;
			}
	}
},

{
	name: "html",
	match: "<[Hh][Tt][Mm][Ll]>",
	lookaheadRegExp: /<[Hh][Tt][Mm][Ll]>((?:.|\n)*?)<\/[Hh][Tt][Mm][Ll]>/mg,
	handler: function(w)
	{
		this.lookaheadRegExp.lastIndex = w.matchStart;
		var lookaheadMatch = this.lookaheadRegExp.exec(w.source)
		if(lookaheadMatch && lookaheadMatch.index == w.matchStart)
			{
			createTiddlyElement(w.output,"span").innerHTML = lookaheadMatch[1];
			w.nextMatch = this.lookaheadRegExp.lastIndex;
			}
	}
},

{
	name: "commentByBlock",
	match: "/%",
	lookaheadRegExp: /\/%((?:.|\n)*?)%\//mg,
	handler: function(w)
	{
		this.lookaheadRegExp.lastIndex = w.matchStart;
		var lookaheadMatch = this.lookaheadRegExp.exec(w.source)
		if(lookaheadMatch && lookaheadMatch.index == w.matchStart)
			w.nextMatch = this.lookaheadRegExp.lastIndex;
	}
},

{
	name: "boldByChar",
	match: "''",
	termRegExp: /('')/mg,
	element: "strong",
	handler: config.formatterHelpers.createElementAndWikify
},

{
	name: "italicByChar",
	match: "//",
	termRegExp: /(\/\/)/mg,
	element: "em",
	handler: config.formatterHelpers.createElementAndWikify
},

{
	name: "underlineByChar",
	match: "__",
	termRegExp: /(__)/mg,
	element: "u",
	handler: config.formatterHelpers.createElementAndWikify
},

{
	name: "strikeByChar",
	match: "--(?!\\s|$)",
	termRegExp: /((?!\s)--|(?=\n\n))/mg,
	element: "strike",
	handler: config.formatterHelpers.createElementAndWikify
},

{
	name: "superscriptByChar",
	match: "\\^\\^",
	termRegExp: /(\^\^)/mg,
	element: "sup",
	handler: config.formatterHelpers.createElementAndWikify
},

{
	name: "subscriptByChar",
	match: "~~",
	termRegExp: /(~~)/mg,
	element: "sub",
	handler: config.formatterHelpers.createElementAndWikify
},

{
	name: "monospacedByChar",
	match: "\\{\\{\\{",
	lookaheadRegExp: /\{\{\{((?:.|\n)*?)\}\}\}/mg,
	handler: function(w)
	{
		this.lookaheadRegExp.lastIndex = w.matchStart;
		var lookaheadMatch = this.lookaheadRegExp.exec(w.source)
		if(lookaheadMatch && lookaheadMatch.index == w.matchStart)
			{
			createTiddlyElement(w.output,"code",null,null,lookaheadMatch[1]);
			w.nextMatch = this.lookaheadRegExp.lastIndex;
			}
	}
},

{
	name: "styleByChar",
	match: "@@",
	termRegExp: /(@@)/mg,
	handler:  function(w)
	{
		var e = createTiddlyElement(w.output,"span");
		var styles = config.formatterHelpers.inlineCssHelper(w);
		if(styles.length == 0)
			e.className = "marked";
		else
			config.formatterHelpers.applyCssHelper(e,styles);
		w.subWikifyTerm(e,this.termRegExp);
	}
},

{
	name: "lineBreak",
	match: "\\n|<br ?/?>",
	handler: function(w)
	{
		createTiddlyElement(w.output,"br");
	}
},

{
	name: "rawText",
	match: "\\\"{3}|<nowiki>",
	lookaheadRegExp: /(?:\"{3}|<nowiki>)((?:.|\n)*?)(?:\"{3}|<\/nowiki>)/mg,
	handler: function(w)
	{
		this.lookaheadRegExp.lastIndex = w.matchStart;
		var lookaheadMatch = this.lookaheadRegExp.exec(w.source)
		if(lookaheadMatch && lookaheadMatch.index == w.matchStart)
			{
			createTiddlyElement(w.output,"span",null,null,lookaheadMatch[1]);
			w.nextMatch = this.lookaheadRegExp.lastIndex;
			}
	}
},

{
	name: "mdash",
	match: "--",
	handler: function(w)
		{
		createTiddlyElement(w.output,"span").innerHTML = "&mdash;";
		}
},

{
	name: "htmlEntitiesEncoding",
	match: "(?:(?:&#?[a-zA-Z0-9]{2,8};|.)(?:&#?(?:x0*(?:3[0-6][0-9a-fA-F]|1D[c-fC-F][0-9a-fA-F]|20[d-fD-F][0-9a-fA-F]|FE2[0-9a-fA-F])|0*(?:76[89]|7[7-9][0-9]|8[0-7][0-9]|761[6-9]|76[2-7][0-9]|84[0-3][0-9]|844[0-7]|6505[6-9]|6506[0-9]|6507[0-1]));)+|&#?[a-zA-Z0-9]{2,8};)",
	handler: function(w)
		{
		createTiddlyElement(w.output,"span").innerHTML = w.matchText;
		}
},

{
	name: "customClasses",
	match: "\\{\\{",
	termRegExp: /(\}\}\})/mg,
	lookaheadRegExp: /\{\{[\s]*([\w]+[\s\w]*)[\s]*\{(\n?)/mg,
	handler: function(w)
	{
		this.lookaheadRegExp.lastIndex = w.matchStart;
		var lookaheadMatch = this.lookaheadRegExp.exec(w.source);
		if(lookaheadMatch)
			{
			var e = createTiddlyElement(w.output,lookaheadMatch[2] == "\n" ? "div" : "span",null,lookaheadMatch[1]);
			w.nextMatch = this.lookaheadRegExp.lastIndex;
			w.subWikifyTerm(e,this.termRegExp);
			}
	}
}

];

// ---------------------------------------------------------------------------------
// Wikifier
// ---------------------------------------------------------------------------------

function getParser(tiddler)
{
	var f = formatter;
	if(tiddler!=null)
		{
		for(var i in config.parsers)
			{
			if(tiddler.isTagged(config.parsers[i].formatTag))
				{
				f = config.parsers[i];
				break;
				}
			}
		}
	return f;
}

function wikify(source,output,highlightRegExp,tiddler)
{
	if(source && source != "")
		{
		var wikifier = new Wikifier(source,getParser(tiddler),highlightRegExp,tiddler);
		wikifier.subWikifyUnterm(output);
		}
}

function wikifyStatic(source,highlightRegExp,tiddler)
{
	var e = createTiddlyElement(document.body,"div");
	e.style.display = "none";
	var html = "";
	if(source && source != "")
		{
		var wikifier = new Wikifier(source,getParser(tiddler),highlightRegExp,tiddler);
		wikifier.isStatic = true;
		wikifier.subWikifyUnterm(e);
		html = e.innerHTML;
		e.parentNode.removeChild(e);
		}
	return html;
}

// Wikify a named tiddler to plain text
function wikifyPlain(title)
{
	if(store.tiddlerExists(title) || store.isShadowTiddler(title))
		{
		var wikifier = new Wikifier(store.getTiddlerText(title),formatter,null,store.getTiddler(title));
		return wikifier.wikifyPlain();
		}
	else
		return "";
}

// Highlight plain text into an element
function highlightify(source,output,highlightRegExp)
{
	if(source && source != "")
		{
		var wikifier = new Wikifier(source,formatter,highlightRegExp);
		wikifier.outputText(output,0,source.length);
		}
}

// Construct a wikifier object
// source - source string that's going to be wikified
// formatter - Formatter() object containing the list of formatters to be used
// highlightRegExp - regular expression of the text string to highlight
// tiddler - reference to the tiddler that's taken to be the container for this wikification
function Wikifier(source,formatter,highlightRegExp,tiddler)
{
	this.source = source;
	this.output = null;
	this.formatter = formatter;
	this.nextMatch = 0;
	this.autoLinkWikiWords = tiddler && tiddler.autoLinkWikiWords() == false ? false : true;
	this.highlightRegExp = highlightRegExp;
	this.highlightMatch = null;
	this.isStatic = false;
	if(highlightRegExp)
		{
		highlightRegExp.lastIndex = 0;
		this.highlightMatch = highlightRegExp.exec(source);
		}
	this.tiddler = tiddler;
}

Wikifier.prototype.wikifyPlain = function()
{
	var e = createTiddlyElement(document.body,"div");
	e.style.display = "none";
	this.subWikify(e);
	var text = getPlainText(e);
	e.parentNode.removeChild(e);
	return text;
}

Wikifier.prototype.subWikify = function(output,terminator)
{
	// Handle the terminated and unterminated cases separately
	if (terminator)
		this.subWikifyTerm(output,new RegExp("(" + terminator + ")","mg"));
	else
		this.subWikifyUnterm(output);
}

Wikifier.prototype.subWikifyUnterm = function(output)
{
	// subWikify() can be indirectly recursive, so we need to save the old output pointer
	var oldOutput = this.output;
	this.output = output;
	// Get the first match
	this.formatter.formatterRegExp.lastIndex = this.nextMatch;
	var formatterMatch = this.formatter.formatterRegExp.exec(this.source);
	while(formatterMatch)
		{
		// Output any text before the match
		if(formatterMatch.index > this.nextMatch)
			this.outputText(this.output,this.nextMatch,formatterMatch.index);
		// Set the match parameters for the handler
		this.matchStart = formatterMatch.index;
		this.matchLength = formatterMatch[0].length;
		this.matchText = formatterMatch[0];
		this.nextMatch = this.formatter.formatterRegExp.lastIndex;
		// Figure out which formatter matched and call its handler
		for(var t=1; t<formatterMatch.length; t++)
			{
			if(formatterMatch[t])
				{
				this.formatter.formatters[t-1].handler(this);
				this.formatter.formatterRegExp.lastIndex = this.nextMatch;
				break;
				}
			}
		// Get the next match
		formatterMatch = this.formatter.formatterRegExp.exec(this.source);
		}
	// Output any text after the last match
	if(this.nextMatch < this.source.length)
		{
		this.outputText(this.output,this.nextMatch,this.source.length);
		this.nextMatch = this.source.length;
		}
	// Restore the output pointer
	this.output = oldOutput;
}

Wikifier.prototype.subWikifyTerm = function(output,terminatorRegExp)
{
	// subWikify() can be indirectly recursive, so we need to save the old output pointer
	var oldOutput = this.output;
	this.output = output;
	// Get the first matches for the formatter and terminator RegExps
	terminatorRegExp.lastIndex = this.nextMatch;
	var terminatorMatch = terminatorRegExp.exec(this.source);
	this.formatter.formatterRegExp.lastIndex = this.nextMatch;
	var formatterMatch = this.formatter.formatterRegExp.exec(terminatorMatch ? this.source.substr(0,terminatorMatch.index) : this.source);
	while(terminatorMatch || formatterMatch)
		{
		// Check for a terminator match  before the next formatter match
		if(terminatorMatch && (!formatterMatch || terminatorMatch.index <= formatterMatch.index))
			{
			// Output any text before the match
			if(terminatorMatch.index > this.nextMatch)
				this.outputText(this.output,this.nextMatch,terminatorMatch.index);
			// Set the match parameters
			this.matchText = terminatorMatch[1];
			this.matchLength = terminatorMatch[1].length;
			this.matchStart = terminatorMatch.index;
			this.nextMatch = this.matchStart + this.matchLength;
			// Restore the output pointer
			this.output = oldOutput;
			return;
			}
		// It must be a formatter match; output any text before the match
		if(formatterMatch.index > this.nextMatch)
			this.outputText(this.output,this.nextMatch,formatterMatch.index);
		// Set the match parameters
		this.matchStart = formatterMatch.index;
		this.matchLength = formatterMatch[0].length;
		this.matchText = formatterMatch[0];
		this.nextMatch = this.formatter.formatterRegExp.lastIndex;
		// Figure out which formatter matched and call its handler
		for(var t=1; t<formatterMatch.length; t++)
			{
			if(formatterMatch[t])
				{
				this.formatter.formatters[t-1].handler(this);
				this.formatter.formatterRegExp.lastIndex = this.nextMatch;
				break;
				}
			}
		// Get the next match
		terminatorRegExp.lastIndex = this.nextMatch;
		terminatorMatch = terminatorRegExp.exec(this.source);
		formatterMatch = this.formatter.formatterRegExp.exec(terminatorMatch ? this.source.substr(0,terminatorMatch.index) : this.source);
		}
	// Output any text after the last match
	if(this.nextMatch < this.source.length)
		{
		this.outputText(this.output,this.nextMatch,this.source.length);
		this.nextMatch = this.source.length;
		}
	// Restore the output pointer
	this.output = oldOutput;
}

Wikifier.prototype.outputText = function(place,startPos,endPos)
{
	// Check for highlights
	while(this.highlightMatch && (this.highlightRegExp.lastIndex > startPos) && (this.highlightMatch.index < endPos) && (startPos < endPos))
		{
		// Deal with any plain text before the highlight
		if(this.highlightMatch.index > startPos)
			{
			createTiddlyText(place,this.source.substring(startPos,this.highlightMatch.index));
			startPos = this.highlightMatch.index;
			}
		// Deal with the highlight
		var highlightEnd = Math.min(this.highlightRegExp.lastIndex,endPos);
		var theHighlight = createTiddlyElement(place,"span",null,"highlight",this.source.substring(startPos,highlightEnd));
		startPos = highlightEnd;
		// Nudge along to the next highlight if we're done with this one
		if(startPos >= this.highlightRegExp.lastIndex)
			this.highlightMatch = this.highlightRegExp.exec(this.source);
		}
	// Do the unhighlighted text left over
	if(startPos < endPos)
		{
		createTiddlyText(place,this.source.substring(startPos,endPos));
		}
}

// ---------------------------------------------------------------------------------
// Macro definitions
// ---------------------------------------------------------------------------------

config.macros.today.handler = function(place,macroName,params)
{
	var now = new Date();
	var text;
	if(params[0])
		text = now.formatString(params[0].trim());
	else
		text = now.toLocaleString();
	createTiddlyElement(place,"span",null,null,text);
}

config.macros.version.handler = function(place)
{
	createTiddlyElement(place,"span",null,null,version.major + "." + version.minor + "." + version.revision + (version.beta ? " (beta " + version.beta + ")" : ""));
}

config.macros.list.handler = function(place,macroName,params)
{
	var type = params[0] ? params[0] : "all";
	var theList = document.createElement("ul");
	place.appendChild(theList);
	if(this[type].prompt)
		createTiddlyElement(theList,"li",null,"listTitle",this[type].prompt);
	var results;
	if(this[type].handler)
		results = this[type].handler(params);
	for(var t = 0; t < results.length; t++)
		{
		var theListItem = document.createElement("li")
		theList.appendChild(theListItem);
		if(typeof results[t] == "string")
			createTiddlyLink(theListItem,results[t],true);
		else
			createTiddlyLink(theListItem,results[t].title,true);
		}
}

config.macros.list.all.handler = function(params)
{
	return store.reverseLookup("tags","excludeLists",false,"title");
}

config.macros.list.missing.handler = function(params)
{
	return store.getMissingLinks();
}

config.macros.list.orphans.handler = function(params)
{
	return store.getOrphans();
}

config.macros.list.shadowed.handler = function(params)
{
	return store.getShadowed();
}

config.macros.allTags.handler = function(place,macroName,params)
{
	var tags = store.getTags();
	var theDateList = createTiddlyElement(place,"ul");
	if(tags.length == 0)
		createTiddlyElement(theDateList,"li",null,"listTitle",this.noTags);
	for(var t=0; t<tags.length; t++)
		{
		var theListItem =createTiddlyElement(theDateList,"li");
		var theTag = createTiddlyButton(theListItem,tags[t][0] + " (" + tags[t][1] + ")",this.tooltip.format([tags[t][0]]),onClickTag);
		theTag.setAttribute("tag",tags[t][0]);
		}
}

config.macros.timeline.handler = function(place,macroName,params)
{
	var field = params[0] ? params[0] : "modified";
	var tiddlers = store.reverseLookup("tags","excludeLists",false,field);
	var lastDay = "";
	var last = params[1] ? tiddlers.length-Math.min(tiddlers.length,parseInt(params[1])) : 0;
	for(var t=tiddlers.length-1; t>=last; t--)
		{
		var tiddler = tiddlers[t];
		var theDay = tiddler[field].convertToLocalYYYYMMDDHHMM().substr(0,8);
		if(theDay != lastDay)
			{
			var theDateList = document.createElement("ul");
			place.appendChild(theDateList);
			createTiddlyElement(theDateList,"li",null,"listTitle",tiddler[field].formatString(this.dateFormat));
			lastDay = theDay;
			}
		var theDateListItem = createTiddlyElement(theDateList,"li",null,"listLink");
		theDateListItem.appendChild(createTiddlyLink(place,tiddler.title,true));
		}
}

config.macros.search.handler = function(place,macroName,params)
{
	var searchTimeout = null;
	var btn = createTiddlyButton(place,this.label,this.prompt,this.onClick);
	var txt = createTiddlyElement(place,"input",null,"txtOptionInput");
	if(params[0])
		txt.value = params[0];
	txt.onkeyup = this.onKeyPress;
	txt.onfocus = this.onFocus;
	txt.setAttribute("size",this.sizeTextbox);
	txt.setAttribute("accessKey",this.accessKey);
	txt.setAttribute("autocomplete","off");
	txt.setAttribute("lastSearchText","");
	if(config.browser.isSafari)
		{
		txt.setAttribute("type","search");
		txt.setAttribute("results","5");
		}
	else
		txt.setAttribute("type","text");
}

// Global because there's only ever one outstanding incremental search timer
config.macros.search.timeout = null;

config.macros.search.doSearch = function(txt)
{
	if(txt.value.length > 0)
		{
		story.search(txt.value,config.options.chkCaseSensitiveSearch,config.options.chkRegExpSearch);
		txt.setAttribute("lastSearchText",txt.value);
		}
}

config.macros.search.onClick = function(e)
{
	config.macros.search.doSearch(this.nextSibling);
	return false;
}

config.macros.search.onKeyPress = function(e)
{
	if(!e) var e = window.event;
	switch(e.keyCode)
		{
		case 13: // Ctrl-Enter
		case 10: // Ctrl-Enter on IE PC
			config.macros.search.doSearch(this);
			break;
		case 27: // Escape
			this.value = "";
			clearMessage();
			break;
		}
	if(this.value.length > 2)
		{
		if(this.value != this.getAttribute("lastSearchText"))
			{
			if(config.macros.search.timeout)
				clearTimeout(config.macros.search.timeout);
			var txt = this;
			config.macros.search.timeout = setTimeout(function() {config.macros.search.doSearch(txt);},500);
			}
		}
	else
		{
		if(config.macros.search.timeout)
			clearTimeout(config.macros.search.timeout);
		}
}

config.macros.search.onFocus = function(e)
{
	this.select();
}

config.macros.tiddler.handler = function(place,macroName,params,wikifier,paramString,tiddler)
{
	params = paramString.parseParams("name",null,true,false,true);
	var names = params[0]["name"];
	var tiddlerName = names[0];
	var className = names[1] ? names[1] : null;
	var args = params[0]["with"];
	var wrapper = createTiddlyElement(place,"span",null,className);
	if(!args)
		{
		wrapper.setAttribute("refresh","content");
		wrapper.setAttribute("tiddler",tiddlerName);
		}
	var text = store.getTiddlerText(tiddlerName);
	if(text)
		{
		var stack = config.macros.tiddler.tiddlerStack;
		if(stack.indexOf(tiddlerName) !== -1)
			return;
		stack.push(tiddlerName);
		try
			{
			var n = args ? Math.min(args.length,9) : 0;
			for(var i=0; i<n; i++) 
				{
				var placeholderRE = new RegExp("\\$" + (i + 1),"mg");
				text = text.replace(placeholderRE,args[i]);
				}
			config.macros.tiddler.renderText(wrapper,text,tiddlerName,params);
			}
		finally
			{
			stack.pop();
			}
		}
}

config.macros.tiddler.renderText = function(place,text,tiddlerName,params) 
{
	wikify(text,place,null,store.getTiddler(tiddlerName));
}

config.macros.tiddler.tiddlerStack = [];

config.macros.tag.handler = function(place,macroName,params)
{
	createTagButton(place,params[0]);
}

config.macros.tags.handler = function(place,macroName,params,wikifier,paramString,tiddler)
{
	params = paramString.parseParams("anon",null,true,false,false);
	var theList = createTiddlyElement(place,"ul");
	var title = getParam(params,"anon","");
	if(title && store.tiddlerExists(title))
		tiddler = store.getTiddler(title);
	var sep = getParam(params,"sep"," ");
	var lingo = config.views.wikified.tag;
	var prompt = tiddler.tags.length == 0 ? lingo.labelNoTags : lingo.labelTags;
	createTiddlyElement(theList,"li",null,"listTitle",prompt.format([tiddler.title]));
	for(var t=0; t<tiddler.tags.length; t++)
		{
		createTagButton(createTiddlyElement(theList,"li"),tiddler.tags[t],tiddler.title);
		if(t<tiddler.tags.length-1)
			createTiddlyText(theList,sep);
		}
}

config.macros.tagging.handler = function(place,macroName,params,wikifier,paramString,tiddler)
{
	params = paramString.parseParams("anon",null,true,false,false);
	var theList = createTiddlyElement(place,"ul");
	var title = getParam(params,"anon","");
	if(title == "" && tiddler instanceof Tiddler)
		title = tiddler.title;
	var sep = getParam(params,"sep"," ");
	theList.setAttribute("title",this.tooltip.format([title]));
	var tagged = store.getTaggedTiddlers(title);
	var prompt = tagged.length == 0 ? this.labelNotTag : this.label;
	createTiddlyElement(theList,"li",null,"listTitle",prompt.format([title,tagged.length]));
	for(var t=0; t<tagged.length; t++)
		{
		createTiddlyLink(createTiddlyElement(theList,"li"),tagged[t].title,true);
		if(t<tagged.length-1)
			createTiddlyText(theList,sep);
		}
}

config.macros.closeAll.handler = function(place)
{
	createTiddlyButton(place,this.label,this.prompt,this.onClick);
}

config.macros.closeAll.onClick = function(e)
{
	story.closeAllTiddlers();
	return false;
}

config.macros.permaview.handler = function(place)
{
	createTiddlyButton(place,this.label,this.prompt,this.onClick);
}

config.macros.permaview.onClick = function(e)
{
	story.permaView();
	return false;
}

config.macros.saveChanges.handler = function(place)
{
	if(!readOnly)
		createTiddlyButton(place,this.label,this.prompt,this.onClick,null,null,this.accessKey);
}

config.macros.saveChanges.onClick = function(e)
{
	saveChanges();
	return false;
}

config.macros.slider.onClickSlider = function(e)
{
	if(!e) var e = window.event;
	var n = this.nextSibling;
	var cookie = n.getAttribute("cookie");
	var isOpen = n.style.display != "none";
	if(anim && config.options.chkAnimate)
		anim.startAnimating(new Slider(n,!isOpen,e.shiftKey || e.altKey,"none"));
	else
		n.style.display = isOpen ? "none" : "block";
	config.options[cookie] = !isOpen;
	saveOptionCookie(cookie);
	return false;
}

config.macros.slider.createSlider = function(place,cookie,title,tooltip)
{
	var cookie = cookie ? cookie : "";
	var btn = createTiddlyButton(place,title,tooltip,this.onClickSlider);
	var panel = createTiddlyElement(null,"div",null,"sliderPanel");
	panel.setAttribute("cookie",cookie);
	panel.style.display = config.options[cookie] ? "block" : "none";
	place.appendChild(panel);
	return panel;
}

config.macros.slider.handler = function(place,macroName,params)
{
	var panel = this.createSlider(place,params[0],params[2],params[3]);
	var text = store.getTiddlerText(params[1]);
	panel.setAttribute("refresh", "content");
	panel.setAttribute("tiddler", params[1]);
	if(text)
		wikify(text,panel,null,store.getTiddler(params[1]));
}

config.macros.option.onChangeOption = function(e)
{
	var opt = this.getAttribute("option");
	var elementType,valueField;
	if(opt)
		{
		switch(opt.substr(0,3))
			{
			case "txt":
				elementType = "input";
				valueField = "value";
				break;
			case "chk":
				elementType = "input";
				valueField = "checked";
				break;
			}
		config.options[opt] = this[valueField];
		saveOptionCookie(opt);
		var nodes = document.getElementsByTagName(elementType);
		for(var t=0; t<nodes.length; t++)
			{
			var optNode = nodes[t].getAttribute("option");
			if(opt == optNode)
				nodes[t][valueField] = this[valueField];
			}
		}
	return(true);
}

config.macros.option.handler = function(place,macroName,params)
{
	var opt = params[0];
	if(config.options[opt] == undefined)
		return;
	var c;
	switch(opt.substr(0,3))
		{
		case "txt":
			c = document.createElement("input");
			c.onkeyup = this.onChangeOption;
			c.setAttribute("option",opt);
			c.className = "txtOptionInput";
			place.appendChild(c);
			c.value = config.options[opt];
			break;
		case "chk":
			c = document.createElement("input");
			c.setAttribute("type","checkbox");
			c.onclick = this.onChangeOption;
			c.setAttribute("option",opt);
			c.className = "chkOptionInput";
			place.appendChild(c);
			c.checked = config.options[opt];
			break;
		}
}



config.macros.newTiddler.createNewTiddlerButton = function(place,title,params,label,prompt,accessKey,newFocus,isJournal)
{
	var tags = [];
	for(var t=1; t<params.length; t++)
		if((params[t].name == "anon" && t != 1) || (params[t].name == "tag"))
			tags.push(params[t].value);
	label = getParam(params,"label",label);
	prompt = getParam(params,"prompt",prompt);
	accessKey = getParam(params,"accessKey",accessKey);
	newFocus = getParam(params,"focus",newFocus);
	var btn = createTiddlyButton(place,label,prompt,this.onClickNewTiddler,null,null,accessKey);
	btn.setAttribute("newTitle",title);
	btn.setAttribute("isJournal",isJournal);
	btn.setAttribute("params",tags.join("|"));
	btn.setAttribute("newFocus",newFocus);
	btn.setAttribute("newTemplate",getParam(params,"template",DEFAULT_EDIT_TEMPLATE));
	var text = getParam(params,"text");
	if(text !== undefined) 
		btn.setAttribute("newText",text);
	return btn;
}

config.macros.newTiddler.onClickNewTiddler = function()
{
	var title = this.getAttribute("newTitle");
	if(this.getAttribute("isJournal"))
		{
		var now = new Date();
		title = now.formatString(title.trim());
		}
	var params = this.getAttribute("params").split("|");
	var focus = this.getAttribute("newFocus");
	var template = this.getAttribute("newTemplate");
	story.displayTiddler(null,title,template);
	var text = this.getAttribute("newText");
	if(typeof text == "string")
		story.getTiddlerField(title,"text").value = text.format([title]);
	for(var t=0;t<params.length;t++)
		story.setTiddlerTag(title,params[t],+1);
	story.focusTiddler(title,focus);
	return false;
}

config.macros.newTiddler.handler = function(place,macroName,params,wikifier,paramString,tiddler)
{
	if(!readOnly)
		{
		params = paramString.parseParams("anon",null,true,false,false);
		var title = params[1] && params[1].name == "anon" ? params[1].value : this.title;
		title = getParam(params,"title",title);
		this.createNewTiddlerButton(place,title,params,this.label,this.prompt,this.accessKey,"title",false);
		}
}

config.macros.newJournal.handler = function(place,macroName,params,wikifier,paramString,tiddler)
{
	if(!readOnly)
		{
		params = paramString.parseParams("anon",null,true,false,false);
		var title = params[1] && params[1].name == "anon" ? params[1].value : "";
		title = getParam(params,"title",title);
		config.macros.newTiddler.createNewTiddlerButton(place,title,params,this.label,this.prompt,this.accessKey,"text",true);
		}
}

config.macros.sparkline.handler = function(place,macroName,params)
{
	var data = [];
	var min = 0;
	var max = 0;
	for(var t=0; t<params.length; t++)
		{
		var v = parseInt(params[t]);
		if(v < min)
			min = v;
		if(v > max)
			max = v;
		data.push(v);
		}
	if(data.length < 1)
		return;
	var box = createTiddlyElement(place,"span",null,"sparkline",String.fromCharCode(160));
	box.title = data.join(",");
	var w = box.offsetWidth;
	var h = box.offsetHeight;
	box.style.paddingRight = (data.length * 2 - w) + "px";
	box.style.position = "relative";
	for(var d=0; d<data.length; d++)
		{
		var tick = document.createElement("img");
		tick.border = 0;
		tick.className = "sparktick";
		tick.style.position = "absolute";
		tick.src = "data:image/gif,GIF89a%01%00%01%00%91%FF%00%FF%FF%FF%00%00%00%C0%C0%C0%00%00%00!%F9%04%01%00%00%02%00%2C%00%00%00%00%01%00%01%00%40%02%02T%01%00%3B";
		tick.style.left = d*2 + "px";
		tick.style.width = "2px";
		var v = Math.floor(((data[d] - min)/(max-min)) * h);
		tick.style.top = (h-v) + "px";
		tick.style.height = v + "px";
		box.appendChild(tick);
		}
}

config.macros.tabs.handler = function(place,macroName,params)
{
	var cookie = params[0];
	var numTabs = (params.length-1)/3;
	var wrapper = createTiddlyElement(null,"div",null,cookie);
	var tabset = createTiddlyElement(wrapper,"div",null,"tabset");
	tabset.setAttribute("cookie",cookie);
	var validTab = false;
	for(var t=0; t<numTabs; t++)
		{
		var label = params[t*3+1];
		var prompt = params[t*3+2];
		var content = params[t*3+3];
		var tab = createTiddlyButton(tabset,label,prompt,this.onClickTab,"tab tabUnselected");
		tab.setAttribute("tab",label);
		tab.setAttribute("content",content);
		tab.title = prompt;
		if(config.options[cookie] == label)
			validTab = true;
		}
	if(!validTab)
		config.options[cookie] = params[1];
	place.appendChild(wrapper);
	this.switchTab(tabset,config.options[cookie]);
}

config.macros.tabs.onClickTab = function(e)
{
	config.macros.tabs.switchTab(this.parentNode,this.getAttribute("tab"));
	return false;
}

config.macros.tabs.switchTab = function(tabset,tab)
{
	var cookie = tabset.getAttribute("cookie");
	var theTab = null
	var nodes = tabset.childNodes;
	for(var t=0; t<nodes.length; t++)
		if(nodes[t].getAttribute && nodes[t].getAttribute("tab") == tab)
			{
			theTab = nodes[t];
			theTab.className = "tab tabSelected";
			}
		else
			nodes[t].className = "tab tabUnselected"
	if(theTab)
		{
		if(tabset.nextSibling && tabset.nextSibling.className == "tabContents")
			tabset.parentNode.removeChild(tabset.nextSibling);
		var tabContent = createTiddlyElement(null,"div",null,"tabContents");
		tabset.parentNode.insertBefore(tabContent,tabset.nextSibling);
		var contentTitle = theTab.getAttribute("content");
		wikify(store.getTiddlerText(contentTitle),tabContent,null,store.getTiddler(contentTitle));
		if(cookie)
			{
			config.options[cookie] = tab;
			saveOptionCookie(cookie);
			}
		}
}

// <<gradient [[tiddler name]] vert|horiz rgb rgb rgb rgb... >>
config.macros.gradient.handler = function(place,macroName,params,wikifier)
{
	var terminator = ">>";
	var panel;
	if(wikifier)
		panel = createTiddlyElement(place,"div",null,"gradient");
	else
		panel = place;
	panel.style.position = "relative";
	panel.style.overflow = "hidden";
	panel.style.zIndex = "0";
	var t;
	if(wikifier)
		{
		var styles = config.formatterHelpers.inlineCssHelper(wikifier);
		config.formatterHelpers.applyCssHelper(panel,styles);
		}
	var colours = [];
	for(t=1; t<params.length; t++)
		{
		var c = new RGB(params[t]);
		if(c)
			colours.push(c);
		}
	drawGradient(panel,params[0] != "vert",colours);
	if(wikifier)
		wikifier.subWikify(panel,terminator);
	if(document.all)
		{
		panel.style.height = "100%";
		panel.style.width = "100%";
		}
}

config.macros.message.handler = function(place,macroName,params)
{
	if(params[0])
		{
		var m = config;
		var p = params[0].split(".");
		for(var t=0; t<p.length; t++)
			{
			if(p[t] in m)
				m = m[p[t]];
			else
				break;
			}
		createTiddlyText(place,m.toString().format(params.splice(1)));
		}
}

config.macros.view.handler = function(place,macroName,params,wikifier,paramString,tiddler)
{
	if((tiddler instanceof Tiddler) && params[0])
		{
		var value = store.getValue(tiddler,params[0]);
		if(value != undefined)
			switch(params[1])
				{
				case undefined:
					highlightify(value,place,highlightHack);
					break;
				case "link":
					createTiddlyLink(place,value,true);
					break;
				case "wikified":
					wikify(value,place,highlightHack,tiddler);
					break;
				case "date":
					value = Date.convertFromYYYYMMDDHHMM(value);
					if(params[2])
						createTiddlyText(place,value.formatString(params[2]));
					else
						createTiddlyText(place,value);
					break;
				}
		}
}

config.macros.edit.handler = function(place,macroName,params,wikifier,paramString,tiddler)
{
	var field = params[0];
	if((tiddler instanceof Tiddler) && field)
		{
		story.setDirty(tiddler.title,true);
		if(field != "text")
			{
				var e = createTiddlyElement(null,"input");
				if(tiddler.isReadOnly())
					e.setAttribute("readOnly","readOnly");
				e.setAttribute("edit",field);
				e.setAttribute("type","text");
				var v = store.getValue(tiddler,field);
				if(!v) 
					v = "";
				e.value = v;
				e.setAttribute("size","40");
				e.setAttribute("autocomplete","off");
				place.appendChild(e);
			}
		else
			{
				var wrapper1 = createTiddlyElement(null,"fieldset",null,"fieldsetFix");
				var wrapper2 = createTiddlyElement(wrapper1,"div");
				var e = createTiddlyElement(wrapper2,"textarea");
				if(tiddler.isReadOnly())
					e.setAttribute("readOnly","readOnly");
				var v = store.getValue(tiddler,field);
				if(!v) 
					v = "";
				e.value = v;
				var rows = 10;
				var lines = v.match(/\n/mg);
				var maxLines = Math.max(parseInt(config.options.txtMaxEditRows),5);
				if(lines != null && lines.length > rows)
					rows = lines.length + 5;
				rows = Math.min(rows,maxLines);
				e.setAttribute("rows",rows);
				e.setAttribute("edit",field);
				place.appendChild(wrapper1);
			}
		}
}

config.macros.tagChooser.onClick = function(e)
{
	if(!e) var e = window.event;
	var lingo = config.views.editor.tagChooser;
	var popup = Popup.create(this);
	var tags = store.getTags();
	if(tags.length == 0)
		createTiddlyText(createTiddlyElement(popup,"li"),lingo.popupNone);
	for(var t=0; t<tags.length; t++)
		{
		var theTag = createTiddlyButton(createTiddlyElement(popup,"li"),tags[t][0],lingo.tagTooltip.format([tags[t][0]]),config.macros.tagChooser.onTagClick);
		theTag.setAttribute("tag",tags[t][0]);
		theTag.setAttribute("tiddler", this.getAttribute("tiddler"));
		}
	Popup.show(popup,false);
	e.cancelBubble = true;
	if(e.stopPropagation) e.stopPropagation();
	return(false);
}

config.macros.tagChooser.onTagClick = function(e)
{
	if(!e) var e = window.event;
	var tag = this.getAttribute("tag");
	var title = this.getAttribute("tiddler");
	if(!readOnly)
		story.setTiddlerTag(title,tag,0);
	return(false);
}

config.macros.tagChooser.handler = function(place,macroName,params,wikifier,paramString,tiddler)
{
	if(tiddler instanceof Tiddler)
		{
		var title = tiddler.title;
		var lingo = config.views.editor.tagChooser;
		var btn = createTiddlyButton(place,lingo.text,lingo.tooltip,this.onClick);
		btn.setAttribute("tiddler", title);
		}
}

// Create a toolbar command button
// place - parent DOM element
// command - reference to config.commands[] member -or- name of member
// tiddler - reference to tiddler that toolbar applies to
// theClass - the class to give the button
config.macros.toolbar.createCommand = function(place,commandName,tiddler,theClass)
{
	if(typeof commandName != "string")
		{
		var c = null;
		for(var t in config.commands)
			if(config.commands[t] == commandName)
				c = t;
		commandName = c;
		}
	if((tiddler instanceof Tiddler) && (typeof commandName == "string"))
		{
		var title = tiddler.title;
		var command = config.commands[commandName];
		var ro = tiddler.isReadOnly();
		var shadow = store.isShadowTiddler(title) && !store.tiddlerExists(title);
		var text = ro && command.readOnlyText ? command.readOnlyText : command.text;
		var tooltip = ro && command.readOnlyTooltip ? command.readOnlyTooltip : command.tooltip;
		if((!ro || (ro && !command.hideReadOnly)) && !(shadow && command.hideShadow))

			{
			var btn = createTiddlyButton(null,text,tooltip,this.onClickCommand);
			btn.setAttribute("commandName", commandName);
			btn.setAttribute("tiddler", title);
			if(theClass)
				addClass(btn,theClass);
			place.appendChild(btn);
			}
		}
}

config.macros.toolbar.onClickCommand = function(e)
{
	if(!e) var e = window.event;
	var command = config.commands[this.getAttribute("commandName")];
	return command.handler(e,this,this.getAttribute("tiddler"));
}

// Invoke the first command encountered from a given place that is tagged with a specified class
config.macros.toolbar.invokeCommand = function(place,theClass,event)
{
	var children = place.getElementsByTagName("a")
	for(var t=0; t<children.length; t++)
		{
		var c = children[t];
		if(hasClass(c,theClass) && c.getAttribute && c.getAttribute("commandName"))
			{
			if(c.onclick instanceof Function)
				c.onclick.call(c,event);
			break;
			}
		}
}

config.macros.toolbar.handler = function(place,macroName,params,wikifier,paramString,tiddler)
{
	for(var t=0; t<params.length; t++)
		{
		var c = params[t];
		var theClass = "";
		switch(c.substr(0,1))
			{
			case "+":
				theClass = "defaultCommand";
				c = c.substr(1);
				break;
			case "-":
				theClass = "cancelCommand";
				c = c.substr(1);
				break;
			}
		if(c in config.commands)
			this.createCommand(place,c,tiddler,theClass);
		}
}

config.macros.plugins.handler = function(place,macroName,params,wikifier,paramString,tiddler)
{
	var e = createTiddlyElement(place,"div");
	e.setAttribute("refresh","macro");
	e.setAttribute("macroName","plugins");
	e.setAttribute("params",paramString);
	this.refresh(e,paramString);
}

config.macros.plugins.refresh = function(place,params)
{
	var selectedRows = [];
	ListView.forEachSelector(place,function(e,rowName) {
			if(e.checked)
				selectedRows.push(e.getAttribute("rowName"));
		});
	removeChildren(place);
	params = params.parseParams("anon");
	var plugins = installedPlugins.slice(0);
	var t,tiddler,p;
	var configTiddlers = store.getTaggedTiddlers("systemConfig");
	for(t=0; t<configTiddlers.length; t++)
		{
		tiddler = configTiddlers[t];
		if(plugins.findByField("title",tiddler.title) == null)
			{
			p = getPluginInfo(tiddler);
			p.executed = false;
			p.log.splice(0,0,this.skippedText);
			plugins.push(p);
			}
		}
	for(t=0; t<plugins.length; t++)
		{
		var p = plugins[t];
		p.forced = p.tiddler.isTagged("systemConfigForce");
		p.disabled = p.tiddler.isTagged("systemConfigDisable");
		p.Selected = selectedRows.indexOf(plugins[t].title) != -1;
		}
	if(plugins.length == 0)
		createTiddlyElement(place,"em",null,null,this.noPluginText);
	else
		ListView.create(place,plugins,this.listViewTemplate,this.onSelectCommand);
}

config.macros.plugins.onSelectCommand = function(command,rowNames)
{
	var t;
	switch(command)
		{
		case "remove":
			for(t=0; t<rowNames.length; t++)
				store.setTiddlerTag(rowNames[t],false,"systemConfig");
			break;
		case "delete":
			if(rowNames.length > 0 && confirm(config.macros.plugins.confirmDeleteText.format([rowNames.join(", ")])))
				{
				for(t=0; t<rowNames.length; t++)
					{
					store.removeTiddler(rowNames[t]);
					story.closeTiddler(rowNames[t],true,false);
					}
				}
			break;
		}
	if(config.options.chkAutoSave)
		saveChanges(true);
}

config.macros.refreshDisplay.handler = function(place)
{
	createTiddlyButton(place,this.label,this.prompt,this.onClick);
}

config.macros.refreshDisplay.onClick = function(e)
{
	refreshAll();
	return false;
}

config.macros.importTiddlers.handler = function(place,macroName,params,wikifier,paramString,tiddler)
{
	if(readOnly)
		{
		createTiddlyElement(place,"div",null,"marked",this.readOnlyWarning);
		return;
		}
	var importer = createTiddlyElement(null,"div",null,"importTiddler wizard");
	createTiddlyElement(importer,"h1",null,null,this.wizardTitle);
	createTiddlyElement(importer,"h2",null,"step1",this.step1);
	var step = createTiddlyElement(importer,"div",null,"wizardStep");
	createTiddlyText(step,this.step1prompt);
	var input = createTiddlyElement(null,"input",null,"txtOptionInput");
	input.type = "text";
	input.size = 50;
	step.appendChild(input);
	importer.inputBox = input;
	createTiddlyElement(step,"br");
	createTiddlyText(step,this.step1promptFile);
	var fileInput = createTiddlyElement(null,"input",null,"txtOptionInput");
	fileInput.type = "file";
	fileInput.size = 50;
	fileInput.onchange = this.onBrowseChange;
	fileInput.onkeyup = this.onBrowseChange;
	step.appendChild(fileInput);
	createTiddlyElement(step,"br");
	createTiddlyText(step,this.step1promptFeeds);
	var feeds = this.getFeeds([{caption: this.step1feedPrompt, name: ""}]);
	createTiddlyDropDown(step,this.onFeedChange,feeds);
	createTiddlyElement(step,"br");
	createTiddlyButton(step,this.fetchLabel,this.fetchPrompt,this.onFetch,null,null,null);
        place.appendChild(importer);
}

config.macros.importTiddlers.getFeeds = function(feeds)
{
	var tagged = store.getTaggedTiddlers("contentPublisher","title");
	for(var t=0; t<tagged.length; t++)
		feeds.push({caption: tagged[t].title, name: store.getTiddlerSlice(tagged[t].title,"URL")});
	return feeds;
}

config.macros.importTiddlers.onFeedChange = function(e)
{
	var importer = findRelated(this,"importTiddler","className","parentNode");
	importer.inputBox.value = this.value;
	this.selectedIndex = 0;
}

config.macros.importTiddlers.onBrowseChange = function(e)
{
	var importer = findRelated(this,"importTiddler","className","parentNode");
	importer.inputBox.value = "file://" + this.value;
}

config.macros.importTiddlers.onFetch = function(e)
{
	var importer = findRelated(this,"importTiddler","className","parentNode");
	var url = importer.inputBox.value;
	var cutoff = findRelated(importer.firstChild,"step2","className","nextSibling");
	while(cutoff)
		{
		var temp = cutoff.nextSibling;
		cutoff.parentNode.removeChild(cutoff);
		cutoff = temp;
		}
	createTiddlyElement(importer,"h2",null,"step2",config.macros.importTiddlers.step2);
	var step = createTiddlyElement(importer,"div",null,"wizardStep",config.macros.importTiddlers.step2Text.format([url]));
	loadRemoteFile(url,config.macros.importTiddlers.onLoad,importer);
}

config.macros.importTiddlers.onLoad = function(status,params,responseText,url,xhr)
{
	if(!status)
		{
		displayMessage(this.fetchError);
		return;
		}
	var importer = params;
	// Check that the tiddler we're in hasn't been closed - doesn't work on IE
//	var p = importer;
//	while(p.parentNode)
//		p = p.parentNode;
//	if(!(p instanceof HTMLDocument))
//		return;
	// Crack out the content - (should be refactored)
	var posOpeningDiv = responseText.indexOf(startSaveArea);
	var limitClosingDiv = responseText.indexOf("<!--POST-BODY-START--"+">");
	var posClosingDiv = responseText.lastIndexOf(endSaveArea,limitClosingDiv == -1 ? responseText.length : limitClosingDiv);
	if((posOpeningDiv == -1) || (posClosingDiv == -1))
		{
		alert(config.messages.invalidFileError.format([url]));
		return;
		}
	var content = "<html><body>" + responseText.substring(posOpeningDiv,posClosingDiv + endSaveArea.length) + "</body></html>";
	// Create the iframe
	var iframe = document.createElement("iframe");
	iframe.style.display = "none";
	importer.insertBefore(iframe,importer.firstChild);
	var doc = iframe.document;
	if(iframe.contentDocument)
		doc = iframe.contentDocument; // For NS6
	else if(iframe.contentWindow)
		doc = iframe.contentWindow.document; // For IE5.5 and IE6
	// Put the content in the iframe
	doc.open();
	doc.writeln(content);
	doc.close();
	// Load the content into a TiddlyWiki() object
	var storeArea = doc.getElementById("storeArea");
	var importStore = new TiddlyWiki();
	importStore.loadFromDiv(storeArea,"store");
	// Get rid of the iframe
	iframe.parentNode.removeChild(iframe);
	// Extract data for the listview
	var tiddlers = [];
	importStore.forEachTiddler(function(title,tiddler)
		{
		var t = {};
		t.title = title;
		t.modified = tiddler.modified;
		t.modifier = tiddler.modifier;
		t.text = tiddler.text.substr(0,50);
		t.tags = tiddler.tags;
		tiddlers.push(t);
		});
	// Display the listview
	createTiddlyElement(importer,"h2",null,"step3",config.macros.importTiddlers.step3);
	var step = createTiddlyElement(importer,"div",null,"wizardStep");
	ListView.create(step,tiddlers,config.macros.importTiddlers.listViewTemplate,config.macros.importTiddlers.onSelectCommand);
	// Save the importer
	importer.store = importStore;
}

config.macros.importTiddlers.onSelectCommand = function(listView,command,rowNames)
{
	var importer = findRelated(listView,"importTiddler","className","parentNode");
	switch(command)
		{
		case "import":
			config.macros.importTiddlers.doImport(importer,rowNames);
			break;
		}
	if(config.options.chkAutoSave)
		saveChanges(true);
}

config.macros.importTiddlers.doImport = function(importer,rowNames)
{
	var theStore = importer.store;
	var overwrite = new Array();
	var t;
	for(t=0; t<rowNames.length; t++)
		{
		if(store.tiddlerExists(rowNames[t]))
			overwrite.push(rowNames[t]);
	}
	if(overwrite.length > 0)
		if(!confirm(this.confirmOverwriteText.format([overwrite.join(", ")])))
			return;
	for(t=0; t<rowNames.length; t++)
		{
		var inbound = theStore.fetchTiddler(rowNames[t]);
		store.saveTiddler(inbound.title, inbound.title, inbound.text, inbound.modifier, inbound.modified, inbound.tags);
		store.fetchTiddler(inbound.title).created = inbound.created;
		store.notify(rowNames[t],false);
		}
	store.notifyAll();
	store.setDirty(true);
	createTiddlyElement(importer,"h2",null,"step4",this.step4.format([rowNames.length]));
	var step = createTiddlyElement(importer,"div",null,"wizardStep");
	for(t=0; t<rowNames.length; t++)
		{
		createTiddlyLink(step,rowNames[t],true);
		createTiddlyElement(step,"br");
		}
	createTiddlyElement(importer,"h2",null,"step5",this.step5);
}
// ---------------------------------------------------------------------------------
// Menu and toolbar commands
// ---------------------------------------------------------------------------------

config.commands.closeTiddler.handler = function(event,src,title)
{
	story.closeTiddler(title,true,event.shiftKey || event.altKey);
	return false;
}

config.commands.closeOthers.handler = function(event,src,title)
{
	story.closeAllTiddlers(title);
	return false;
}

config.commands.editTiddler.handler = function(event,src,title)
{
	clearMessage();
	story.displayTiddler(null,title,DEFAULT_EDIT_TEMPLATE);
	story.focusTiddler(title,"text");
	return false;
}

config.commands.saveTiddler.handler = function(event,src,title)
{
	var newTitle = story.saveTiddler(title,event.shiftKey);
	if(newTitle)
	   story.displayTiddler(null,newTitle);
	return false;
}

config.commands.cancelTiddler.handler = function(event,src,title)
{
	if(story.hasChanges(title) && !readOnly)
		if(!confirm(this.warning.format([title])))
			return false;
	story.setDirty(title,false);
	story.displayTiddler(null,title);
	return false;
}

config.commands.deleteTiddler.handler = function(event,src,title)
{
	var deleteIt = true;
	if (config.options.chkConfirmDelete)
		deleteIt = confirm(this.warning.format([title]));
	if (deleteIt)
		{
		store.removeTiddler(title);
		story.closeTiddler(title,true,event.shiftKey || event.altKey);
		if(config.options.chkAutoSave)
			saveChanges();
		}
	return false;
}

config.commands.permalink.handler = function(event,src,title)
{
	var t = encodeURIComponent(String.encodeTiddlyLink(title));
	if(window.location.hash != t)
		window.location.hash = t;
	return false;
}

config.commands.references.handler = function(event,src,title)
{
	var popup = Popup.create(src);
	if(popup)
		{
		var references = store.getReferringTiddlers(title);
		var c = false;
		for(var r=0; r<references.length; r++)
			if(references[r].title != title && !references[r].isTagged("excludeLists"))
				{
				createTiddlyLink(createTiddlyElement(popup,"li"),references[r].title,true);
				c = true;
				}
		if(!c)
			createTiddlyText(createTiddlyElement(popup,"li",null,"disabled"),this.popupNone);
		}
	Popup.show(popup,false);
	event.cancelBubble = true;
	if (event.stopPropagation) event.stopPropagation();
	return false;
}

config.commands.jump.handler = function(event,src,title)
{
	var popup = Popup.create(src);
	if(popup)
		{
		story.forEachTiddler(function(title,element) {
			createTiddlyLink(createTiddlyElement(popup,"li"),title,true);
			});
		}
	Popup.show(popup,false);
	event.cancelBubble = true;
	if (event.stopPropagation) event.stopPropagation();
	return false;
}

// ---------------------------------------------------------------------------------
// Tiddler() object
// ---------------------------------------------------------------------------------

function Tiddler()
{
	this.title = null;
	this.text = null;
	this.modifier = null;
	this.modified = new Date();
	this.created = new Date();
	this.links = [];
	this.linksUpdated = false;
	this.tags = [];
	return this;
}

Tiddler.prototype.getLinks = function()
{
	if(this.linksUpdated==false)
		this.changed();
	return this.links;
}

// Format the text for storage in an RSS item
Tiddler.prototype.saveToRss = function(url)
{
	var s = [];
	s.push("<item>");
	s.push("<title" + ">" + this.title.htmlEncode() + "</title" + ">");
	s.push("<description>" + wikifyStatic(this.text,null,this).htmlEncode() + "</description>");
	for(var t=0; t<this.tags.length; t++)
		s.push("<category>" + this.tags[t] + "</category>");
	s.push("<link>" + url + "#" + encodeURIComponent(String.encodeTiddlyLink(this.title)) + "</link>");
	s.push("<pubDate>" + this.modified.toGMTString() + "</pubDate>");
	s.push("</item>");
	return(s.join("\n"));
}

// Change the text and other attributes of a tiddler
Tiddler.prototype.set = function(title,text,modifier,modified,tags,created,fields)
{
	this.assign(title,text,modifier,modified,tags,created,fields);
	this.changed();
	return this;
}

// Change the text and other attributes of a tiddler without triggered a tiddler.changed() call
Tiddler.prototype.assign = function(title,text,modifier,modified,tags,created,fields)
{
	if(title != undefined)
		this.title = title;
	if(text != undefined)
		this.text = text;
	if(modifier != undefined)
		this.modifier = modifier;
	if(modified != undefined)
		this.modified = modified;
	if(created != undefined)
		this.created = created;
	if(fields != undefined)
		this.fields = fields;
	if(tags != undefined)
		this.tags = (typeof tags == "string") ? tags.readBracketedList() : tags;
	else if(this.tags == undefined)
		this.tags = [];
	return this;
}

// Get the tags for a tiddler as a string (space delimited, using [[brackets]] for tags containing spaces)
Tiddler.prototype.getTags = function()
{
	return String.encodeTiddlyLinkList(this.tags);
}

// Test if a tiddler carries a tag
Tiddler.prototype.isTagged = function(tag)
{
	return this.tags.indexOf(tag) != -1;
}

// Static method to convert "\n" to newlines, "\s" to "\"
Tiddler.unescapeLineBreaks = function(text)
{
	return text ? text.unescapeLineBreaks() : "";
}

// Convert newlines to "\n", "\" to "\s"
Tiddler.prototype.escapeLineBreaks = function()
{
	return this.text.escapeLineBreaks();
}

// Updates the secondary information (like links[] array) after a change to a tiddler
Tiddler.prototype.changed = function()
{
	this.links = [];
	var t = this.autoLinkWikiWords() ? 0 : 1;
	var tiddlerLinkRegExp = t==0 ? config.textPrimitives.tiddlerAnyLinkRegExp : config.textPrimitives.tiddlerForcedLinkRegExp;
	tiddlerLinkRegExp.lastIndex = 0;
	var formatMatch = tiddlerLinkRegExp.exec(this.text);
	while(formatMatch)
		{
		if(t==0 && formatMatch[1] && formatMatch[1] != this.title) // wikiWordLink
			{
			if(formatMatch.index > 0)
				{
				var preRegExp = new RegExp(config.textPrimitives.unWikiLink+"|"+config.textPrimitives.anyLetter,"mg");
				preRegExp.lastIndex = formatMatch.index-1;
				var preMatch = preRegExp.exec(this.text);
				if(preMatch.index != formatMatch.index-1)
					this.links.pushUnique(formatMatch[1]);
				}
			else
				this.links.pushUnique(formatMatch[1]);
			}
		else if(formatMatch[2-t] && (store.tiddlerExists(formatMatch[3-t]) || store.isShadowTiddler(formatMatch[3-t]))) // titledBrackettedLink
			this.links.pushUnique(formatMatch[3-t]);
		else if(formatMatch[4-t] && formatMatch[4-t] != this.title) // brackettedLink
			this.links.pushUnique(formatMatch[4-t]);
		// Do not add link if match urlPattern (formatMatch[5-t])
		formatMatch = tiddlerLinkRegExp.exec(this.text);
		}
	this.linksUpdated = true;
	return;
}

Tiddler.prototype.getSubtitle = function()
{
	var theModifier = this.modifier;
	if(!theModifier)
		theModifier = config.messages.subtitleUnknown;
	var theModified = this.modified;
	if(theModified)
		theModified = theModified.toLocaleString();
	else
		theModified = config.messages.subtitleUnknown;
	return(config.messages.tiddlerLinkTooltip.format([this.title,theModifier,theModified]));
}

Tiddler.prototype.isReadOnly = function()
{
	return readOnly;
}

Tiddler.prototype.autoLinkWikiWords = function()
{
	return !(this.isTagged("systemConfig") || this.isTagged("excludeMissing"));
}

Tiddler.prototype.generateFingerprint = function()
{
	return "0x" + Crypto.hexSha1Str(this.text);
}

// ---------------------------------------------------------------------------------
// TiddlyWiki() object contains Tiddler()s
// ---------------------------------------------------------------------------------

function TiddlyWiki()
{
	var tiddlers = {}; // Hashmap by name of tiddlers
	this.tiddlersUpdated = false;
	this.namedNotifications = []; // Array of {name:,notify:} of notification functions
	this.notificationLevel = 0;
	this.slices = {}; // map tiddlerName->(map sliceName->sliceValue). Lazy.
	this.clear = function() {
		tiddlers = {};
		this.setDirty(false);
		};
	this.fetchTiddler = function(title) {
		return tiddlers[title];
		};
	this.deleteTiddler = function(title) {
		delete this.slices[title];
		delete tiddlers[title];
		};
	this.addTiddler = function(tiddler) {
		delete this.slices[tiddler.title];
		tiddlers[tiddler.title] = tiddler;
		};
	this.forEachTiddler = function(callback) {
		for(var t in tiddlers)
			{
			var tiddler = tiddlers[t];
			if(tiddler instanceof Tiddler)
				callback.call(this,t,tiddler);
			}
		};
}

// Set the dirty flag
TiddlyWiki.prototype.setDirty = function(dirty)
{
	this.dirty = dirty;
}

TiddlyWiki.prototype.isDirty = function()
{
	return this.dirty;
}

TiddlyWiki.prototype.suspendNotifications = function()
{
	this.notificationLevel--;
}

TiddlyWiki.prototype.resumeNotifications = function()
{
	this.notificationLevel++;
}

// Invoke the notification handlers for a particular tiddler
TiddlyWiki.prototype.notify = function(title,doBlanket)
{
	if(!this.notificationLevel)
		for(var t=0; t<this.namedNotifications.length; t++)
			{
			var n = this.namedNotifications[t];
			if((n.name == null && doBlanket) || (n.name == title))
				n.notify(title);
			}
}

// Invoke the notification handlers for all tiddlers
TiddlyWiki.prototype.notifyAll = function()
{
	if(!this.notificationLevel)
		for(var t=0; t<this.namedNotifications.length; t++)
			{
			var n = this.namedNotifications[t];
			if(n.name)
				n.notify(n.name);
			}
}

// Add a notification handler to a tiddler
TiddlyWiki.prototype.addNotification = function(title,fn)
{
	for (var i=0; i<this.namedNotifications.length; i++)
		if((this.namedNotifications[i].name == title) && (this.namedNotifications[i].notify == fn))
			return this;
	this.namedNotifications.push({name: title, notify: fn});
	return this;
}

TiddlyWiki.prototype.removeTiddler = function(title)
{
	var tiddler = this.fetchTiddler(title);
	if(tiddler)
		{
		this.deleteTiddler(title);
		this.notify(title,true);
		this.setDirty(true);
		}
}

TiddlyWiki.prototype.tiddlerExists = function(title)
{
	var t = this.fetchTiddler(title);
	return (t != undefined);
}

TiddlyWiki.prototype.isShadowTiddler = function(title)
{
	return typeof config.shadowTiddlers[title] == "string";
}

TiddlyWiki.prototype.getTiddler = function(title)
{
	var t = this.fetchTiddler(title);
	if(t != undefined)
		return t;
	else
		return null;
}

TiddlyWiki.prototype.getTiddlerText = function(title,defaultText)
{
	var tiddler = this.fetchTiddler(title);
	if(tiddler)
		return tiddler.text;
	if(!title)
		return defaultText;
	var pos = title.indexOf(config.textPrimitives.sliceSeparator);
	if(pos != -1)
		{
		var slice = this.getTiddlerSlice(title.substr(0,pos),title.substr(pos + config.textPrimitives.sliceSeparator.length));
		if(slice)
			return slice;
		}
	if(this.isShadowTiddler(title))
		return config.shadowTiddlers[title];
	if(defaultText != undefined)
		return defaultText;
	return null;
}

TiddlyWiki.prototype.slicesRE = /(?:[\'\/]*~?(\w+)[\'\/]*\:[\'\/]*\s*(.*?)\s*$)|(?:\|[\'\/]*~?(\w+)\:?[\'\/]*\|\s*(.*?)\s*\|)/gm

// @internal
TiddlyWiki.prototype.calcAllSlices = function(title) 
{
	var slices = {};
	var text = this.getTiddlerText(title,"");
	this.slicesRE.lastIndex = 0;
	do 
		{
			var m = this.slicesRE.exec(text);
			if (m) 
				{
					if (m[1])
						slices[m[1]] = m[2];
					else
						slices[m[3]] = m[4];
				}
		}
	while(m);
	return slices;
}

// Returns the slice of text of the given name
//#
//# A text slice is a substring in the tiddler's text that is defined
//# either like this
//#    aName:  textSlice
//# or
//#    |aName:| textSlice |
//# or
//#    |aName| textSlice |
//#
//# In the text the name (or name:) may be decorated with '' or //. I.e.
//# this would also a possible text slice:
//#
//#    |''aName:''| textSlice |
//#
//# @param name should only contain "word characters" (i.e. "a-ZA-Z_0-9")
//# @return [may be undefined] the (trimmed) text of the specified slice.
TiddlyWiki.prototype.getTiddlerSlice = function(title,sliceName)
{
	var slices = this.slices[title];
	if (!slices) {
		slices = this.calcAllSlices(title);
		this.slices[title] = slices;
	}
	return slices[sliceName];
}

// Build an hashmap of the specified named slices of a tiddler
TiddlyWiki.prototype.getTiddlerSlices = function(title,sliceNames)
{
	var r = {};
	for(var t=0; t<sliceNames.length; t++)
		{
		var slice = this.getTiddlerSlice(title,sliceNames[t]);
		if(slice)
			r[sliceNames[t]] = slice;
		}
	return r;
}

TiddlyWiki.prototype.getRecursiveTiddlerText = function(title,defaultText,depth)
{
	var bracketRegExp = new RegExp("(?:\\[\\[([^\\]]+)\\]\\])","mg");
	var text = this.getTiddlerText(title,null);
	if(text == null)
		return defaultText;
	var textOut = [];
	var lastPos = 0;
	do {
		var match = bracketRegExp.exec(text);
		if(match)
			{
			textOut.push(text.substr(lastPos,match.index-lastPos));
			if(match[1])
				{
				if(depth <= 0)
					textOut.push(match[1]);
				else
					textOut.push(this.getRecursiveTiddlerText(match[1],"[[" + match[1] + "]]",depth-1));
				}
			lastPos = match.index + match[0].length;
			}
		else
			textOut.push(text.substr(lastPos));
	} while(match);
	return(textOut.join(""));
}

TiddlyWiki.prototype.setTiddlerTag = function(title,status,tag)
{
	var tiddler = this.fetchTiddler(title);
	if(tiddler)
		{
		var t = tiddler.tags.indexOf(tag);
		if(t != -1)
			tiddler.tags.splice(t,1);
		if(status)
			tiddler.tags.push(tag);
		tiddler.changed();
		this.notify(title,true);
		this.setDirty(true);
		}
}

TiddlyWiki.prototype.saveTiddler = function(title,newTitle,newBody,modifier,modified,tags,fields)
{
	var tiddler = this.fetchTiddler(title);
	var created;
	if(tiddler)
		{
		created = tiddler.created; // Preserve created date
		this.deleteTiddler(title);
		}
	else
		{
		tiddler = new Tiddler();
		created = modified;
		}
	tiddler.set(newTitle,newBody,modifier,modified,tags,created,fields);
	this.addTiddler(tiddler);
	if(title != newTitle)
		this.notify(title,true);
	this.notify(newTitle,true);
	this.setDirty(true);
	return tiddler;
}

TiddlyWiki.prototype.createTiddler = function(title)
{
	var tiddler = this.fetchTiddler(title);
	if(!tiddler)
		{
		tiddler = new Tiddler();
		tiddler.title = title;
		this.addTiddler(tiddler);
		this.setDirty(true);
		}
	return tiddler;
}

// Load contents of a tiddlywiki from an HTML DIV
TiddlyWiki.prototype.loadFromDiv = function(src,idPrefix,noUpdate)
{
	this.idPrefix = idPrefix;
	var storeElem = (typeof src == "string") ? document.getElementById(src) : src;
	var tiddlers = this.getLoader().loadTiddlers(this,storeElem.childNodes);
	this.setDirty(false);
	if(!noUpdate)
		{
		for(var i = 0;i<tiddlers.length; i++)
			tiddlers[i].changed();
		}
}

TiddlyWiki.prototype.updateTiddlers = function()
{
	this.tiddlersUpdated = true;
	this.forEachTiddler(function(title,tiddler) {
		tiddler.changed();
		});
}

// Return all tiddlers formatted as an HTML string
TiddlyWiki.prototype.allTiddlersAsHtml = function()
{
	return store.getSaver().externalize(store);
}

// Return an array of tiddlers matching a search regular expression
TiddlyWiki.prototype.search = function(searchRegExp,sortField,excludeTag)
{
	var candidates = this.reverseLookup("tags",excludeTag,false);
	var results = [];
	for(var t=0; t<candidates.length; t++)
		{
		if((candidates[t].title.search(searchRegExp) != -1) || (candidates[t].text.search(searchRegExp) != -1))
			results.push(candidates[t]);
		}
	if(!sortField)
		sortField = "title";
	results.sort(function(a,b) {return a[sortField] < b[sortField] ? -1 : (a[sortField] == b[sortField] ? 0 : +1);});
	return results;
}

// Return an array of all the tags in use. Each member of the array is another array where [0] is the name of the tag and [1] is the number of occurances
TiddlyWiki.prototype.getTags = function()
{
	var results = [];
	this.forEachTiddler(function(title,tiddler) {
		for(var g=0; g<tiddler.tags.length; g++)
			{
			var tag = tiddler.tags[g];
			var f = false;
			for(var c=0; c<results.length; c++)
				if(results[c][0] == tag)
					{
					f = true;
					results[c][1]++;
					}
			if(!f)
				results.push([tag,1]);
			}
		});
	results.sort(function(a,b) {return a[0].toLowerCase() < b[0].toLowerCase() ? -1 : (a[0].toLowerCase() == b[0].toLowerCase() ? 0 : +1);});
	return results;
}

// Return an array of the tiddlers that are tagged with a given tag
TiddlyWiki.prototype.getTaggedTiddlers = function(tag,sortField)
{
	return this.reverseLookup("tags",tag,true,sortField);
}

// Return an array of the tiddlers that link to a given tiddler
TiddlyWiki.prototype.getReferringTiddlers = function(title,unusedParameter,sortField)
{
	if(!this.tiddlersUpdated)
		this.updateTiddlers();
	return this.reverseLookup("links",title,true,sortField);
}

// Return an array of the tiddlers that do or do not have a specified entry in the specified storage array (ie, "links" or "tags")
// lookupMatch == true to match tiddlers, false to exclude tiddlers
TiddlyWiki.prototype.reverseLookup = function(lookupField,lookupValue,lookupMatch,sortField)
{
	var results = [];
	this.forEachTiddler(function(title,tiddler) {
		var f = !lookupMatch;
		for(var lookup=0; lookup<tiddler[lookupField].length; lookup++)
			if(tiddler[lookupField][lookup] == lookupValue)
				f = lookupMatch;
		if(f)
			results.push(tiddler);
		});
	if(!sortField)
		sortField = "title";
	results.sort(function(a,b) {return a[sortField] < b[sortField] ? -1 : (a[sortField] == b[sortField] ? 0 : +1);});
	return results;
}

// Return the tiddlers as a sorted array
TiddlyWiki.prototype.getTiddlers = function(field,excludeTag)
{
	var results = [];
	this.forEachTiddler(function(title,tiddler) {
		if(excludeTag == undefined || !tiddler.isTagged(excludeTag))
			results.push(tiddler);
		});
	if(field)
		results.sort(function(a,b) {return a[field] < b[field] ? -1 : (a[field] == b[field] ? 0 : +1);});
	return results;
}

// Return array of names of tiddlers that are referred to but not defined
TiddlyWiki.prototype.getMissingLinks = function(sortField)
{
	if(!this.tiddlersUpdated)
		this.updateTiddlers();
	var results = [];
	this.forEachTiddler(function (title,tiddler) {
		for(var n=0; n<tiddler.links.length;n++)
			{
			var link = tiddler.links[n];
			if(this.fetchTiddler(link) == null && !this.isShadowTiddler(link))
				results.pushUnique(link);
			}
		});
	results.sort();
	return results;
}

// Return an array of names of tiddlers that are defined but not referred to
TiddlyWiki.prototype.getOrphans = function()
{
	var results = [];
	this.forEachTiddler(function (title,tiddler) {
		if(this.getReferringTiddlers(title).length == 0 && !tiddler.isTagged("excludeLists"))
			results.push(title);
		});
	results.sort();
	return results;
}

// Return an array of names of all the shadow tiddlers
TiddlyWiki.prototype.getShadowed = function()
{
	var results = [];
	for(var t in config.shadowTiddlers)
		if(typeof config.shadowTiddlers[t] == "string")
			results.push(t);
	results.sort();
	return results;
}

// Resolves a Tiddler reference or tiddler title into a Tiddler object, or null if it doesn't exist
TiddlyWiki.prototype.resolveTiddler = function(tiddler) 
{
	var t = (typeof tiddler == 'string') ? this.getTiddler(tiddler) : tiddler;
	return t instanceof Tiddler ? t : null;
}

TiddlyWiki.prototype.getLoader = function() 
{
	if (!this.loader) 
		this.loader = new TW21Loader();
	return this.loader;
}
 
TiddlyWiki.prototype.getSaver = function() 
{
	if (!this.saver) 
		this.saver = new TW21Saver();
	return this.saver;
}

// Returns true if path is a valid field name (path),
// i.e. a sequence of identifiers, separated by '.'
TiddlyWiki.isValidFieldName = function (name) {
	var match = /[a-zA-Z_]\w*(\.[a-zA-Z_]\w*)*/.exec(name);
	return match && (match[0] == name);
}

// Throws an exception when name is not a valid field name.
TiddlyWiki.checkFieldName = function(name) {
	if (!TiddlyWiki.isValidFieldName(name))
		throw config.messages.invalidFieldName.format([name]);
}

function StringFieldAccess(n, readOnly) {
	this.set = readOnly 
		? function(t,v) {if (v != t[n]) throw config.messages.fieldCannotBeChanged.format([n]);}
		: function(t,v) {if (v != t[n]) {t[n] = v; return true;}};
	this.get = function(t) {return t[n];};
}

function DateFieldAccess(n) {
	this.set = function(t,v) {
			var d = v instanceof Date ? v : Date.convertFromYYYYMMDDHHMM(v); 
			if (d != t[n]) {
				t[n] = d; return true;
			}
		};
	this.get = function(t)   {return t[n].convertToYYYYMMDDHHMM();}
}

function LinksFieldAccess(n) {
	this.set = function(t,v) {
			var s = (typeof v == "string") ? v.readBracketedList() : v; 
			if (s.toString() != t[n].toString()) {
				t[n] = s; return true;
			}
		};
	this.get = function(t)   {return String.encodeTiddlyLinkList(t[n]);}
}

TiddlyWiki.standardFieldAccess = {
	// The set functions return true when setting the data has changed the value.
	
	"title":    new StringFieldAccess("title", true),
	// Handle the "tiddler" field name as the title
	"tiddler":  new StringFieldAccess("title", true),
	
	"text":     new StringFieldAccess("text"),
	"modifier": new StringFieldAccess("modifier"),
	"modified": new DateFieldAccess("modified"),
	"created":  new DateFieldAccess("created"),
	"tags":     new LinksFieldAccess("tags")
};

TiddlyWiki.isStandardField = function(name) {
	return TiddlyWiki.standardFieldAccess[name] != undefined;
}

// Sets the value of the given field of the tiddler to the value. 
// Setting an ExtendedField's value to null or undefined removes the field. 
// Setting a namespace to undefined removes all fields of that namespace.
// The fieldName is case-insensitive.
// All values will be converted to a string value.
TiddlyWiki.prototype.setValue = function(tiddler, fieldName, value) {
	TiddlyWiki.checkFieldName(fieldName);
	var t = this.resolveTiddler(tiddler);
	if (!t)
		return;
		
	fieldName = fieldName.toLowerCase();

	var isRemove = (value === undefined) || (value === null);

	if (!t.fields) 
		t.fields = {};
		
	var accessor = TiddlyWiki.standardFieldAccess[fieldName];
	if (accessor) {
		if (isRemove)
			// don't remove StandardFields
			return;
		var h = TiddlyWiki.standardFieldAccess[fieldName];
		if (!h.set(t, value))
			return;

	} else {
		var oldValue = t.fields[fieldName];
		
		if (isRemove) {
			if (oldValue !== undefined) {
				// deletes a single field
				delete t.fields[fieldName];
			} else {
				// no concrete value is defined for the fieldName
				// so we guess this is a namespace path.
				
				// delete all fields in a namespace
				var re = new RegExp('^'+fieldName+'\\.');
				var dirty = false;
				for (var n in t.fields) {
					if (n.match(re)) {
						delete t.fields[n];
						dirty = true;
					}
				}
				if (!dirty)
					return
			}
				
		} else {
			// the "normal" set case. value is defined (not null/undefined)
			// For convenience provide a nicer conversion Date->String
 			value = value instanceof Date 
				? value.convertToYYYYMMDDHHMMSSMMM() 
				: String(value);
			if (oldValue == value) 
				return;
			t.fields[fieldName] = value;
		}
	}
	
	// When we are here the tiddler/store really was changed.
	this.notify(t.title,true);
	if (!fieldName.match(/^temp\./))
		this.setDirty(true);
}

// Returns the value of the given field of the tiddler. 
// The fieldName is case-insensitive.
// Will only return String values (or undefined).
TiddlyWiki.prototype.getValue = function(tiddler, fieldName) {
	var t = this.resolveTiddler(tiddler);
	if (!t)
		return undefined;

	fieldName = fieldName.toLowerCase();

	var accessor = TiddlyWiki.standardFieldAccess[fieldName];
	if (accessor) {
		return accessor.get(t);
	}
	
	return t.fields ? t.fields[fieldName] : undefined;
}

// Calls the callback function for every field in the tiddler.
//
// When callback function returns a non-false value the iteration stops 
// and that value is returned. 
//
// The order of the fields is not defined.
// 
// @param callback a function(tiddler, fieldName, value). 
// 
TiddlyWiki.prototype.forEachField = function(tiddler, callback, onlyExtendedFields) {
	var t = this.resolveTiddler(tiddler);
	if (!t)
		return undefined;
	
	if (t.fields) {
		for (var n in t.fields) {
			var result = callback(t, n, t.fields[n]);
			if (result)
				return result;
		}
	}
	
	if (onlyExtendedFields)
		return undefined;

	for (var n in TiddlyWiki.standardFieldAccess) {
		if (n == "tiddler")
			// even though the "title" field can also be referenced through the name "tiddler"
			// we only visit this field once.
			continue;
			
		var result = callback(t, n, TiddlyWiki.standardFieldAccess[n].get(t));
		if (result)
			return result;
	}

	return undefined;
};
// ---------------------------------------------------------------------------------
// Story functions
// ---------------------------------------------------------------------------------

// A story is a HTML div containing a sequence of tiddlers that can be manipulated
// container - id of containing element
// idPrefix - string prefix prepended to title to make ids for tiddlers in this story
function Story(container,idPrefix)
{
	this.container = container;
	this.idPrefix = idPrefix;
	this.highlightRegExp = null;
}

// Iterate through all the tiddlers in a story
// fn - callback function to be called for each tiddler. Arguments are:
//		tiddler - reference to Tiddler object
//		element - reference to tiddler display element
Story.prototype.forEachTiddler = function(fn)
{
	var place = document.getElementById(this.container);
	if(!place)
		return;
	var e = place.firstChild;
	while(e)
		{
		var n = e.nextSibling;
		var title = e.getAttribute("tiddler");
		fn.call(this,title,e);
		e = n;
		}
}

// Display several tiddlers given their titles in an array. Parameters same as displayTiddler(), except:
// titles - array of string titles
Story.prototype.displayTiddlers = function(srcElement,titles,template,animate,slowly)
{
	for(var t = titles.length-1;t>=0;t--)
		this.displayTiddler(srcElement,titles[t],template,animate,slowly);
}

// Display a given tiddler with a given template. If the tiddler is already displayed but with a different
// template, it is switched to the specified template
// srcElement - reference to element from which this one is being opened -or-
//              special positions "top", "bottom"
// title - title of tiddler to display
// template - the name of the tiddler containing the template -or-
//			  one of the constants DEFAULT_VIEW_TEMPLATE and DEFAULT_EDIT_TEMPLATE -or-
//			  null or undefined to indicate the current template if there is one, DEFAULT_VIEW_TEMPLATE if not
// animate - whether to perform animations
// slowly - whether to perform animations in slomo
Story.prototype.displayTiddler = function(srcElement,title,template,animate,slowly)
{
	var place = document.getElementById(this.container);
	var tiddlerElem = document.getElementById(this.idPrefix + title);
	if(tiddlerElem)
		this.refreshTiddler(title,template);
	else
		{
		var before = this.positionTiddler(srcElement);
		tiddlerElem = this.createTiddler(place,before,title,template);
		}
	if(srcElement && typeof srcElement !== "string")
		{
		if(anim && config.options.chkAnimate && (animate == undefined || animate == true))
			anim.startAnimating(new Cascade(title,srcElement,tiddlerElem,slowly),new Scroller(tiddlerElem,slowly));
		else
			window.scrollTo(0,ensureVisible(tiddlerElem));
		}
}

// Figure out the appropriate position for a newly opened tiddler
// srcElement - reference to the element containing the link to the tiddler -or-
//              special positions "top", "bottom"
// returns - reference to the tiddler that the new one should appear before (null for the bottom of the story)
Story.prototype.positionTiddler = function(srcElement)
{
	var place = document.getElementById(this.container);
	var before;
	if(typeof srcElement == "string")
		{
		switch(srcElement)
			{
			case "top":
				before = place.firstChild;
				break;
			case "bottom":
				before = null;
				break;
			}
		}
	else
		{
		var after = this.findContainingTiddler(srcElement);
		if(after == null)
			before = place.firstChild;
		else if(after.nextSibling)
			before = after.nextSibling;
		else
			before = null;
		}
	return before;
}

// Create a tiddler frame at the appropriate place in a story column
// place - reference to parent element
// before - null, or reference to element before which to insert new tiddler
// title - title of new tiddler
// template - the name of the tiddler containing the template or one of the constants DEFAULT_VIEW_TEMPLATE and DEFAULT_EDIT_TEMPLATE
Story.prototype.createTiddler = function(place,before,title,template)
{
	var tiddlerElem = createTiddlyElement(null,"div",this.idPrefix + title,"tiddler");
	tiddlerElem.setAttribute("refresh","tiddler");
	place.insertBefore(tiddlerElem,before);
	this.refreshTiddler(title,template);
	return tiddlerElem;
}

// Overridable for choosing the name of the template to apply for a tiddler
Story.prototype.chooseTemplateForTiddler = function(title,template)
{
	if(!template)
		template = DEFAULT_VIEW_TEMPLATE;
	if(template == DEFAULT_VIEW_TEMPLATE || template == DEFAULT_EDIT_TEMPLATE)
		template = config.tiddlerTemplates[template];
	return template;
}

// Overridable for extracting the text of a template from a tiddler
Story.prototype.getTemplateForTiddler = function(title,template,tiddler)
{
	return store.getRecursiveTiddlerText(template,null,10);
}

// Apply a template to an existing tiddler if it is not already displayed using that template
// title - title of tiddler to update
// template - the name of the tiddler containing the template or one of the constants DEFAULT_VIEW_TEMPLATE and DEFAULT_EDIT_TEMPLATE
// force - if true, forces the refresh even if the template hasn't changedd
Story.prototype.refreshTiddler = function(title,template,force)
{
	var tiddlerElem = document.getElementById(this.idPrefix + title);
	if(tiddlerElem)
		{
		if(tiddlerElem.getAttribute("dirty") == "true" && !force)
			return tiddlerElem;
		template = this.chooseTemplateForTiddler(title,template);
		var currTemplate = tiddlerElem.getAttribute("template");
		if((template != currTemplate) || force)
			{
			var tiddler = store.getTiddler(title);
			if(!tiddler)
				{
				tiddler = new Tiddler();
				if(store.isShadowTiddler(title))
					tiddler.set(title,store.getTiddlerText(title),config.views.wikified.shadowModifier,version.date,[],version.date);
				else
					{
					var text = template=="EditTemplate"
								? config.views.editor.defaultText.format([title])
								: config.views.wikified.defaultText.format([title]);
					tiddler.set(title,text,config.views.wikified.defaultModifier,version.date,[],version.date);
					}
				}
			tiddlerElem.setAttribute("tags",tiddler.tags.join(" "));
			tiddlerElem.setAttribute("tiddler",title);
			tiddlerElem.setAttribute("template",template);
			var me = this;
			tiddlerElem.onmouseover = this.onTiddlerMouseOver;
			tiddlerElem.onmouseout = this.onTiddlerMouseOut;
			tiddlerElem.ondblclick = this.onTiddlerDblClick;
			tiddlerElem[window.event?"onkeydown":"onkeypress"] = this.onTiddlerKeyPress;
			var html = this.getTemplateForTiddler(title,template,tiddler);
			tiddlerElem.innerHTML = html;
			applyHtmlMacros(tiddlerElem,tiddler);
			if(store.getTaggedTiddlers(title).length > 0)
				addClass(tiddlerElem,"isTag");
			else
				removeClass(tiddlerElem,"isTag");
			if(!store.tiddlerExists(title))
				{
				if(store.isShadowTiddler(title))
					addClass(tiddlerElem,"shadow");
				else
					addClass(tiddlerElem,"missing");
				}
			else
				{
				removeClass(tiddlerElem,"shadow");
				removeClass(tiddlerElem,"missing");
				}
			}
		}
	return tiddlerElem;
}

// Refresh all tiddlers in the Story
Story.prototype.refreshAllTiddlers = function() 
{
	var place = document.getElementById(this.container);
	var e = place.firstChild;
	if(!e)
		return;
	this.refreshTiddler(e.getAttribute("tiddler"),e.getAttribute("template"),true);
	while((e = e.nextSibling) != null) 
		this.refreshTiddler(e.getAttribute("tiddler"),e.getAttribute("template"),true);
}

// Default tiddler onmouseover/out event handlers
Story.prototype.onTiddlerMouseOver = function(e)
{
	if(window.addClass instanceof Function)
		addClass(this,"selected");
}

Story.prototype.onTiddlerMouseOut = function(e)
{
	if(window.removeClass instanceof Function)
		removeClass(this,"selected");
}

// Default tiddler ondblclick event handler
Story.prototype.onTiddlerDblClick = function(e)
{
	if(!e) var e = window.event;
	var theTarget = resolveTarget(e);
	if(theTarget && theTarget.nodeName.toLowerCase() != "input" && theTarget.nodeName.toLowerCase() != "textarea")
		{
		if(document.selection && document.selection.empty)
			document.selection.empty();
		config.macros.toolbar.invokeCommand(this,"defaultCommand",e);
		e.cancelBubble = true;
		if (e.stopPropagation) e.stopPropagation();
		return true;
		}
	else
		return false;
}

Story.prototype.onTiddlerKeyPress = function(e)
{
	if(!e) var e = window.event;
	clearMessage();
	var consume = false; 
	var title = this.getAttribute("tiddler");
	var target = resolveTarget(e);
	switch(e.keyCode)
		{
		case 9: // Tab
			if(config.options.chkInsertTabs && target.tagName.toLowerCase() == "textarea")
				{
				replaceSelection(target,String.fromCharCode(9));
				consume = true; 
				}
			if(config.isOpera)
				{
				target.onblur = function()
					{
					this.focus();
					this.onblur = null;
					}
				}
			break;
		case 13: // Ctrl-Enter
		case 10: // Ctrl-Enter on IE PC
		case 77: // Ctrl-Enter is "M" on some platforms
			if(e.ctrlKey)
				{
				blurElement(this);
				config.macros.toolbar.invokeCommand(this,"defaultCommand",e);
				consume = true;
				}
			break; 
		case 27: // Escape
			blurElement(this);
			config.macros.toolbar.invokeCommand(this,"cancelCommand",e);
			consume = true;
			break;
		}
	e.cancelBubble = consume;
	if(consume)
		{
		if(e.stopPropagation) e.stopPropagation(); // Stop Propagation
		e.returnValue = true; // Cancel The Event in IE
		if(e.preventDefault ) e.preventDefault(); // Cancel The Event in Moz
		}
	return(!consume);
};

// Returns the specified field (input or textarea element) in a tiddler, otherwise the first edit field it finds
// or null if it found no edit field at all
Story.prototype.getTiddlerField = function(title,field)
{
	var tiddlerElem = document.getElementById(this.idPrefix + title);
	var e = null;
	if(tiddlerElem != null)
		{
		var children = tiddlerElem.getElementsByTagName("*");
		for (var t=0; t<children.length; t++)
			{
			var c = children[t];
			if(c.tagName.toLowerCase() == "input" || c.tagName.toLowerCase() == "textarea")
				{
				if(!e)
					e = c;
				if(c.getAttribute("edit") == field)
					e = c;
				}
			}
		}
	return e;
}

// Focus a specified tiddler. Attempts to focus the specified field, otherwise the first edit field it finds
Story.prototype.focusTiddler = function(title,field)
{
	var e = this.getTiddlerField(title,field);
	if(e)
		{
		e.focus();
		e.select();
		}
}

// Ensures that a specified tiddler does not have the focus
Story.prototype.blurTiddler = function(title)
{
	var tiddlerElem = document.getElementById(this.idPrefix + title);
	if(tiddlerElem != null && tiddlerElem.focus && tiddlerElem.blur)
		{
		tiddlerElem.focus();
		tiddlerElem.blur();
		}
}

// Adds a specified value to the edit controls (if any) of a particular
// array-formatted field of a particular tiddler (eg "tags")
//  title - name of tiddler
//  tag - value of field, without any [[brackets]]
//  mode - +1 to add the tag, -1 to remove it, 0 to toggle it
//  field - name of field (eg "tags")
Story.prototype.setTiddlerField = function(title,tag,mode,field)
{
	var c = story.getTiddlerField(title,field);

	var tags = c.value.readBracketedList();
	tags.setItem(tag,mode);
	c.value = String.encodeTiddlyLinkList(tags);
}

// The same as setTiddlerField but preset to the "tags" field
Story.prototype.setTiddlerTag = function(title,tag,mode)
{
	Story.prototype.setTiddlerField(title,tag,mode,"tags");
}

// Close a specified tiddler
// title - name of tiddler to close
// animate - whether to perform animations
// slowly - whether to perform animations in slomo
Story.prototype.closeTiddler = function(title,animate,slowly)
{
	var tiddlerElem = document.getElementById(this.idPrefix + title);
	if(tiddlerElem != null)
		{
		clearMessage();
		this.scrubTiddler(tiddlerElem);
		if(anim && config.options.chkAnimate && animate)
			anim.startAnimating(new Slider(tiddlerElem,false,slowly,"all"));
		else
			tiddlerElem.parentNode.removeChild(tiddlerElem);
		}
}

// Scrub IDs from a tiddler. This is so that the 'ghost' of a tiddler while it is being closed
// does not interfere with things
// tiddler - reference to the tiddler element
Story.prototype.scrubTiddler = function(tiddlerElem)
{
	tiddlerElem.id = null;
}

// Set the 'dirty' flag of a tiddler
// title - title of tiddler to change
// dirty - new boolean status of flag
Story.prototype.setDirty = function(title,dirty)
{
	var tiddlerElem = document.getElementById(this.idPrefix + title);
	if(tiddlerElem != null)
		tiddlerElem.setAttribute("dirty",dirty ? "true" : "false");
}

// Is a particular tiddler dirty (with unsaved changes)?
Story.prototype.isDirty = function(title)
{
	var tiddlerElem = document.getElementById(this.idPrefix + title);
	if(tiddlerElem != null)
		return tiddlerElem.getAttribute("dirty") == "true";
	return null;
}

// Determine whether any open tiddler are dirty
Story.prototype.areAnyDirty = function()
{
	var r = false;
	this.forEachTiddler(function(title,element) {
		if(this.isDirty(title))
			r = true;
		});
	return r;
}

// Close all tiddlers in the story
Story.prototype.closeAllTiddlers = function(exclude)
{
	clearMessage();
	this.forEachTiddler(function(title,element) {
		if((title != exclude) && element.getAttribute("dirty") != "true")
			this.closeTiddler(title);
		});
	window.scrollTo(0,0);
}

// Check if there are any tiddlers in the story
Story.prototype.isEmpty = function()
{
	var place = document.getElementById(this.container);
	return(place && place.firstChild == null);
}

// Perform a search and display the result
// text - text to search for
// useCaseSensitive - true for case sensitive matching
// useRegExp - true to interpret text as a RegExp
Story.prototype.search = function(text,useCaseSensitive,useRegExp)
{
	this.closeAllTiddlers();
	highlightHack = new RegExp(useRegExp ?	 text : text.escapeRegExp(),useCaseSensitive ? "mg" : "img");
	var matches = store.search(highlightHack,"title","excludeSearch");
	var titles = [];
	for(var t=matches.length-1; t>=0; t--)
		titles.push(matches[t].title);
	this.displayTiddlers(null,titles);
	highlightHack = null;
	var q = useRegExp ? "/" : "'";
	if(matches.length > 0)
		displayMessage(config.macros.search.successMsg.format([titles.length.toString(),q + text + q]));
	else
		displayMessage(config.macros.search.failureMsg.format([q + text + q]));
}

// Determine if the specified element is within a tiddler in this story
// e - reference to an element
// returns: reference to a tiddler element or null if none
Story.prototype.findContainingTiddler = function(e)
{
	while(e && !hasClass(e,"tiddler"))
		e = e.parentNode;
	return(e);
}

// Gather any saveable fields from a tiddler element
// e - reference to an element to scan recursively
// fields - object to contain gathered field values
Story.prototype.gatherSaveFields = function(e,fields)
{
	if(e && e.getAttribute)
		{
		var f = e.getAttribute("edit");
		if(f)
			fields[f] = e.value.replace(/\r/mg,"");;
		if(e.hasChildNodes())
			{
			var c = e.childNodes;
			for(var t=0; t<c.length; t++)
				this.gatherSaveFields(c[t],fields)
			}
		}
}

// Determine whether a tiddler has any edit fields, and if so if their values have been changed
// title - name of tiddler
Story.prototype.hasChanges = function(title)
{
	var e = document.getElementById(this.idPrefix + title);
	if(e != null)
		{
		var fields = {};
		this.gatherSaveFields(e,fields);
		var tiddler = store.fetchTiddler(title);
		if (!tiddler)
			return false;
		for(var n in fields)
			if (store.getValue(title,n) != fields[n])
				return true;
		}
	return false;
}

// Save any open edit fields of a tiddler and updates the display as necessary
// title - name of tiddler
// minorUpdate - true if the modified date shouldn't be updated
// returns: title of saved tiddler, or null if not saved
Story.prototype.saveTiddler = function(title,minorUpdate)
{
	var tiddlerElem = document.getElementById(this.idPrefix + title);
	if(tiddlerElem != null)
		{
		var fields = {};
		this.gatherSaveFields(tiddlerElem,fields);
		var newTitle = fields.title ? fields.title : title;
		if(store.tiddlerExists(newTitle) && newTitle != title)
			{
			if(confirm(config.messages.overwriteWarning.format([newTitle.toString()])))
				this.closeTiddler(newTitle,false,false);
			else
				return null;
			}
		tiddlerElem.id = this.idPrefix + newTitle;
		tiddlerElem.setAttribute("tiddler",newTitle);
		tiddlerElem.setAttribute("template",DEFAULT_VIEW_TEMPLATE);
		tiddlerElem.setAttribute("dirty","false");
		if(config.options.chkForceMinorUpdate)
			minorUpdate = !minorUpdate;
		var newDate = new Date();
		store.saveTiddler(title,newTitle,fields.text,config.options.txtUserName,minorUpdate ? undefined : newDate,fields.tags);
		for (var n in fields) 
			if (!TiddlyWiki.isStandardField(n))
				store.setValue(newTitle,n,fields[n]);
		if(config.options.chkAutoSave)
			saveChanges();
		return newTitle;
		}
	return null;
}

Story.prototype.permaView = function()
{
	var links = [];
	this.forEachTiddler(function(title,element) {
		links.push(String.encodeTiddlyLink(title));
		});
	var t = encodeURIComponent(links.join(" "));
	if(t == "")
		t = "#";
	if(window.location.hash != t)
		window.location.hash = t;
}

// ---------------------------------------------------------------------------------
// Message area
// ---------------------------------------------------------------------------------

function getMessageDiv()
{
	var msgArea = document.getElementById("messageArea");
	if(!msgArea)
		return null;
	if(!msgArea.hasChildNodes())
		createTiddlyButton(createTiddlyElement(msgArea,"div",null,"messageToolbar"),
			config.messages.messageClose.text,
			config.messages.messageClose.tooltip,
			clearMessage);
	msgArea.style.display = "block";
	return createTiddlyElement(msgArea,"div");
}

function displayMessage(text,linkText)
{
	var e = getMessageDiv();
	if(!e)
		{
		alert(text);
		return;
		}
	if(linkText)
		{
		var link = createTiddlyElement(e,"a",null,null,text);
		link.href = linkText;
		link.target = "_blank";
		}
	else
		e.appendChild(document.createTextNode(text));
}

function clearMessage()
{
	var msgArea = document.getElementById("messageArea");
	if(msgArea)
		{
		removeChildren(msgArea);
		msgArea.style.display = "none";
		}
	return false;
}

// ---------------------------------------------------------------------------------
// Refresh mechanism
// ---------------------------------------------------------------------------------

config.refreshers = {
	link: function(e,changeList)
		{
		var title = e.getAttribute("tiddlyLink");
		refreshTiddlyLink(e,title);
		return true;
		},
	
	tiddler: function(e,changeList)
		{
		var title = e.getAttribute("tiddler");
		var template = e.getAttribute("template");
		if(changeList && changeList.indexOf(title) != -1 && !story.isDirty(title))
			story.refreshTiddler(title,template,true);
		else
			refreshElements(e,changeList);
		return true;
		},

	content: function(e,changeList)
		{
		var title = e.getAttribute("tiddler");
		var force = e.getAttribute("force");
		if(force != null || changeList == null || changeList.indexOf(title) != -1)
			{
			removeChildren(e);
			wikify(store.getTiddlerText(title,title),e);
			return true;
			}
		else
			return false;
		},

	macro: function(e,changeList)
		{
		var macro = e.getAttribute("macroName");
		var params = e.getAttribute("params");
		if(macro)
			macro = config.macros[macro];
		if(macro && macro.refresh)
			macro.refresh(e,params);
		return true;
		}
};

function refreshElements(root,changeList)
{
	var nodes = root.childNodes;
	for(var c=0; c<nodes.length; c++)
		{
		var e = nodes[c],type;
		if(e.getAttribute)
			type = e.getAttribute("refresh");
		else
			type = null;
		var refresher = config.refreshers[type];
		var refreshed = false;
		if(refresher != undefined)
			refreshed = refresher(e,changeList);
		if(e.hasChildNodes() && !refreshed)
			refreshElements(e,changeList);
		}
}

function applyHtmlMacros(root,tiddler)
{
	var e = root.firstChild;
	while(e)
		{
		var nextChild = e.nextSibling;
		if(e.getAttribute)
			{
			var macro = e.getAttribute("macro");
			if(macro)
				{
				var params = "";
				var p = macro.indexOf(" ");
				if(p != -1)
					{
					params = macro.substr(p+1);
					macro = macro.substr(0,p);
					}
				invokeMacro(e,macro,params,null,tiddler);
				}
			}
		if(e.hasChildNodes())
			applyHtmlMacros(e,tiddler);
		e = nextChild;
		}
}

function refreshPageTemplate(title)
{
	var stash = createTiddlyElement(document.body,"div");
	stash.style.display = "none";
	var display = document.getElementById("tiddlerDisplay");
	var nodes,t;
	if(display)
		{
		nodes = display.childNodes;
		for(t=nodes.length-1; t>=0; t--)
			stash.appendChild(nodes[t]);
		}
	var wrapper = document.getElementById("contentWrapper");
	if(!title)
		title = "PageTemplate";
	var html = store.getRecursiveTiddlerText(title,null,10);
	wrapper.innerHTML = html;
	applyHtmlMacros(wrapper);
	refreshElements(wrapper);
	display = document.getElementById("tiddlerDisplay");
	removeChildren(display);
	if(!display)
		display = createTiddlyElement(wrapper,"div","tiddlerDisplay");
	nodes = stash.childNodes;
	for(t=nodes.length-1; t>=0; t--)
		display.appendChild(nodes[t]);
	stash.parentNode.removeChild(stash);
}

function refreshDisplay(hint)
{
	var e = document.getElementById("contentWrapper");
	if(typeof hint == "string")
		hint = [hint];
	refreshElements(e,hint);
}

function refreshPageTitle()
{
	document.title = wikifyPlain("SiteTitle") + " - " + wikifyPlain("SiteSubtitle");
}

function refreshStyles(title)
{
	setStylesheet(title == null ? "" : store.getRecursiveTiddlerText(title,"",10),title);
}

function refreshColorPalette(title)
{
	if(!startingUp)
		refreshAll();
}

function refreshAll()
{
	refreshPageTemplate();
	refreshDisplay();
	refreshStyles("StyleSheetLayout");
	refreshStyles("StyleSheetColors");
	refreshStyles("StyleSheet");
	refreshStyles("StyleSheetPrint");
}

// ---------------------------------------------------------------------------------
// Options cookie stuff
// ---------------------------------------------------------------------------------

function loadOptionsCookie()
{
	if(safeMode)
		return;
	var cookies = document.cookie.split(";");
	for(var c=0; c<cookies.length; c++)
		{
		var p = cookies[c].indexOf("=");
		if(p != -1)
			{
			var name = cookies[c].substr(0,p).trim();
			var value = cookies[c].substr(p+1).trim();
			switch(name.substr(0,3))
				{
				case "txt":
					config.options[name] = unescape(value);
					break;
				case "chk":
					config.options[name] = value == "true";
					break;
				}
			}
		}
}

function saveOptionCookie(name)
{
	if(safeMode)
		return;
	var c = name + "=";
	switch(name.substr(0,3))
		{
		case "txt":
			c += escape(config.options[name].toString());
			break;
		case "chk":
			c += config.options[name] ? "true" : "false";
			break;
		}
	c += "; expires=Fri, 1 Jan 2038 12:00:00 UTC; path=/";
	document.cookie = c;
}

// ---------------------------------------------------------------------------------
// Saving
// ---------------------------------------------------------------------------------

var saveUsingSafari = false;

var startSaveArea = '<div id="' + 'storeArea">'; // Split up into two so that indexOf() of this source doesn't find it
var endSaveArea = '</d' + 'iv>';

// If there are unsaved changes, force the user to confirm before exitting
function confirmExit()
{
	hadConfirmExit = true;
	if((store && store.isDirty && store.isDirty()) || (story && story.areAnyDirty && story.areAnyDirty()))
		return config.messages.confirmExit;
}

// Give the user a chance to save changes before exitting
function checkUnsavedChanges()
{
	if(store && store.isDirty && store.isDirty() && window.hadConfirmExit === false)
		{
		if(confirm(config.messages.unsavedChangesWarning))
			saveChanges();
		}
}

function updateMarkupBlock(s,blockName,tiddlerName)
{
	return s.replaceChunk(
			"<!--%0-START-->".format([blockName]),
			"<!--%0-END-->".format([blockName]),
			"\n" + store.getRecursiveTiddlerText(tiddlerName,"") + "\n");
}

// Save this tiddlywiki with the pending changes
function saveChanges(onlyIfDirty)
{
	if(onlyIfDirty && !store.isDirty())
		return;
	clearMessage();
	// Get the URL of the document
	var originalPath = document.location.toString();
	// Check we were loaded from a file URL
	if(originalPath.substr(0,5) != "file:")
		{
		alert(config.messages.notFileUrlError);
		if(store.tiddlerExists(config.messages.saveInstructions))
			story.displayTiddler(null,config.messages.saveInstructions);
		return;
		}
	var localPath = getLocalPath(originalPath);
	// Load the original file
	var original = loadFile(localPath);
	if(original == null)
		{
		alert(config.messages.cantSaveError);
		if(store.tiddlerExists(config.messages.saveInstructions))
			story.displayTiddler(null,config.messages.saveInstructions);
		return;
		}
	// Locate the storeArea div's
	var posOpeningDiv = original.indexOf(startSaveArea);
	var limitClosingDiv = original.indexOf("<!--POST-BODY-START--"+">");
	var posClosingDiv = original.lastIndexOf(endSaveArea,limitClosingDiv == -1 ? original.length : limitClosingDiv);
	if((posOpeningDiv == -1) || (posClosingDiv == -1))
		{
		alert(config.messages.invalidFileError.format([localPath]));
		return;
		}
	// Save the backup
	if(config.options.chkSaveBackups)
		{
		var backupPath = getBackupPath(localPath);
		var backup = saveFile(backupPath,original);
		if(backup)
			displayMessage(config.messages.backupSaved,"file://" + backupPath);
		else
			alert(config.messages.backupFailed);
		}
	// Save Rss
	if(config.options.chkGenerateAnRssFeed)
		{
		var rssPath = localPath.substr(0,localPath.lastIndexOf(".")) + ".xml";
		var rssSave = saveFile(rssPath,convertUnicodeToUTF8(generateRss()));
		if(rssSave)
			displayMessage(config.messages.rssSaved,"file://" + rssPath);
		else
			alert(config.messages.rssFailed);
		}
	// Save empty template
	if(config.options.chkSaveEmptyTemplate)
		{
		var emptyPath,p;
		if((p = localPath.lastIndexOf("/")) != -1)
			emptyPath = localPath.substr(0,p) + "/empty.html";
		else if((p = localPath.lastIndexOf("\\")) != -1)
			emptyPath = localPath.substr(0,p) + "\\empty.html";
		else
			emptyPath = localPath + ".empty.html";
		var empty = original.substr(0,posOpeningDiv + startSaveArea.length) + original.substr(posClosingDiv);
		var emptySave = saveFile(emptyPath,empty);
		if(emptySave)
			displayMessage(config.messages.emptySaved,"file://" + emptyPath);
		else
			alert(config.messages.emptyFailed);
		}
	var save;
	try 
		{
		// Save new file
		var revised = original.substr(0,posOpeningDiv + startSaveArea.length) + "\n" +
					convertUnicodeToUTF8(store.allTiddlersAsHtml()) + "\n" +
					original.substr(posClosingDiv);
		var newSiteTitle = convertUnicodeToUTF8((wikifyPlain("SiteTitle") + " - " + wikifyPlain("SiteSubtitle")).htmlEncode());
		revised = revised.replaceChunk("<title"+">","</title"+">"," " + newSiteTitle + " ");
		revised = updateMarkupBlock(revised,"PRE-HEAD","MarkupPreHead");
		revised = updateMarkupBlock(revised,"POST-HEAD","MarkupPostHead");
		revised = updateMarkupBlock(revised,"PRE-BODY","MarkupPreBody");
		revised = updateMarkupBlock(revised,"POST-BODY","MarkupPostBody");
		save = saveFile(localPath,revised);
		}
	catch (e) 
		{
		showException(e);
		}
	if(save)
		{
		displayMessage(config.messages.mainSaved,"file://" + localPath);
		store.setDirty(false);
		}
	else
		alert(config.messages.mainFailed);
}

function getLocalPath(originalPath)
{
	// Remove any location or query part of the URL
	var argPos = originalPath.indexOf("?");
	if(argPos != -1)
		originalPath = originalPath.substr(0,argPos);
	var hashPos = originalPath.indexOf("#");
	if(hashPos != -1)
		originalPath = originalPath.substr(0,hashPos);
	// Convert file://localhost/ to file:///
	if(originalPath.indexOf("file://localhost/") == 0)
		originalPath = "file://" + originalPath.substr(16);
	// Convert to a native file format assuming
	// "file:///x:/path/path/path..." - pc local file --> "x:\path\path\path..."
	// "file://///server/share/path/path/path..." - FireFox pc network file --> "\\server\share\path\path\path..."
	// "file:///path/path/path..." - mac/unix local file --> "/path/path/path..."
	// "file://server/share/path/path/path..." - pc network file --> "\\server\share\path\path\path..."
	var localPath;
	if(originalPath.charAt(9) == ":") // pc local file
		localPath = unescape(originalPath.substr(8)).replace(new RegExp("/","g"),"\\");
	else if(originalPath.indexOf("file://///") == 0) // FireFox pc network file
		localPath = "\\\\" + unescape(originalPath.substr(10)).replace(new RegExp("/","g"),"\\");
	else if(originalPath.indexOf("file:///") == 0) // mac/unix local file
		localPath = unescape(originalPath.substr(7));
	else if(originalPath.indexOf("file:/") == 0) // mac/unix local file
		localPath = unescape(originalPath.substr(5));
	else // pc network file
		localPath = "\\\\" + unescape(originalPath.substr(7)).replace(new RegExp("/","g"),"\\");
	return localPath;
}

function getBackupPath(localPath)
{
	var backSlash = true;
	var dirPathPos = localPath.lastIndexOf("\\");
	if(dirPathPos == -1)
		{
		dirPathPos = localPath.lastIndexOf("/");
		backSlash = false;
		}
	var backupFolder = config.options.txtBackupFolder;
	if(!backupFolder || backupFolder == "")
		backupFolder = ".";
	var backupPath = localPath.substr(0,dirPathPos) + (backSlash ? "\\" : "/") + backupFolder + localPath.substr(dirPathPos);
	backupPath = backupPath.substr(0,backupPath.lastIndexOf(".")) + "." + (new Date()).convertToYYYYMMDDHHMMSSMMM() + ".html";
	return backupPath;
}

function generateRss()
{
	var s = [];
	var d = new Date();
	var u = store.getTiddlerText("SiteUrl");
	// Assemble the header
	s.push("<" + "?xml version=\"1.0\"?" + ">");
	s.push("<rss version=\"2.0\">");
	s.push("<channel>");
	s.push("<title" + ">" + wikifyPlain("SiteTitle").htmlEncode() + "</title" + ">");
	if(u)
		s.push("<link>" + u.htmlEncode() + "</link>");
	s.push("<description>" + wikifyPlain("SiteSubtitle").htmlEncode() + "</description>");
	s.push("<language>en-us</language>");
	s.push("<copyright>Copyright " + d.getFullYear() + " " + config.options.txtUserName.htmlEncode() + "</copyright>");
	s.push("<pubDate>" + d.toGMTString() + "</pubDate>");
	s.push("<lastBuildDate>" + d.toGMTString() + "</lastBuildDate>");
	s.push("<docs>http://blogs.law.harvard.edu/tech/rss</docs>");
	s.push("<generator>TiddlyWiki " + version.major + "." + version.minor + "." + version.revision + "</generator>");
	// The body
	var tiddlers = store.getTiddlers("modified","excludeLists");
	var n = config.numRssItems > tiddlers.length ? 0 : tiddlers.length-config.numRssItems;
	for (var t=tiddlers.length-1; t>=n; t--)
		s.push(tiddlers[t].saveToRss(u));
	// And footer
	s.push("</channel>");
	s.push("</rss>");
	// Save it all
	return s.join("\n");
}


// UTF-8 encoding rules:
// 0x0000 - 0x007F:	0xxxxxxx
// 0x0080 - 0x07FF:	110xxxxx 10xxxxxx
// 0x0800 - 0xFFFF:	1110xxxx 10xxxxxx 10xxxxxx

function convertUTF8ToUnicode(u)
{
	if(window.netscape == undefined)
		return manualConvertUTF8ToUnicode(u);
	else
		return mozConvertUTF8ToUnicode(u);
}

function manualConvertUTF8ToUnicode(utf)
{
	var uni = utf;
	var src = 0;
	var dst = 0;
	var b1, b2, b3;
	var c;
	while(src < utf.length)
		{
		b1 = utf.charCodeAt(src++);
		if(b1 < 0x80)
			dst++;
		else if(b1 < 0xE0)
			{
			b2 = utf.charCodeAt(src++);
			c = String.fromCharCode(((b1 & 0x1F) << 6) | (b2 & 0x3F));
			uni = uni.substring(0,dst++).concat(c,utf.substr(src));
			}
		else
			{
			b2 = utf.charCodeAt(src++);
			b3 = utf.charCodeAt(src++);
			c = String.fromCharCode(((b1 & 0xF) << 12) | ((b2 & 0x3F) << 6) | (b3 & 0x3F));
			uni = uni.substring(0,dst++).concat(c,utf.substr(src));
			}
	}
	return(uni);
}

function mozConvertUTF8ToUnicode(u)
{
	try
		{
		netscape.security.PrivilegeManager.enablePrivilege("UniversalXPConnect");
		var converter = Components.classes["@mozilla.org/intl/scriptableunicodeconverter"].createInstance(Components.interfaces.nsIScriptableUnicodeConverter);
		converter.charset = "UTF-8";
		}
	catch(e)
		{
		return manualConvertUTF8ToUnicode(u);
		} // fallback
	var s = converter.ConvertToUnicode(u);
	var fin = converter.Finish();
	return (fin.length > 0) ? s+fin : s;
}

function convertUnicodeToUTF8(s)
{
	if(window.netscape == undefined)
		return manualConvertUnicodeToUTF8(s);
	else
		return mozConvertUnicodeToUTF8(s);
}

function manualConvertUnicodeToUTF8(s)
{
	var re = /[^\u0000-\u007F]/g ;
	return s.replace(re, function($0) {return("&#" + $0.charCodeAt(0).toString() + ";");})
}

function mozConvertUnicodeToUTF8(s)
{
	try
		{
		netscape.security.PrivilegeManager.enablePrivilege("UniversalXPConnect");
		var converter = Components.classes["@mozilla.org/intl/scriptableunicodeconverter"].createInstance(Components.interfaces.nsIScriptableUnicodeConverter);
		converter.charset = "UTF-8";
		}
	catch(e)
		{
		return manualConvertUnicodeToUTF8(s);
		} // fallback
	var u = converter.ConvertFromUnicode(s);
	var fin = converter.Finish();
	if(fin.length > 0)
		return u + fin;
	else
		return u;
}

function saveFile(fileUrl, content)
{
	var r = null;
	if((r == null) || (r == false))
		r = mozillaSaveFile(fileUrl, content);
	if((r == null) || (r == false))
		r = ieSaveFile(fileUrl, content);
	if((r == null) || (r == false))
		r = javaSaveFile(fileUrl, content);
	return(r);
}

function loadFile(fileUrl)
{
	var r = null;
	if((r == null) || (r == false))
		r = mozillaLoadFile(fileUrl);
	if((r == null) || (r == false))
		r = ieLoadFile(fileUrl);
	if((r == null) || (r == false))
		r = javaLoadFile(fileUrl);
	return(r);
}

// Returns null if it can't do it, false if there's an error, true if it saved OK
function ieSaveFile(filePath, content)
{
	try
		{
		var fso = new ActiveXObject("Scripting.FileSystemObject");
		}
	catch(e)
		{
		//alert("Exception while attempting to save\n\n" + e.toString());
		return(null);
		}
	var file = fso.OpenTextFile(filePath,2,-1,0);
	file.Write(content);
	file.Close();
	return(true);
}

// Returns null if it can't do it, false if there's an error, or a string of the content if successful
function ieLoadFile(filePath)
{
	try
		{
		var fso = new ActiveXObject("Scripting.FileSystemObject");
		var file = fso.OpenTextFile(filePath,1);
		var content = file.ReadAll();
		file.Close();
		}
	catch(e)
		{
		//alert("Exception while attempting to load\n\n" + e.toString());
		return(null);
		}
	return(content);
}

// Returns null if it can't do it, false if there's an error, true if it saved OK
function mozillaSaveFile(filePath, content)
{
	if(window.Components)
		try
			{
			netscape.security.PrivilegeManager.enablePrivilege("UniversalXPConnect");
			var file = Components.classes["@mozilla.org/file/local;1"].createInstance(Components.interfaces.nsILocalFile);
			file.initWithPath(filePath);
			if (!file.exists())
				file.create(0, 0664);
			var out = Components.classes["@mozilla.org/network/file-output-stream;1"].createInstance(Components.interfaces.nsIFileOutputStream);
			out.init(file, 0x20 | 0x02, 00004,null);
			out.write(content, content.length);
			out.flush();
			out.close();
			return(true);
			}
		catch(e)
			{
			//alert("Exception while attempting to save\n\n" + e);
			return(false);
			}
	return(null);
}

// Returns null if it can't do it, false if there's an error, or a string of the content if successful
function mozillaLoadFile(filePath)
{
	if(window.Components)
		try
			{
			netscape.security.PrivilegeManager.enablePrivilege("UniversalXPConnect");
			var file = Components.classes["@mozilla.org/file/local;1"].createInstance(Components.interfaces.nsILocalFile);
			file.initWithPath(filePath);
			if (!file.exists())
				return(null);
			var inputStream = Components.classes["@mozilla.org/network/file-input-stream;1"].createInstance(Components.interfaces.nsIFileInputStream);
			inputStream.init(file, 0x01, 00004, null);
			var sInputStream = Components.classes["@mozilla.org/scriptableinputstream;1"].createInstance(Components.interfaces.nsIScriptableInputStream);
			sInputStream.init(inputStream);
			return(sInputStream.read(sInputStream.available()));
			}
		catch(e)
			{
			//alert("Exception while attempting to load\n\n" + e);
			return(false);
			}
	return(null);
}

function javaUrlToFilename(url)
{
	var f = "//localhost";
	if(url.indexOf(f) == 0)
		return url.substring(f.length);
	var i = url.indexOf(":");
	if(i > 0)
		return url.substring(i-1);
	return url;
}

function javaSaveFile(filePath, content)
{
	try
		{
		if(document.applets["TiddlySaver"])
			return document.applets["TiddlySaver"].saveFile(javaUrlToFilename(filePath),"UTF-8",content);
		}
	catch(e)
		{
		}
	try
		{
		var s = new java.io.PrintStream(new java.io.FileOutputStream(javaUrlToFilename(filePath)));
		s.print(content);
		s.close();
		}
	catch(e)
		{
		return null;
		}
	return true;
}

function javaLoadFile(filePath)
{
	try
		{
	if(document.applets["TiddlySaver"])
		return String(document.applets["TiddlySaver"].loadFile(javaUrlToFilename(filePath),"UTF-8"));
		}
	catch(e)
		{
		}
	var content = [];
	try
		{
		var r = new java.io.BufferedReader(new java.io.FileReader(javaUrlToFilename(filePath)));
		var line;
		while ((line = r.readLine()) != null)
			content.push(new String(line));
		r.close();
		}
	catch(e)
		{
		return null;
		}
	return content.join("\n");
}


// ---------------------------------------------------------------------------------
// Remote HTTP requests
// ---------------------------------------------------------------------------------

// Load a file over http
//   url - the source url
//   callback - function to call when there's a response
//   params - parameter object that gets passed to the callback for storing it's state
// Return value is the underlying XMLHttpRequest object, or 'null' if there was an error
// Callback function is called like this:
//   callback(status,params,responseText,xhr)
//     status - true if OK, false if error
//     params - the parameter object provided to loadRemoteFile()
//     responseText - the text of the file
//     xhr - the underlying XMLHttpRequest object
function loadRemoteFile(url,callback,params)
{
	// Get an xhr object
	var x;
	try
		{
		x = new XMLHttpRequest(); // Modern
		}
	catch(e)
		{
		try
			{
			x = new ActiveXObject("Msxml2.XMLHTTP"); // IE 6
			}
		catch (e)
			{
			return null;
			}
		}
	// Install callback
	x.onreadystatechange = function()
		{
		if (x.readyState == 4)
			{
			if ((x.status == 0 || x.status == 200) && callback)
				{
				callback(true,params,x.responseText,url,x);
			}
			else
				callback(false,params,null,url,x);
			}
		}
	// Send request
	if(window.netscape && window.netscape.security && document.location.protocol.indexOf("http") == -1)
		window.netscape.security.PrivilegeManager.enablePrivilege("UniversalBrowserRead");
	try
		{
		url = url + (url.indexOf("?") < 0 ? "?" : "&") + "nocache=" + Math.random();
		x.open("GET",url,true);
		if (x.overrideMimeType)
			x.overrideMimeType("text/html");
		x.send(null);
		}
	catch (e)
		{
		alert("Error in send " + e);
		return null;
		}
	return x;
}
// ---------------------------------------------------------------------------------
// TiddlyWiki-specific utility functions
// ---------------------------------------------------------------------------------

function createTiddlyButton(theParent,theText,theTooltip,theAction,theClass,theId,theAccessKey)
{
	var theButton = document.createElement("a");
	if(theAction)
		{
		theButton.onclick = theAction;
		theButton.setAttribute("href","javascript:;");
		}
	if(theTooltip)
		theButton.setAttribute("title",theTooltip);
	if(theText)
		theButton.appendChild(document.createTextNode(theText));
	if(theClass)
		theButton.className = theClass;
	else
		theButton.className = "button";
	if(theId)
		theButton.id = theId;
	if(theParent)
		theParent.appendChild(theButton);
	if(theAccessKey)
		theButton.setAttribute("accessKey",theAccessKey);
	return(theButton);
}

function createTiddlyLink(place,title,includeText,theClass,isStatic)
{
	var text = includeText ? title : null;
	var i = getTiddlyLinkInfo(title,theClass)
	var btn;
	if(isStatic)
		btn = createExternalLink(place,"#" + title);
	else
		btn = createTiddlyButton(place,text,i.subTitle,onClickTiddlerLink,i.classes);
	btn.setAttribute("refresh","link");
	btn.setAttribute("tiddlyLink",title);
	return(btn);
}

function refreshTiddlyLink(e,title)
{
	var i = getTiddlyLinkInfo(title,e.className);
	e.className = i.classes;
	e.title = i.subTitle;
}

function getTiddlyLinkInfo(title,currClasses)
{
	var classes = currClasses ? currClasses.split(" ") : [];
	classes.pushUnique("tiddlyLink");
	var tiddler = store.fetchTiddler(title);
	var subTitle;
	if(tiddler)
		{
		subTitle = tiddler.getSubtitle();
		classes.pushUnique("tiddlyLinkExisting");
		classes.remove("tiddlyLinkNonExisting");
		classes.remove("shadow");
		}
	else
		{
		classes.remove("tiddlyLinkExisting");
		classes.pushUnique("tiddlyLinkNonExisting");
		if(store.isShadowTiddler(title))
			{
			subTitle = config.messages.shadowedTiddlerToolTip.format([title]);
			classes.pushUnique("shadow");
			}
		else
			{
			subTitle = config.messages.undefinedTiddlerToolTip.format([title]);
			classes.remove("shadow");
			}
		}
	return {classes: classes.join(" "), subTitle: subTitle};
}

function createExternalLink(place,url)
{
	var theLink = document.createElement("a");
	theLink.className = "externalLink";
	theLink.href = url;
	theLink.title = config.messages.externalLinkTooltip.format([url]);
	if(config.options.chkOpenInNewWindow)
		theLink.target = "_blank";
	place.appendChild(theLink);
	return(theLink);
}

// Event handler for clicking on a tiddly link
function onClickTiddlerLink(e)
{
	if (!e) var e = window.event;
	var theTarget = resolveTarget(e);
	var theLink = theTarget;
	var title = null;
	do {
		title = theLink.getAttribute("tiddlyLink");
		theLink = theLink.parentNode;
	} while(title == null && theLink != null);
	if(title)
		{
		var toggling = e.metaKey || e.ctrlKey;
		if(config.options.chkToggleLinks)
			toggling = !toggling;
		var opening;
		if(toggling && document.getElementById("tiddler" + title))
			story.closeTiddler(title,true,e.shiftKey || e.altKey);
		else
			story.displayTiddler(theTarget,title,null,true,e.shiftKey || e.altKey);
		}
	clearMessage();
	return(false);
}

// Create a button for a tag with a popup listing all the tiddlers that it tags
function createTagButton(place,tag,excludeTiddler)
{
	var theTag = createTiddlyButton(place,tag,config.views.wikified.tag.tooltip.format([tag]),onClickTag);
	theTag.setAttribute("tag",tag);
	if(excludeTiddler)
		theTag.setAttribute("tiddler",excludeTiddler);
	return(theTag);
}

// Event handler for clicking on a tiddler tag
function onClickTag(e)
{
	if (!e) var e = window.event;
	var theTarget = resolveTarget(e);
	var popup = Popup.create(this);
	var tag = this.getAttribute("tag");
	var title = this.getAttribute("tiddler");
	if(popup && tag)
		{
		var tagged = store.getTaggedTiddlers(tag);
		var titles = [];
		var li,r;
		for(r=0;r<tagged.length;r++)
			if(tagged[r].title != title)
				titles.push(tagged[r].title);
		var lingo = config.views.wikified.tag;
		if(titles.length > 0)
			{
			var openAll = createTiddlyButton(createTiddlyElement(popup,"li"),lingo.openAllText.format([tag]),lingo.openAllTooltip,onClickTagOpenAll);
			openAll.setAttribute("tag",tag);
			createTiddlyElement(createTiddlyElement(popup,"li",null,"listBreak"),"div");
			for(r=0; r<titles.length; r++)
				{
				createTiddlyLink(createTiddlyElement(popup,"li"),titles[r],true);
				}
			}
		else
			createTiddlyText(createTiddlyElement(popup,"li",null,"disabled"),lingo.popupNone.format([tag]));
		createTiddlyElement(createTiddlyElement(popup,"li",null,"listBreak"),"div");
		var h = createTiddlyLink(createTiddlyElement(popup,"li"),tag,false);
		createTiddlyText(h,lingo.openTag.format([tag]));
		}
	Popup.show(popup,false);
	e.cancelBubble = true;
	if (e.stopPropagation) e.stopPropagation();
	return(false);
}

// Event handler for 'open all' on a tiddler popup
function onClickTagOpenAll(e)
{
	if (!e) var e = window.event;
	var tag = this.getAttribute("tag");
	var tagged = store.getTaggedTiddlers(tag);
	var titles = [];
	for(var t=0; t<tagged.length; t++)
		titles.push(tagged[t].title);
	story.displayTiddlers(this,titles);
	return(false);
}

function onClickError(e)
{
	if (!e) var e = window.event;
	var popup = Popup.create(this);
	var lines = this.getAttribute("errorText").split("\n");
	for(var t=0; t<lines.length; t++)
		createTiddlyElement(popup,"li",null,null,lines[t]);
	Popup.show(popup,false);
	e.cancelBubble = true;
	if (e.stopPropagation) e.stopPropagation();
	return false;
}

function createTiddlyDropDown(place,onchange,options)
{
	var sel = createTiddlyElement(place,"select");
	sel.onchange = onchange;
	for(var t=0; t<options.length; t++)
		{
		var e = createTiddlyElement(sel,"option",null,null,options[t].caption);
		e.value = options[t].name;
		}
}

function createTiddlyError(place,title,text)
{
	var btn = createTiddlyButton(place,title,null,onClickError,"errorButton");
	if (text) btn.setAttribute("errorText",text);
}

function merge(dst,src,preserveExisting)
{
	for (p in src)
		if (!preserveExisting || dst[p] === undefined)
			dst[p] = src[p];
	return dst;
}

// Returns a string containing the description of an exception, optionally prepended by a message
function exceptionText(e, message)
{
	var s = e.description ? e.description : e.toString();
	return message ? "%0:\n%1".format([message, s]) : s;
}

// Displays an alert of an exception description with optional message
function showException(e, message)
{
	alert(exceptionText(e, message));
}

// ---------------------------------------------------------------------------------
// Animation engine
// ---------------------------------------------------------------------------------

function Animator()
{
	this.running = 0; // Incremented at start of each animation, decremented afterwards. If zero, the interval timer is disabled
	this.timerID = 0; // ID of the timer used for animating
	this.animations = []; // List of animations in progress
	return this;
}

// Start animation engine
Animator.prototype.startAnimating = function() // Variable number of arguments
{
	for(var t=0; t<arguments.length; t++)
		this.animations.push(arguments[t]);
	if(this.running == 0)
		{
		var me = this;
		this.timerID = window.setInterval(function() {me.doAnimate(me);},5);
		}
	this.running += arguments.length;
}

// Perform an animation engine tick, calling each of the known animation modules
Animator.prototype.doAnimate = function(me)
{
	var a = 0;
	while(a < me.animations.length)
		{
		var animation = me.animations[a];
		if(animation.tick())
			a++;
		else
			{
			me.animations.splice(a,1);
			if(--me.running == 0)
				window.clearInterval(me.timerID);
			}
		}
}

// Map a 0..1 value to 0..1, but slow down at the start and end
Animator.slowInSlowOut = function(progress)
{
	return(1-((Math.cos(progress * Math.PI)+1)/2));
}

// ---------------------------------------------------------------------------------
// Cascade animation
// ---------------------------------------------------------------------------------

function Cascade(text,startElement,targetElement,slowly)
{
	var winWidth = findWindowWidth();
	var winHeight = findWindowHeight();
	this.elements = [];
	this.startElement = startElement;
	this.startLeft = findPosX(this.startElement);
	this.startTop = findPosY(this.startElement);
	this.startWidth = Math.min(this.startElement.offsetWidth,winWidth);
	this.startHeight = Math.min(this.startElement.offsetHeight,winHeight);
	this.targetElement = targetElement;
	targetElement.style.position = "relative";
	targetElement.style.zIndex = 2;
	this.targetLeft = findPosX(this.targetElement);
	this.targetTop = findPosY(this.targetElement);
	this.targetWidth = Math.min(this.targetElement.offsetWidth,winWidth);
	this.targetHeight = Math.min(this.targetElement.offsetHeight,winHeight);
	this.progress = -1;
	this.steps = slowly ? config.cascadeSlow : config.cascadeFast;
	this.text = text;
	this.tick();
	return this;
}

Cascade.prototype.tick = function()
{
	this.progress++;
	if(this.progress >= this.steps)
		{
		while(this.elements.length > 0)
			this.removeTail();
		this.targetElement.style.position = "static";
		this.targetElement.style.zIndex = "";
		return false;
		}
	else
		{
		if(this.elements.length > 0 && this.progress > config.cascadeDepth)
			this.removeTail();
		if(this.progress < (this.steps - config.cascadeDepth))
			{
			var f = Animator.slowInSlowOut(this.progress/(this.steps - config.cascadeDepth - 1));
			var e = createTiddlyElement(document.body,"div",null,"cascade",this.text);
			e.style.zIndex = 1;
			e.style.left = this.startLeft + (this.targetLeft-this.startLeft) * f + "px";
			e.style.top = this.startTop + (this.targetTop-this.startTop) * f + "px";
			e.style.width = this.startWidth + (this.targetWidth-this.startWidth) * f + "px";
			e.style.height = this.startHeight + (this.targetHeight-this.startHeight) * f + "px";
			e.style.display = "block";
			this.elements.push(e);
			}
		return true;
		}
}

Cascade.prototype.removeTail = function()
{
	var e = this.elements[0];
	e.parentNode.removeChild(e);
	this.elements.shift();
}

// ---------------------------------------------------------------------------------
// Scroller animation
// ---------------------------------------------------------------------------------

function Scroller(targetElement,slowly)
{
	this.targetElement = targetElement;
	this.startScroll = findScrollY();
	this.targetScroll = ensureVisible(targetElement);
	this.progress = 0;
	this.step = slowly ? config.animSlow : config.animFast;
	return this;
}

Scroller.prototype.tick = function()
{
	this.progress += this.step;
	if(this.progress > 1)
		{
		window.scrollTo(0,this.targetScroll);
		return false;
		}
	else
		{
		var f = Animator.slowInSlowOut(this.progress);
		window.scrollTo(0,this.startScroll + (this.targetScroll-this.startScroll) * f);
		return true;
		}
}

// ---------------------------------------------------------------------------------
// Slider animation
// ---------------------------------------------------------------------------------

// deleteMode - "none", "all" [delete target element and it's children], [only] "children" [but not the target element]
function Slider(element,opening,slowly,deleteMode)
{
	this.element = element;
	element.style.display = "block";
	this.deleteMode = deleteMode;
	this.element.style.height = "auto";
	this.realHeight = element.offsetHeight;
	this.opening = opening;
	this.step = slowly ? config.animSlow : config.animFast;
	if(opening)
		{
		this.progress = 0;
		element.style.height = "0px";
		element.style.display = "block";
		}
	else
		{
		this.progress = 1;
		this.step = -this.step;
		}
	element.style.overflow = "hidden";
	return this;
}

Slider.prototype.stop = function()
{
	if(this.opening)
		{
		this.element.style.height = "auto";
		this.element.style.opacity = 1;
		this.element.style.filter = "alpha(opacity:100)";
		}
	else
		{
		switch(this.deleteMode)
			{
			case "none":
				this.element.style.display = "none";
				break;
			case "all":
				this.element.parentNode.removeChild(this.element);
				break;
			case "children":
				removeChildren(this.element);
				break;
			}
		}
}

Slider.prototype.tick = function()
{
	this.progress += this.step;
	if(this.progress < 0 || this.progress > 1)
		{
		this.stop();
		return false;
		}
	else
		{
		var f = Animator.slowInSlowOut(this.progress);
		var h = this.realHeight * f;
		this.element.style.height = h + "px";
		this.element.style.opacity = f;
		this.element.style.filter = "alpha(opacity:" + f * 100 +")";
		return true;
		}
}

// ---------------------------------------------------------------------------------
// Popup menu
// ---------------------------------------------------------------------------------

var Popup = {
	stack: [] // Array of objects with members root: and popup:
	};

Popup.create = function(root)
{
	Popup.remove();
	var popup = createTiddlyElement(document.body,"ol","popup","popup");
	Popup.stack.push({root: root, popup: popup});
	return popup;
}

Popup.onDocumentClick = function(e)
{
	if (!e) var e = window.event;
	var target = resolveTarget(e);
	if(e.eventPhase == undefined)
		Popup.remove();
	else if(e.eventPhase == Event.BUBBLING_PHASE || e.eventPhase == Event.AT_TARGET)
		Popup.remove();
	return true;
}

Popup.show = function(unused,slowly)
{
	var curr = Popup.stack[Popup.stack.length-1];
	var rootLeft = findPosX(curr.root);
	var rootTop = findPosY(curr.root);
	var rootHeight = curr.root.offsetHeight;
	var popupLeft = rootLeft;
	var popupTop = rootTop + rootHeight;
	var popupWidth = curr.popup.offsetWidth;
	var winWidth = findWindowWidth();
	if(popupLeft + popupWidth > winWidth)
		popupLeft = winWidth - popupWidth;
	curr.popup.style.left = popupLeft + "px";
	curr.popup.style.top = popupTop + "px";
	curr.popup.style.display = "block";
	addClass(curr.root,"highlight");
	if(anim && config.options.chkAnimate)
		anim.startAnimating(new Scroller(curr.popup,slowly));
	else
		window.scrollTo(0,ensureVisible(curr.popup));
}

Popup.remove = function()
{
	if(Popup.stack.length > 0)
		{
		Popup.removeFrom(0);
		}
}

Popup.removeFrom = function(from)
{
	for(var t=Popup.stack.length-1; t>=from; t--)
		{
		var p = Popup.stack[t];
		removeClass(p.root,"highlight");
		p.popup.parentNode.removeChild(p.popup);
		}
	Popup.stack = Popup.stack.slice(0,from);
}

// ---------------------------------------------------------------------------------
// ListView gadget
// ---------------------------------------------------------------------------------

var ListView = {};

// Create a listview
//   place - where in the DOM tree to insert the listview
//   listObject - array of objects to be included in the listview
//   listTemplate - template for the listview
//   callback - callback for a command being selected
//   className - optional classname for the <table> element
ListView.create = function(place,listObject,listTemplate,callback,className)
{
	var table = createTiddlyElement(place,"table",null,className ? className : "listView");
	var thead = createTiddlyElement(table,"thead");
	var r = createTiddlyElement(thead,"tr");
	for(var t=0; t<listTemplate.columns.length; t++)
		{
		var columnTemplate = listTemplate.columns[t];
		var c = createTiddlyElement(r,"th");
		var colType = ListView.columnTypes[columnTemplate.type];
		if(colType && colType.createHeader)
			colType.createHeader(c,columnTemplate,t);
		}
	var tbody = createTiddlyElement(table,"tbody");
	for(var rc=0; rc<listObject.length; rc++)
		{
		rowObject = listObject[rc];
		r = createTiddlyElement(tbody,"tr");
		for(var c=0; c<listTemplate.rowClasses.length; c++)
			{
			if(rowObject[listTemplate.rowClasses[c].field])
				addClass(r,listTemplate.rowClasses[c].className);
			}
		rowObject.rowElement = rowObject;
		rowObject.colElements = {};
		for(var cc=0; cc<listTemplate.columns.length; cc++)
			{
			var c = createTiddlyElement(r,"td");
			var columnTemplate = listTemplate.columns[cc];
			var field = columnTemplate.field;
			var colType = ListView.columnTypes[columnTemplate.type];
			if(colType && colType.createItem)
				colType.createItem(c,rowObject,field,columnTemplate,cc,rc);
			rowObject.colElements[field] = c;
			}
		}
	if(callback && listTemplate.actions)
		createTiddlyDropDown(place,ListView.getCommandHandler(callback),listTemplate.actions);
	if(callback && listTemplate.buttons)
		{
		for(t=0; t<listTemplate.buttons.length; t++)
			{
			var a = listTemplate.buttons[t];
			if(a && a.name != "")
				createTiddlyButton(place,a.caption,null,ListView.getCommandHandler(callback,a.name,a.allowEmptySelection));
			}
		}
	return table;
}

ListView.getCommandHandler = function(callback,name,allowEmptySelection)
{
	return function(e)
		{
		var view = findRelated(this,"TABLE",null,"previousSibling");
		var tiddlers = [];
		ListView.forEachSelector(view,function(e,rowName) {
					if(e.checked)
						tiddlers.push(rowName);
					});
		if(tiddlers.length == 0 && !allowEmptySelection)
			alert(config.messages.nothingSelected);
		else
			{
			if(this.nodeName.toLowerCase() == "select")
				{
				callback(view,this.value,tiddlers);
				this.selectedIndex = 0;
				}
			else
				callback(view,name,tiddlers);
			}
		};
}

// Invoke a callback for each selector checkbox in the listview
//   view - <table> element of listView
//   callback(checkboxElement,rowName)
//     where
//       checkboxElement - DOM element of checkbox
//       rowName - name of this row as assigned by the column template
//   result: true if at least one selector was checked
ListView.forEachSelector = function(view,callback)
{
	var checkboxes = view.getElementsByTagName("input");
	var hadOne = false;
	for(var t=0; t<checkboxes.length; t++)
		{
		var cb = checkboxes[t];
		if(cb.getAttribute("type") == "checkbox")
			{
			var rn = cb.getAttribute("rowName");
			if(rn)
				{
				callback(cb,rn);
				hadOne = true;
				}
			}
		}
	return hadOne;
}

ListView.columnTypes = {};

ListView.columnTypes.String = {
	createHeader: function(place,columnTemplate,col)
		{
			createTiddlyText(place,columnTemplate.title);
		},
	createItem: function(place,listObject,field,columnTemplate,col,row)
		{
			var v = listObject[field];
			if(v != undefined)
				createTiddlyText(place,v);
		}
};

ListView.columnTypes.Date = {
	createHeader: ListView.columnTypes.String.createHeader,
	createItem: function(place,listObject,field,columnTemplate,col,row)
		{
			var v = listObject[field];
			if(v != undefined)
				createTiddlyText(place,v.formatString(columnTemplate.dateFormat));
		}
};

ListView.columnTypes.StringList = {
	createHeader: ListView.columnTypes.String.createHeader,
	createItem: function(place,listObject,field,columnTemplate,col,row)
		{
			var v = listObject[field];
			if(v != undefined)
				{
				for(var t=0; t<v.length; t++)
					{
					createTiddlyText(place,v[t]);
					createTiddlyElement(place,"br");
					}
				}
		}
};

ListView.columnTypes.Selector = {
	createHeader: function(place,columnTemplate,col)
		{
			createTiddlyCheckbox(place,null,false,this.onHeaderChange);
		},
	createItem: function(place,listObject,field,columnTemplate,col,row)
		{
			var e = createTiddlyCheckbox(place,null,listObject[field],null);
			e.setAttribute("rowName",listObject[columnTemplate.rowName]);
		},
	onHeaderChange: function(e)
		{
			var state = this.checked;
			var view = findRelated(this,"TABLE");
			if(!view)
				return;
			ListView.forEachSelector(view,function(e,rowName) {
								e.checked = state;
							});
		}
};

ListView.columnTypes.Tags = {
	createHeader: ListView.columnTypes.String.createHeader,
	createItem: function(place,listObject,field,columnTemplate,col,row)
		{
			var tags = listObject[field];
			createTiddlyText(place,String.encodeTiddlyLinkList(tags));
		}
};

ListView.columnTypes.Boolean = {
	createHeader: ListView.columnTypes.String.createHeader,
	createItem: function(place,listObject,field,columnTemplate,col,row)
		{
			if(listObject[field] == true)
				createTiddlyText(place,columnTemplate.trueText);
			if(listObject[field] == false)
				createTiddlyText(place,columnTemplate.falseText);
		}
};

ListView.columnTypes.TagCheckbox = {
	createHeader: ListView.columnTypes.String.createHeader,
	createItem: function(place,listObject,field,columnTemplate,col,row)
		{
			var e = createTiddlyCheckbox(place,null,listObject[field],this.onChange);
			e.setAttribute("tiddler",listObject.title);
			e.setAttribute("tag",columnTemplate.tag);
		},
	onChange : function(e)
		{
			var tag = this.getAttribute("tag");
			var tiddler = this.getAttribute("tiddler");
			store.setTiddlerTag(tiddler,this.checked,tag);
		}
};

ListView.columnTypes.TiddlerLink = {
	createHeader: ListView.columnTypes.String.createHeader,
	createItem: function(place,listObject,field,columnTemplate,col,row)
		{
			var v = listObject[field];
			if(v != undefined)
				{
				var link = createTiddlyLink(place,listObject[columnTemplate.tiddlerLink],false,null);
				createTiddlyText(link,listObject[field]);
				}
		}
};
// ---------------------------------------------------------------------------------
// Augmented methods for the JavaScript Number(), Array(), String() and Date() objects
// ---------------------------------------------------------------------------------

// Clamp a number to a range
Number.prototype.clamp = function(min,max)
{
	var c = this;
	if(c < min)
		c = min;
	if(c > max)
		c = max;
	return c;
}

// Add indexOf function if browser does not support it
if(!Array.indexOf) {
Array.prototype.indexOf = function(item,from)
{
	if(!from)
		from = 0;
	for(var i=from; i<this.length; i++)
		if(this[i] === item)
			return i;
	return -1;
}}

// Find an entry in a given field of the members of an array
Array.prototype.findByField = function(field,value)
{
	for(var t=0; t<this.length; t++)
		if(this[t][field] == value)
			return t;
	return null;
}

// Return whether an entry exists in an array
Array.prototype.contains = function(item)
{
	return this.indexOf(item) != -1;
};

// Adds, removes or toggles a particular value within an array
//  value - value to add
//  mode - +1 to add value, -1 to remove value, 0 to toggle it
Array.prototype.setItem = function(value,mode)
{
	var p = this.indexOf(value);
	if(mode == 0)
		mode = (p == -1) ? +1 : -1;
	if(mode == +1)
		{
		if(p == -1)
			this.push(value);
		}
	else if(mode == -1)
		{
		if(p != -1)
			this.splice(p,1);
		}
}

// Return whether one of a list of values exists in an array
Array.prototype.containsAny = function(items)
{
	for(var i=0; i<items.length; i++)
		if (this.indexOf(items[i]) != -1)
			return true;
	return false;
};

// Return whether all of a list of values exists in an array
Array.prototype.containsAll = function(items)
{
	for (var i = 0; i<items.length; i++)
		if (this.indexOf(items[i]) == -1)
			return false;
	return true;
};

// Push a new value into an array only if it is not already present in the array. If the optional unique parameter is false, it reverts to a normal push
Array.prototype.pushUnique = function(item,unique)
{
	if(unique != undefined && unique == false)
		this.push(item);
	else
		{
		if(this.indexOf(item) == -1)
			this.push(item);
		}
}

Array.prototype.remove = function(item)
{
	var p = this.indexOf(item);
	if(p != -1)
		this.splice(p,1);
}

// Get characters from the right end of a string
String.prototype.right = function(n)
{
	if(n < this.length)
		return this.slice(this.length-n);
	else
		return this;
}

// Trim whitespace from both ends of a string
String.prototype.trim = function()
{
	return this.replace(/^\s*|\s*$/g,"");
}

// Convert a string from a CSS style property name to a JavaScript style name ("background-color" -> "backgroundColor")
String.prototype.unDash = function()
{
	var s = this.split("-");
	if(s.length > 1)
		for(var t=1; t<s.length; t++)
			s[t] = s[t].substr(0,1).toUpperCase() + s[t].substr(1);
	return s.join("");
}

// Substitute substrings from an array into a format string that includes '%1'-type specifiers
String.prototype.format = function(substrings)
{
	var subRegExp = /(?:%(\d+))/mg;
	var currPos = 0;
	var r = [];
	do {
		var match = subRegExp.exec(this);
		if(match && match[1])
			{
			if(match.index > currPos)
				r.push(this.substring(currPos,match.index));
			r.push(substrings[parseInt(match[1])]);
			currPos = subRegExp.lastIndex;
			}
	} while(match);
	if(currPos < this.length)
		r.push(this.substring(currPos,this.length));
	return r.join("");
}

// Escape any special RegExp characters with that character preceded by a backslash
String.prototype.escapeRegExp = function()
{
	var s = "\\^$*+?()=!|,{}[].";
	var c = this;
	for(var t=0; t<s.length; t++)
		c = c.replace(new RegExp("\\" + s.substr(t,1),"g"),"\\" + s.substr(t,1));
	return c;
}

// Convert "\" to "\s", newlines to "\n" (and remove carriage returns)
String.prototype.escapeLineBreaks = function()
{
	return this.replace(/\\/mg,"\\s").replace(/\n/mg,"\\n").replace(/\r/mg,"");
}

// Convert "\n" to newlines, "\b" to " ", "\s" to "\" (and remove carriage returns)
String.prototype.unescapeLineBreaks = function()
{
	return this.replace(/\\n/mg,"\n").replace(/\\b/mg," ").replace(/\\s/mg,"\\").replace(/\r/mg,"");
}

// Convert & to "&amp;", < to "&lt;", > to "&gt;" and " to "&quot;"
String.prototype.htmlEncode = function()
{
	return(this.replace(/&/mg,"&amp;").replace(/</mg,"&lt;").replace(/>/mg,"&gt;").replace(/\"/mg,"&quot;"));
}

// Convert "&amp;" to &, "&lt;" to <, "&gt;" to > and "&quot;" to "
String.prototype.htmlDecode = function()
{
	return(this.replace(/&amp;/mg,"&").replace(/&lt;/mg,"<").replace(/&gt;/mg,">").replace(/&quot;/mg,"\""));
}

// Parse a space-separated string of name:value parameters where:
//   - the name or the value can be optional (in which case separate defaults are used instead)
//     - in case of ambiguity, a lone word is taken to be a value
//     - if 'cascadeDefaults' is set to true, then the defaults are modified by updated by each specified name or value
//     - name prefixes are not allowed if the 'noNames' parameter is true
//   - if both the name and value are present they must be separated by a colon
//   - the name and the value may both be quoted with single- or double-quotes, double-square brackets
//   - names or values quoted with {{double-curly braces}} are evaluated as a JavaScript expression
//     - as long as the 'allowEval' parameter is true
// The result is an array of objects:
//   result[0] = object with a member for each parameter name, value of that member being an array of values
//   result[1..n] = one object for each parameter, with 'name' and 'value' members
String.prototype.parseParams = function(defaultName,defaultValue,allowEval,noNames,cascadeDefaults)
{
	var parseToken = function(match,p)
		{
		var n;
		if(match[p]) // Double quoted
			n = match[p];
		else if(match[p+1]) // Single quoted
			n = match[p+1];
		else if(match[p+2]) // Double-square-bracket quoted
			n = match[p+2];
		else if(match[p+3]) // Double-brace quoted
			try
				{
				n = match[p+3];
				if(allowEval)
					n = window.eval(n);
				}
			catch(e)
				{
				throw "Unable to evaluate {{" + match[p+3] + "}}: " + exceptionText(e);
				}
		else if(match[p+4]) // Unquoted
			n = match[p+4];
		else if(match[p+5]) // empty quote
			n = "";
		return n;
		};
	var r = [{}];
	var dblQuote = "(?:\"((?:(?:\\\\\")|[^\"])+)\")";
	var sngQuote = "(?:'((?:(?:\\\\\')|[^'])+)')";
	var dblSquare = "(?:\\[\\[((?:\\s|\\S)*?)\\]\\])";
	var dblBrace = "(?:\\{\\{((?:\\s|\\S)*?)\\}\\})";
	var unQuoted = noNames ? "([^\"'\\s]\\S*)" : "([^\"':\\s][^\\s:]*)";
	var emptyQuote = "((?:\"\")|(?:''))";
	var skipSpace = "(?:\\s*)";
	var token = "(?:" + dblQuote + "|" + sngQuote + "|" + dblSquare + "|" + dblBrace + "|" + unQuoted + "|" + emptyQuote + ")";
	var re = noNames
		? new RegExp(token,"mg")
		: new RegExp(skipSpace + token + skipSpace + "(?:(\\:)" + skipSpace + token + ")?","mg");
	var params = [];
	do {
		var match = re.exec(this);
		if(match)
			{
			var n = parseToken(match,1);
			if(noNames)
				r.push({name: "", value: n});
			else
				{
				var v = parseToken(match,8);
				if(v == null && defaultName)
					{
					v = n;
					n = defaultName;
					}
				else if(v == null && defaultValue)
					v = defaultValue;
				r.push({name: n, value: v});
				if(cascadeDefaults)
					{
					defaultName = n;
					defaultValue = v;
					}
				}
			}
	} while(match);
	// Summarise parameters into first element
	for(var t=1; t<r.length; t++)
		{
		if(r[0][r[t].name])
			r[0][r[t].name].push(r[t].value);
		else
			r[0][r[t].name] = [r[t].value];
		}
	return r;
}

// Process a string list of macro parameters into an array. Parameters can be quoted with "", '',
// [[]], {{ }} or left unquoted (and therefore space-separated). Double-braces {{}} results in
// an *evaluated* parameter: e.g. {{config.options.txtUserName}} results in the current user's name.
String.prototype.readMacroParams = function()
{
	var p = this.parseParams("list",null,true,true);
	var n = [];
	for(var t=1; t<p.length; t++)
		n.push(p[t].value);
	return n;
}

// Process a string list of unique tiddler names into an array. Tiddler names that have spaces in them must be [[bracketed]]
String.prototype.readBracketedList = function(unique)
{
	var p = this.parseParams("list",null,false,true);
	var n = [];
	for(var t=1; t<p.length; t++)
		n.pushUnique(p[t].value,unique);
	return n;
}

// Returns array with start and end index of chunk between given start and end marker, or undefined.
String.prototype.getChunkRange = function(start,end) 
{
	var s = this.indexOf(start);
	if(s != -1)
		{
		s += start.length;
		var e = this.indexOf(end,s);
		if(e != -1)
			return [s, e];
		}
}

// Replace a chunk of a string given start and end markers
String.prototype.replaceChunk = function(start,end,sub)
{
	var r = this.getChunkRange(start,end);
	return r 
		? this.substring(0,r[0]) + sub + this.substring(r[1])
		: this;
}

// Returns a chunk of a string between start and end markers, or undefined
String.prototype.getChunk = function(start,end)
{
	var r = this.getChunkRange(start,end);
	if (r)
		return this.substring(r[0],r[1]);
}


// Static method to bracket a string with double square brackets if it contains a space
String.encodeTiddlyLink = function(title)
{
	if(title.indexOf(" ") == -1)
		return(title);
	else
		return("[[" + title + "]]");
}

// Static method to encodeTiddlyLink for every item in an array and join them with spaces
String.encodeTiddlyLinkList = function(list)
{
	if(list)
		{
		var results = [];
		for(var t=0; t<list.length; t++)
			results.push(String.encodeTiddlyLink(list[t]));
		return results.join(" ");
		}
	else
		return "";
}

// Static method to left-pad a string with 0s to a certain width
String.zeroPad = function(n,d)
{
	var s = n.toString();
	if(s.length < d)
		s = "000000000000000000000000000".substr(0,d-s.length) + s;
	return(s);
}

String.prototype.startsWith = function(prefix) 
{
	return !prefix || this.substring(0,prefix.length) == prefix;
}

// Returns the first value of the given named parameter.
//#
//# @param params
//#         as returned by parseParams or null/undefined
//# @return [may be null/undefined]
//#
function getParam(params, name, defaultValue) {
	if (!params)
		return defaultValue;
	var p = params[0][name];
	return p ? p[0] : defaultValue;
}

// Returns the first value of the given boolean named parameter.
//#
//# @param params
//#         as returned by parseParams or null/undefined
//#
function getFlag(params, name, defaultValue) {
	return !!getParam(params, name, defaultValue);
} 
	
// Substitute date components into a string
Date.prototype.formatString = function(template)
{
	var t = template.replace(/0hh12/g,String.zeroPad(this.getHours12(),2));
	t = t.replace(/hh12/g,this.getHours12());
	t = t.replace(/0hh/g,String.zeroPad(this.getHours(),2));
	t = t.replace(/hh/g,this.getHours());
	t = t.replace(/0mm/g,String.zeroPad(this.getMinutes(),2));
	t = t.replace(/mm/g,this.getMinutes());
	t = t.replace(/0ss/g,String.zeroPad(this.getSeconds(),2));
	t = t.replace(/ss/g,this.getSeconds());
	t = t.replace(/[ap]m/g,this.getAmPm().toLowerCase());
	t = t.replace(/[AP]M/g,this.getAmPm().toUpperCase());
	t = t.replace(/wYYYY/g,this.getYearForWeekNo());
	t = t.replace(/wYY/g,String.zeroPad(this.getYearForWeekNo()-2000,2));
	t = t.replace(/YYYY/g,this.getFullYear());
	t = t.replace(/YY/g,String.zeroPad(this.getFullYear()-2000,2));
	t = t.replace(/MMM/g,config.messages.dates.months[this.getMonth()]);
	t = t.replace(/mmm/g,config.messages.dates.shortMonths[this.getMonth()]);
	t = t.replace(/0MM/g,String.zeroPad(this.getMonth()+1,2));
	t = t.replace(/MM/g,this.getMonth()+1);
	t = t.replace(/0WW/g,String.zeroPad(this.getWeek(),2));
	t = t.replace(/WW/g,this.getWeek());
	t = t.replace(/DDD/g,config.messages.dates.days[this.getDay()]);
	t = t.replace(/ddd/g,config.messages.dates.shortDays[this.getDay()]);
	t = t.replace(/0DD/g,String.zeroPad(this.getDate(),2));
	t = t.replace(/DDth/g,this.getDate()+this.daySuffix());
	t = t.replace(/DD/g,this.getDate());
	return t;
}

Date.prototype.getWeek = function()
{
	var dt = new Date(this.getTime());
	var d = dt.getDay();
	if (d==0) d=7;// JavaScript Sun=0, ISO Sun=7
	dt.setTime(dt.getTime()+(4-d)*86400000);// shift day to Thurs of same week to calculate weekNo
	var n = Math.floor((dt.getTime()-new Date(dt.getFullYear(),0,1)+3600000)/86400000); 
	return Math.floor(n/7)+1;
}

Date.prototype.getYearForWeekNo = function()
{
	var dt = new Date(this.getTime());
	var d = dt.getDay();
	if (d==0) d=7;// JavaScript Sun=0, ISO Sun=7
	dt.setTime(dt.getTime()+(4-d)*86400000);// shift day to Thurs of same week
	return dt.getFullYear();
}

Date.prototype.getHours12 = function()
{
	var h = this.getHours();
	return h > 12 ? h-12 : ( h > 0 ? h : 12 );
}

Date.prototype.getAmPm = function()
{
	return this.getHours() >= 12 ? "pm" : "am";
}

Date.prototype.daySuffix = function()
{
	var num = this.getDate();
	if (num >= 11 && num <= 13) return "th";
	else if (num.toString().substr(-1)=="1") return "st";
	else if (num.toString().substr(-1)=="2") return "nd";
	else if (num.toString().substr(-1)=="3") return "rd";
	return "th";
}

// Convert a date to local YYYYMMDDHHMM string format
Date.prototype.convertToLocalYYYYMMDDHHMM = function()
{
	return(String.zeroPad(this.getFullYear(),4) + String.zeroPad(this.getMonth()+1,2) + String.zeroPad(this.getDate(),2) + String.zeroPad(this.getHours(),2) + String.zeroPad(this.getMinutes(),2));
}

// Convert a date to UTC YYYYMMDDHHMM string format
Date.prototype.convertToYYYYMMDDHHMM = function()
{
	return(String.zeroPad(this.getUTCFullYear(),4) + String.zeroPad(this.getUTCMonth()+1,2) + String.zeroPad(this.getUTCDate(),2) + String.zeroPad(this.getUTCHours(),2) + String.zeroPad(this.getUTCMinutes(),2));
}

// Convert a date to UTC YYYYMMDD.HHMMSSMMM string format
Date.prototype.convertToYYYYMMDDHHMMSSMMM = function()
{
	return(String.zeroPad(this.getUTCFullYear(),4) + String.zeroPad(this.getUTCMonth()+1,2) + String.zeroPad(this.getUTCDate(),2) + "." + String.zeroPad(this.getUTCHours(),2) + String.zeroPad(this.getUTCMinutes(),2) + String.zeroPad(this.getUTCSeconds(),2) + String.zeroPad(this.getUTCMilliseconds(),4));
}

// Static method to create a date from a UTC YYYYMMDDHHMM format string
Date.convertFromYYYYMMDDHHMM = function(d)
{
	var theDate = new Date(Date.UTC(parseInt(d.substr(0,4),10),
							parseInt(d.substr(4,2),10)-1,
							parseInt(d.substr(6,2),10),
							parseInt(d.substr(8,2),10),
							parseInt(d.substr(10,2),10),0,0));
	return(theDate);
}

// ---------------------------------------------------------------------------------
// Crypto functions and associated conversion routines
// ---------------------------------------------------------------------------------

// Crypto "namespace"
function Crypto() {}

// Convert a string to an array of big-endian 32-bit words
Crypto.strToBe32s = function(str)
{
	var be = Array();
	var len = Math.floor(str.length/4);
	var i, j;
	for(i=0, j=0; i<len; i++, j+=4)
		{
		be[i] = ((str.charCodeAt(j)&0xff) << 24)|((str.charCodeAt(j+1)&0xff) << 16)|((str.charCodeAt(j+2)&0xff) << 8)|(str.charCodeAt(j+3)&0xff);
		}
	while (j<str.length)
		{
		be[j>>2] |= (str.charCodeAt(j)&0xff)<<(24-(j*8)%32);
		j++;
		}
	return be;
}

// Convert an array of big-endian 32-bit words to a string
Crypto.be32sToStr = function(be)
{
	var str = "";
	for(var i=0;i<be.length*32;i+=8)
		str += String.fromCharCode((be[i>>5]>>>(24-i%32)) & 0xff);
	return str;
}

// Convert an array of big-endian 32-bit words to a hex string
Crypto.be32sToHex = function(be)
{
	var hex = "0123456789ABCDEF";
	var str = "";
	for(var i=0;i<be.length*4;i++)
		str += hex.charAt((be[i>>2]>>((3-i%4)*8+4))&0xF) + hex.charAt((be[i>>2]>>((3-i%4)*8))&0xF);
	return str;
}

// Return, in hex, the SHA-1 hash of a string
Crypto.hexSha1Str = function(str)
{
	return Crypto.be32sToHex(Crypto.sha1Str(str));
}

// Return the SHA-1 hash of a string
Crypto.sha1Str = function(str)
{
	return Crypto.sha1(Crypto.strToBe32s(str),str.length);
}

// Calculate the SHA-1 hash of an array of blen bytes of big-endian 32-bit words
Crypto.sha1 = function(x,blen)
{
	// Add 32-bit integers, wrapping at 32 bits
	//# Uses 16-bit operations internally to work around bugs in some JavaScript interpreters.
	add32 = function(a,b)
	{
		var lsw = (a&0xFFFF)+(b&0xFFFF);
		var msw = (a>>16)+(b>>16)+(lsw>>16);
		return (msw<<16)|(lsw&0xFFFF);
	};
	// Add five 32-bit integers, wrapping at 32 bits
	//# Uses 16-bit operations internally to work around bugs in some JavaScript interpreters.
	add32x5 = function(a,b,c,d,e)
	{
		var lsw = (a&0xFFFF)+(b&0xFFFF)+(c&0xFFFF)+(d&0xFFFF)+(e&0xFFFF);
		var msw = (a>>16)+(b>>16)+(c>>16)+(d>>16)+(e>>16)+(lsw>>16);
		return (msw<<16)|(lsw&0xFFFF);
	};
	// Bitwise rotate left a 32-bit integer by 1 bit
	rol32 = function(n)
	{
		return (n>>>31)|(n<<1);
	};

	var len = blen*8;
	// Append padding so length in bits is 448 mod 512
	x[len>>5] |= 0x80 << (24-len%32);
	// Append length
	x[((len+64>>9)<<4)+15] = len;
	var w = Array(80);

	var k1 = 0x5A827999;
	var k2 = 0x6ED9EBA1;
	var k3 = 0x8F1BBCDC;
	var k4 = 0xCA62C1D6;

	var h0 = 0x67452301;
	var h1 = 0xEFCDAB89;
	var h2 = 0x98BADCFE;
	var h3 = 0x10325476;
	var h4 = 0xC3D2E1F0;

	for(var i=0;i<x.length;i+=16)
		{
		var j,t;
		var a = h0;
		var b = h1;
		var c = h2;
		var d = h3;
		var e = h4;
		for(j = 0;j<16;j++)
			{
			w[j] = x[i+j];
			t = add32x5(e,(a>>>27)|(a<<5),d^(b&(c^d)),w[j],k1);
			e=d; d=c; c=(b>>>2)|(b<<30); b=a; a = t;
			}
		for(j=16;j<20;j++)
			{
			w[j] = rol32(w[j-3]^w[j-8]^w[j-14]^w[j-16]);
			t = add32x5(e,(a>>>27)|(a<<5),d^(b&(c^d)),w[j],k1);
			e=d; d=c; c=(b>>>2)|(b<<30); b=a; a = t;
			}
		for(j=20;j<40;j++)
			{
			w[j] = rol32(w[j-3]^w[j-8]^w[j-14]^w[j-16]);
			t = add32x5(e,(a>>>27)|(a<<5),b^c^d,w[j],k2);
			e=d; d=c; c=(b>>>2)|(b<<30); b=a; a = t;
			}
		for(j=40;j<60;j++)
			{
			w[j] = rol32(w[j-3]^w[j-8]^w[j-14]^w[j-16]);
			t = add32x5(e,(a>>>27)|(a<<5),(b&c)|(d&(b|c)),w[j],k3);
			e=d; d=c; c=(b>>>2)|(b<<30); b=a; a = t;
			}
		for(j=60;j<80;j++)
			{
			w[j] = rol32(w[j-3]^w[j-8]^w[j-14]^w[j-16]);
			t = add32x5(e,(a>>>27)|(a<<5),b^c^d,w[j],k4);
			e=d; d=c; c=(b>>>2)|(b<<30); b=a; a = t;
			}

		h0 = add32(h0,a);
		h1 = add32(h1,b);
		h2 = add32(h2,c);
		h3 = add32(h3,d);
		h4 = add32(h4,e);
		}
	return Array(h0,h1,h2,h3,h4);
}

// ---------------------------------------------------------------------------------
// RGB colour object
// ---------------------------------------------------------------------------------

// Construct an RGB colour object from a '#rrggbb', '#rgb' or 'rgb(n,n,n)' string or from separate r,g,b values
function RGB(r,g,b)
{
	this.r = 0;
	this.g = 0;
	this.b = 0;
	if(typeof r == "string")
		{
		if(r.substr(0,1) == "#")
			{
			if(r.length == 7)
				{
				this.r = parseInt(r.substr(1,2),16)/255;
				this.g = parseInt(r.substr(3,2),16)/255;
				this.b = parseInt(r.substr(5,2),16)/255;
				}
			else
				{
				this.r = parseInt(r.substr(1,1),16)/15;
				this.g = parseInt(r.substr(2,1),16)/15;
				this.b = parseInt(r.substr(3,1),16)/15;
				}
			}
		else
			{
			var rgbPattern = /rgb\s*\(\s*(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*(\d{1,3})\s*\)/ ;
			var c = r.match(rgbPattern);
			if (c)
				{
				this.r = parseInt(c[1],10)/255;
				this.g = parseInt(c[2],10)/255;
				this.b = parseInt(c[3],10)/255;
				}
			}
		}
	else
		{
		this.r = r;
		this.g = g;
		this.b = b;
		}
	return this;
}

// Mixes this colour with another in a specified proportion
// c = other colour to mix
// f = 0..1 where 0 is this colour and 1 is the new colour
// Returns an RGB object
RGB.prototype.mix = function(c,f)
{
	return new RGB(this.r + (c.r-this.r) * f,this.g + (c.g-this.g) * f,this.b + (c.b-this.b) * f);
}

// Return an rgb colour as a #rrggbb format hex string
RGB.prototype.toString = function()
{
	var r = this.r.clamp(0,1);
	var g = this.g.clamp(0,1);
	var b = this.b.clamp(0,1);
	return("#" + ("0" + Math.floor(r * 255).toString(16)).right(2) +
				 ("0" + Math.floor(g * 255).toString(16)).right(2) +
				 ("0" + Math.floor(b * 255).toString(16)).right(2));
}

// ---------------------------------------------------------------------------------
// DOM utilities - many derived from www.quirksmode.org
// ---------------------------------------------------------------------------------

function drawGradient(place,horiz,colours)
{
	for(var t=0; t<= 100; t+=2)
		{
		var bar = document.createElement("div");
		place.appendChild(bar);
		bar.style.position = "absolute";
		bar.style.left = horiz ? t + "%" : 0;
		bar.style.top = horiz ? 0 : t + "%";
		bar.style.width = horiz ? (101-t) + "%" : "100%";
		bar.style.height = horiz ? "100%" : (101-t) + "%";
		bar.style.zIndex = -1;
		var f = t/100;
		var p = f*(colours.length-1);
		bar.style.backgroundColor = colours[Math.floor(p)].mix(colours[Math.ceil(p)],p-Math.floor(p)).toString();
		}
}

function createTiddlyText(theParent,theText)
{
	return theParent.appendChild(document.createTextNode(theText));
}

function createTiddlyCheckbox(theParent,caption,checked,onChange)
{
	var cb = document.createElement("input");
	cb.setAttribute("type","checkbox");
	cb.onclick = onChange;
	theParent.appendChild(cb);
	cb.checked = checked;
	cb.className = "chkOptionInput";
	if(caption)
		wikify(caption,theParent);
	return cb;
}

function createTiddlyElement(theParent,theElement,theID,theClass,theText)
{
	var e = document.createElement(theElement);
	if(theClass != null)
		e.className = theClass;
	if(theID != null)
		e.setAttribute("id",theID);
	if(theText != null)
		e.appendChild(document.createTextNode(theText));
	if(theParent != null)
		theParent.appendChild(e);
	return(e);
}

// Add an event handler
// Thanks to John Resig, via QuirksMode
function addEvent(obj,type,fn)
{
	if(obj.attachEvent)
		{
		obj['e'+type+fn] = fn;
		obj[type+fn] = function(){obj['e'+type+fn](window.event);}
		obj.attachEvent('on'+type,obj[type+fn]);
		}
	else
		obj.addEventListener(type,fn,false);
}

// Remove  an event handler
// Thanks to John Resig, via QuirksMode
function removeEvent(obj,type,fn)
{
	if(obj.detachEvent)
		{
		obj.detachEvent('on'+type,obj[type+fn]);
		obj[type+fn] = null;
		}
	else
		obj.removeEventListener(type,fn,false);
}

function addClass(e,theClass)
{
	var currClass = e.className.split(" ");
	if(currClass.indexOf(theClass) == -1)
		e.className += " " + theClass;
}

function removeClass(e,theClass)
{
	var currClass = e.className.split(" ");
	var i = currClass.indexOf(theClass);
	while(i != -1)
		{
		currClass.splice(i,1);
		i = currClass.indexOf(theClass);
		}
	e.className = currClass.join(" ");
}

function hasClass(e,theClass)
{
	if(e.className)
		{
		if(e.className.split(" ").indexOf(theClass) != -1)
			return true;
		}
	return false;
}

// Find the closest relative with a given property value (property defaults to tagName, relative defaults to parentNode)
function findRelated(e,value,name,relative)
{
	name = name ? name : "tagName";
	relative = relative ? relative : "parentNode";
	if(name == "className")
		{
		while(e && !hasClass(e,value))
			{
			e = e[relative];
			}
		}
	else
		{
		while(e && e[name] != value)
			{
			e = e[relative];
			}
		}
	return e;
}

// Resolve the target object of an event
function resolveTarget(e)
{
	var obj;
	if (e.target)
		obj = e.target;
	else if (e.srcElement)
		obj = e.srcElement;
	if (obj.nodeType == 3) // defeat Safari bug
		obj = obj.parentNode;
	return(obj);
}

// Return the content of an element as plain text with no formatting
function getPlainText(e)
{
	var text = "";
	if(e.innerText)
		text = e.innerText;
	else if(e.textContent)
		text = e.textContent;
	return text;
}

// Get the scroll position for window.scrollTo necessary to scroll a given element into view
function ensureVisible(e)
{
	var posTop = findPosY(e);
	var posBot = posTop + e.offsetHeight;
	var winTop = findScrollY();
	var winHeight = findWindowHeight();
	var winBot = winTop + winHeight;
	if(posTop < winTop)
		return(posTop);
	else if(posBot > winBot)
		{
		if(e.offsetHeight < winHeight)
			return(posTop - (winHeight - e.offsetHeight));
		else
			return(posTop);
		}
	else
		return(winTop);
}

// Get the current width of the display window
function findWindowWidth()
{
	return(window.innerWidth ? window.innerWidth : document.documentElement.clientWidth);
}

// Get the current height of the display window
function findWindowHeight()
{
	return(window.innerHeight ? window.innerHeight : document.documentElement.clientHeight);
}

// Get the current horizontal page scroll position
function findScrollX()
{
	return(window.scrollX ? window.scrollX : document.documentElement.scrollLeft);
}

// Get the current vertical page scroll position
function findScrollY()
{
	return(window.scrollY ? window.scrollY : document.documentElement.scrollTop);
}

function findPosX(obj)
{
	var curleft = 0;
	while (obj.offsetParent)
		{
		curleft += obj.offsetLeft;
		obj = obj.offsetParent;
		}
	return curleft;
}

function findPosY(obj)
{
	var curtop = 0;
	while (obj.offsetParent)
		{
		curtop += obj.offsetTop;
		obj = obj.offsetParent;
		}
	return curtop;
}

// Blur a particular element
function blurElement(e)
{
	if(e != null && e.focus && e.blur)
		{
		e.focus();
		e.blur();
		}
}

// Create a non-breaking space
function insertSpacer(place)
{
	var e = document.createTextNode(String.fromCharCode(160));
	if(place)
		place.appendChild(e);
	return e;
}

// Remove all children of a node
function removeChildren(e)
{
	while(e.hasChildNodes())
		e.removeChild(e.firstChild);
}

// Add a stylesheet, replacing any previous custom stylesheet
function setStylesheet(s,id)
{
	if(!id)
		id = "customStyleSheet";
	var n = document.getElementById(id);
	if(document.createStyleSheet) // Test for IE's non-standard createStyleSheet method
		{
		if(n)
			n.parentNode.removeChild(n);
		// This failed without the &nbsp;
		document.getElementsByTagName("head")[0].insertAdjacentHTML("beforeEnd","&nbsp;<style id='" + id + "'>" + s + "</style>");
		}
	else
		{
		if(n)
			n.replaceChild(document.createTextNode(s),n.firstChild);
		else
			{
			var n = document.createElement("style");
			n.type = "text/css";
			n.id = id;
			n.appendChild(document.createTextNode(s));
			document.getElementsByTagName("head")[0].appendChild(n);
			}
		}
}

// Replace the current selection of a textarea or text input and scroll it into view

function replaceSelection(e,text)
{
	if (e.setSelectionRange)
		{
		var oldpos = e.selectionStart + 1;
		e.value = e.value.substr(0,e.selectionStart) + text + e.value.substr(e.selectionStart);
		e.setSelectionRange( oldpos, oldpos);
		var linecount = e.value.split('\n').length;
		var thisline = e.value.substr(0,e.selectionStart).split('\n').length-1;
		e.scrollTop = Math.floor((thisline-e.rows/2)*e.scrollHeight/linecount);
		}
	else if (document.selection)
		{
		var range = document.selection.createRange();
		if (range.parentElement() == e)
			{
			var isCollapsed = range.text == "";
			range.text = text;
			 if (!isCollapsed)
				{
				range.moveStart('character', -text.length);
				range.select();
				}
			}
		}
}

// Returns the text of the given (text) node, possibly merging subsequent text nodes
function getNodeText(e)
{
	var t = ""; 
	while (e && e.nodeName == "#text")
		{
		t += e.nodeValue;
		e = e.nextSibling;
		}
	return t;
}
//# -------------------------
//# LoaderBase: A (abstract) storage loader that loads the tiddlers from a list of HTML elements.
//# The format of the elements is defined by subclasses of this loader through the internalizeTiddler implementation.
//# Subclasses must implement:
//# 			function getTitle(store, e)
//#
//# store must implement:
//# 			function createTiddler(title).
//#

function LoaderBase()
{
}

LoaderBase.prototype.loadTiddler = function(store,e,tiddlers)
{
	var title = this.getTitle(store, e);
	if (title)
		{
		var tiddler = store.createTiddler(title);
		this.internalizeTiddler(store, tiddler, title, e);
		tiddlers.push(tiddler);
		}
}

LoaderBase.prototype.loadTiddlers = function(store,nodes)
{
	var tiddlers = [];
	for (var t = 0; t < nodes.length; t++)
		{
		try
			{
			this.loadTiddler(store, nodes[t], tiddlers);
			}
		catch(e)
			{
			showException(e, config.messages.tiddlerLoadError.format([this.getTitle(store, nodes[t])]));
			}
		}
	return tiddlers;
}
	
//# -------------------------
//# SaverBase: a (abstract) storage saver that externalizes all tiddlers into a string, 
//# with every tiddler individually externalized (using this.externalizeTiddler) and joined with newlines 
//# Subclasses must implement:
//# 			function externalizeTiddler(store, tiddler)
//#
//# store must implement:
//# 			function getTiddlers(sortByFieldName)
//#

function SaverBase()
{
}

SaverBase.prototype.externalize = function(store) 
{
	var results = [];
	var tiddlers = store.getTiddlers("title");
	for (var t = 0; t < tiddlers.length; t++)
		results.push(this.externalizeTiddler(store, tiddlers[t]));
	return results.join("\n");
}
//--------------------------------
// TW21Loader (inherits from LoaderBase)

function TW21Loader() {};

TW21Loader.prototype = new LoaderBase();

TW21Loader.prototype.getTitle = function(store, e) {
	var title = null;
	if(e.getAttribute)
		title = e.getAttribute("tiddler");
	if(!title && e.id) {	
		var lenPrefix = store.idPrefix.length;
		if (e.id.substr(0,lenPrefix) == store.idPrefix)
			title = e.id.substr(lenPrefix);
	}
	return title;
}

TW21Loader.prototype.internalizeTiddler = function(store, tiddler, title, data) {
	var text = getNodeText(data.firstChild).unescapeLineBreaks();
	var modifier = data.getAttribute("modifier");
	var modified = Date.convertFromYYYYMMDDHHMM(data.getAttribute("modified"));
	var c = data.getAttribute("created");
	var created = c ? Date.convertFromYYYYMMDDHHMM(c) : modified;
	var tags = data.getAttribute("tags");
	var fields = {};
	var attrs = data.attributes;
	for(var i = attrs.length-1; i >= 0; i--) {
		var name = attrs[i].name;
		if (attrs[i].specified && !TiddlyWiki.isStandardField(name)) {
			fields[name] = attrs[i].value.unescapeLineBreaks();
		}
	}
	tiddler.assign(title,text,modifier,modified,tags,created, fields);
	return tiddler;
};

//--------------------------------
// TW21Saver (inherits from SaverBase)

function TW21Saver() {};

TW21Saver.prototype = new SaverBase();

TW21Saver.prototype.externalizeTiddler = function(store, tiddler) 
{
	try {
		var extendedFieldAttributes = "";
		store.forEachField(tiddler, 
			function(tiddler, fieldName, value) {
				// don't store stuff from the temp namespace
				if (!fieldName.match(/^temp\./))
					extendedFieldAttributes += ' %0="%1"'.format([fieldName, value.escapeLineBreaks().htmlEncode()]);
			}, true);
		return '<div tiddler="%0" modifier="%1" modified="%2" created="%3" tags="%4"%6>%5</div>'.format([
				tiddler.title.htmlEncode(),
				tiddler.modifier.htmlEncode(),
				tiddler.modified.convertToYYYYMMDDHHMM(),
				tiddler.created.convertToYYYYMMDDHHMM(),
				tiddler.getTags().htmlEncode(),
				tiddler.escapeLineBreaks().htmlEncode(),
				extendedFieldAttributes
			]);
	} catch (e) {
		throw exceptionText(e, config.messages.tiddlerSaveError.format([tiddler.title]));
	}
}

// ---------------------------------------------------------------------------------
// Deprecated code
// ---------------------------------------------------------------------------------

// @Deprecated: Use createElementAndWikify and this.termRegExp instead
config.formatterHelpers.charFormatHelper = function(w)
{
	w.subWikify(createTiddlyElement(w.output,this.element),this.terminator);
}

// @Deprecated: Use enclosedTextHelper and this.lookaheadRegExp instead
config.formatterHelpers.monospacedByLineHelper = function(w)
{
	var lookaheadRegExp = new RegExp(this.lookahead,"mg");
	lookaheadRegExp.lastIndex = w.matchStart;
	var lookaheadMatch = lookaheadRegExp.exec(w.source);
	if(lookaheadMatch && lookaheadMatch.index == w.matchStart)
		{
		var text = lookaheadMatch[1];
		if(config.browser.isIE)
			text = text.replace(/\n/g,"\r");
		createTiddlyElement(w.output,"pre",null,null,text);
		w.nextMatch = lookaheadRegExp.lastIndex;
		}
}

// @Deprecated: Use <br> or <br /> instead of <<br>>
config.macros.br.handler = function(place)
{
	createTiddlyElement(place,"br");
}

// Find an entry in an array. Returns the array index or null
// @Deprecated: Use indexOf instead
Array.prototype.find = function(item)
{
	var i = this.indexOf(item);
	return i == -1 ? null : i;
}

// Load a tiddler from an HTML DIV. The caller should make sure to later call Tiddler.changed()
// @Deprecated: Use store.getLoader().internalizeTiddler instead
Tiddler.prototype.loadFromDiv = function(divRef,title)
{
	return store.getLoader().internalizeTiddler(store,this,title,divRef);
}

// Format the text for storage in an HTML DIV
// @Deprecated Use store.getSaver().externalizeTiddler instead.
Tiddler.prototype.saveToDiv = function()
{
	return store.getSaver().externalizeTiddler(store,this);
}

// @Deprecated: Use store.allTiddlersAsHtml() instead
function allTiddlersAsHtml()
{
	return store.allTiddlersAsHtml();
}

// @Deprecated: Use refreshPageTemplate instead
function applyPageTemplate(title)
{
	refreshPageTemplate(title);
}

// @Deprecated: Use story.displayTiddlers instead
function displayTiddlers(srcElement,titles,template,unused1,unused2,animate,slowly)
{
	story.displayTiddlers(srcElement,titles,template,animate,slowly);
}

// @Deprecated: Use story.displayTiddler instead
function displayTiddler(srcElement,title,template,unused1,unused2,animate,slowly)
{
	story.displayTiddler(srcElement,title,template,animate,slowly);
}

// @Deprecated: Use functions on right hand side directly instead
var createTiddlerPopup = Popup.create;
var scrollToTiddlerPopup = Popup.show;
var hideTiddlerPopup = Popup.remove;

// @Deprecated: Use right hand side directly instead
var regexpBackSlashEn = new RegExp("\\\\n","mg");
var regexpBackSlash = new RegExp("\\\\","mg");
var regexpBackSlashEss = new RegExp("\\\\s","mg");
var regexpNewLine = new RegExp("\n","mg");
var regexpCarriageReturn = new RegExp("\r","mg");
// ---------------------------------------------------------------------------------
// End of scripts
// ---------------------------------------------------------------------------------
//]]>
</script>
<style type="text/css">

#saveTest {
	display: none;
}

.zoomer {
	display: none;
}

#messageArea {
	display: none;
}

#copyright {
	display: none;
}

.popup {
	position: absolute;
}

#storeArea {
	display: none;
	margin: 4em 10em 3em;
}

#storeArea div {
 padding: 0.5em;
 margin: 1em 0em 0em 0em;
 border-color: #f0f0f0 #606060 #404040 #d0d0d0; 
 border-style: solid; 
 border-width: 2px;
 overflow: auto;
}

#javascriptWarning {
	width: 100%;
	text-align: center;
	font-weight: bold;
	background-color: #dd1100;
	color: #fff;
	padding:1em 0em; 
}

</style>
<!--POST-HEAD-START-->
<!--POST-HEAD-END-->
</head>
<body onload="main();" onunload="if(window.checkUnsavedChanges) checkUnsavedChanges();">
<!--PRE-BODY-START-->
<!--PRE-BODY-END-->
	<script type="text/javascript">
//<![CDATA[
if (useJavaSaver)
	document.write("<applet style='position:absolute;left:-1px' name='TiddlySaver' code='TiddlySaver.class' archive='TiddlySaver.jar' width='1' height='1'></applet>");
//]]>
	</script>
	<div id="copyright">
	Welcome to TiddlyWiki by Jeremy Ruston, Copyright &copy; 2006 Osmosoft Limited
	</div>
	<noscript>
		<div id="javascriptWarning">This page requires JavaScript to function properly</div>
	</noscript>
	<div id="saveTest"></div>
	<div id="contentWrapper"></div>
	<div id="contentStash"></div>
	<div id="storeArea">
<div tiddler="LegacyStrikeThroughPlugin" modifier="MartinBudden" modified="200607210000" created="200609152742" tags="systemConfig">/***\n|''Name:''|LegacyStrikeThroughPlugin|\n|''Description:''|Support for  legacy (pre 2.1) strike through formatting|\n|''Version:''|1.0.1|\n|''Date:''|Jul 21, 2006|\n|''Source:''|http://www.tiddlywiki.com/#LegacyStrikeThroughPlugin|\n|''Author:''|MartinBudden (mjbudden (at) gmail (dot) com)|\n|''License:''|[[BSD open source license]]|\n|''CoreVersion:''|2.1.0|\n|''Browser:''|Firefox 1.0.4+; Firefox 1.5; InternetExplorer 6.0|\n\n***/\n\n//{{{\n\n// Ensure that the LegacyStrikeThrough Plugin is only installed once.\nif(!version.extensions.LegacyStrikeThroughPlugin)\n	{\n	version.extensions.LegacyStrikeThroughPlugin = true;\n\nconfig.formatters.push(\n{\n	name: &quot;legacyStrikeByChar&quot;,\n	match: &quot;==&quot;,\n	termRegExp: /(==)/mg,\n	element: &quot;strike&quot;,\n	handler: config.formatterHelpers.createElementAndWikify\n});\n\n} // end of &quot;install only once&quot;\n//}}}\n</div>
<?cs each:tiddler = combinewiki.tiddlers ?><div tiddler="<?cs var:tiddler.name ?>" modifier="<?cs var:tiddler.author ?>" modified="<?cs var:tiddler.modtime ?>" created="<?cs var:tiddler.ctime ?>" tag=""><?cs var:tiddler.content ?></div>
<?cs /each ?>
</div>
<!--POST-BODY-START-->
<!--POST-BODY-END-->
	</body>
</html>
