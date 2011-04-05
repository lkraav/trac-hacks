{   'headers': [   {'col': 'ticket', 'title': 'ticket'},
                   {'col': 'Summary', 'title': 'Summary'},
                   {'col': 'MyDate', 'title': 'Mydate'},
                   {'col': 'MyDateTime', 'title': 'Mydatetime'}],
    'message': <Markup u'<style type="text/css">\n.ticket-imported, .modified-ticket-imported { width: 40px; }\n.color-new-odd td, .color-new-even td, .modified-ticket-imported, .modified-Summary, .modified-MyDate, .modified-MyDateTime { font-style: italic; }\n</style>\n<p>\nScroll to see a preview of the tickets as they will be imported. If the data is correct, select the <strong>Execute Import</strong> button.\n</p>\n<ul><li>2 tickets will be imported (2 added, 0 modified, 0 unchanged).\n</li><li>A <strong>ticket</strong> column was not found: tickets will be reconciliated by summary. If an existing ticket with the same summary is found, values that are changing appear in italics in the preview below. If no ticket with same summary is found, the whole line appears in italics below, and a new ticket will be added.\n</li><li>Some Trac fields are not present in the import. They will default to:\n</li></ul><blockquote>\n<blockquote>\n<table class="wiki">\n<tr><td><strong>field</strong></td><td><strong>Default value</strong>\n</td></tr><tr><td>Description, Cc, Milestone, Component, Version, Keywords, Severity</td><td><em>(Empty value)</em>\n</td></tr><tr><td>Status</td><td>new\n</td></tr><tr><td>Changetime</td><td><em>(now)</em>\n</td></tr><tr><td>Reporter</td><td>testuser\n</td></tr><tr><td>Resolution</td><td><em>(None)</em>\n</td></tr><tr><td>Priority</td><td>major\n</td></tr><tr><td>Time</td><td><em>(now)</em>\n</td></tr><tr><td>Type</td><td>task\n</td></tr></table>\n</blockquote>\n</blockquote>\n<p>\n(You can change some of these default values in the Trac Admin module, if you are administrator; or you can add the corresponding column to your spreadsheet and re-upload it).\n</p>\n<br/>'>,
    'rows': [   {   'cells': [   {   'col': 'ticket',
                                     'style': '',
                                     'value': '(new)'},
                                 {   'col': 'Summary',
                                     'style': 'Summary',
                                     'value': u'summary1'},
                                 {   'col': 'MyDate',
                                     'style': 'MyDate',
                                     'value': '01/01/10 00:00:00'},
                                 {   'col': 'MyDateTime',
                                     'style': 'MyDateTime',
                                     'value': '01/01/10 06:45:00'}],
                    'style': 'color-new-even'},
                {   'cells': [   {   'col': 'ticket',
                                     'style': '',
                                     'value': '(new)'},
                                 {   'col': 'Summary',
                                     'style': 'Summary',
                                     'value': u'summary2'},
                                 {   'col': 'MyDate',
                                     'style': 'MyDate',
                                     'value': '12/23/65 00:00:00'},
                                 {   'col': 'MyDateTime',
                                     'style': 'MyDateTime',
                                     'value': '12/23/71 16:42:45'}],
                    'style': 'color-new-odd'}],
    'title': 'Preview Import'}
