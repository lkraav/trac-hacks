{   'headers': [   {'col': 'ticket', 'title': 'ticket'},
                   {'col': 'summary', 'title': 'Summary'},
                   {'col': 'status', 'title': 'Status'},
                   {'col': 'type', 'title': 'Type'},
                   {'col': 'priority', 'title': 'Priority'},
                   {'col': 'milestone', 'title': 'Milestone'},
                   {'col': 'component', 'title': 'Component'}],
    'message': <Markup u'<style type="text/css">\n.ticket-imported, .modified-ticket-imported { width: 40px; }\n.color-new-odd td, .color-new-even td, .modified-ticket-imported, .modified-summary, .modified-status, .modified-type, .modified-priority, .modified-milestone, .modified-component { font-style: italic; }\n</style>\n<p>\nScroll to see a preview of the tickets as they will be imported. If the data is correct, select the <strong>Execute Import</strong> button.\n</p>\n<ul><li>1 tickets will be imported (1 added, 0 modified, 0 unchanged).\n</li><li>A <strong>ticket</strong> column was not found: tickets will be reconciliated by summary. If an existing ticket with the same summary is found, values that are changing appear in italics in the preview below. If no ticket with same summary is found, the whole line appears in italics below, and a new ticket will be added.\n</li><li>Some Trac fields are not present in the import. They will default to:\n</li></ul><blockquote>\n<blockquote>\n<table class="wiki">\n<tr><td><strong>field</strong></td><td><strong>Default value</strong>\n</td></tr><tr><td>Description, Cc, Keywords, Version, Mycustomfield, Severity</td><td><i>(Empty value)</i>\n</td></tr><tr><td>Changetime</td><td><i>(now)</i>\n</td></tr><tr><td>Reporter</td><td>testuser\n</td></tr><tr><td>Time</td><td><i>(now)</i>\n</td></tr><tr><td>Owner</td><td>Computed from component\n</td></tr><tr><td>Resolution</td><td><i>(None)</i>\n</td></tr></table>\n</blockquote>\n</blockquote>\n<p>\n(You can change some of these default values in the Trac Admin module, if you are administrator; or you can add the corresponding column to your spreadsheet and re-upload it).\n</p>\n<ul><li>Some lookup values are not found and will be added to the possible list of values:\n</li></ul><blockquote>\n<blockquote>\n<table class="wiki">\n<tr><td><strong>field</strong></td><td><strong>New values</strong>\n</td></tr><tr><td>Component</td><td>Wiki\n</td></tr><tr><td>Type</td><td>Aufgabe\n</td></tr><tr><td>Milestone</td><td>Infothek-Pr\xc3\xa4si\n</td></tr></table>\n</blockquote>\n</blockquote>\n<br/>'>,
    'rows': [   {   'cells': [   {   'col': 'ticket',
                                     'style': '',
                                     'value': '(new)'},
                                 {   'col': 'summary',
                                     'style': 'summary',
                                     'value': u'Trac-Wiki beschreiben'},
                                 {   'col': 'status',
                                     'style': 'status',
                                     'value': u'assigned'},
                                 {   'col': 'type',
                                     'style': 'type',
                                     'value': u'Aufgabe'},
                                 {   'col': 'priority',
                                     'style': 'priority',
                                     'value': u'major'},
                                 {   'col': 'milestone',
                                     'style': 'milestone',
                                     'value': u'Infothek-Pr\xc3\xa4si'},
                                 {   'col': 'component',
                                     'style': 'component',
                                     'value': u'Wiki'}],
                    'style': 'color-new-even'}],
    'title': 'Preview Import'}
