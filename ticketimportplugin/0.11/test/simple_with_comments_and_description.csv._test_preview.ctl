{   'headers': [   {'col': 'ticket', 'title': 'ticket'},
                   {'col': 'summary', 'title': 'Summary'},
                   {'col': 'owner', 'title': 'Owner'},
                   {'col': 'priority', 'title': 'Priority'},
                   {'col': 'component', 'title': 'Component'},
                   {'col': 'description', 'title': 'Description'},
                   {'col': 'comment', 'title': 'Comment'}],
    'message': <Markup u'<style type="text/css">\n.ticket-imported, .modified-ticket-imported { width: 40px; }\n.color-new-odd td, .color-new-even td, .modified-ticket-imported, .modified-summary, .modified-owner, .modified-priority, .modified-component, .modified-description, .modified-comment { font-style: italic; }\n</style>\n<p>\nScroll to see a preview of the tickets as they will be imported. If the data is correct, select the <strong>Execute Import</strong> button.\n</p>\n<ul><li>3 tickets will be imported (1 added, 2 modified, 0 unchanged).\n</li><li>A <strong>ticket</strong> column was not found: tickets will be reconciliated by summary. If an existing ticket with the same summary is found, values that are changing appear in italics in the preview below. If no ticket with same summary is found, the whole line appears in italics below, and a new ticket will be added.\n</li><li>Some Trac fields are not present in the import. They will default to:\n</li></ul><blockquote>\n<blockquote>\n<table class="wiki">\n<tr><td><strong>field</strong></td><td><strong>Default value</strong>\n</td></tr><tr><td>Cc, Milestone, Url, Version, Mycustomfield, Keywords, Severity</td><td><i>(Empty value)</i>\n</td></tr><tr><td>Status</td><td>new\n</td></tr><tr><td>Changetime</td><td><i>(now)</i>\n</td></tr><tr><td>Reporter</td><td>testuser\n</td></tr><tr><td>Resolution</td><td><i>(None)</i>\n</td></tr><tr><td>Time</td><td><i>(now)</i>\n</td></tr><tr><td>Type</td><td>task\n</td></tr></table>\n</blockquote>\n</blockquote>\n<p>\n(You can change some of these default values in the Trac Admin module, if you are administrator; or you can add the corresponding column to your spreadsheet and re-upload it).\n</p>\n<ul><li>Some fields will not be imported because they don\'t exist in Trac: anyotherfield.\n</li><li>The field "comment" will be used as comment when modifying tickets, and appended to the description for new tickets.\n</li><li>Some lookup values are not found and will be added to the possible list of values:\n</li></ul><blockquote>\n<blockquote>\n<table class="wiki">\n<tr><td><strong>field</strong></td><td><strong>New values</strong>\n</td></tr><tr><td>Component</td><td>again again mycomp again\n</td></tr></table>\n</blockquote>\n</blockquote>\n<ul><li>Some user names do not exist in the system: me again modified. Make sure that they are valid users.\n</li></ul><br/>'>,
    'rows': [   {   'cells': [   {   'col': 'ticket',
                                     'style': '',
                                     'value': 1246},
                                 {   'col': 'summary',
                                     'style': 'summary',
                                     'value': u'sum1'},
                                 {   'col': 'owner',
                                     'style': 'modified-owner',
                                     'value': u'me again modified'},
                                 {   'col': 'priority',
                                     'style': 'priority',
                                     'value': u'mypriority'},
                                 {   'col': 'component',
                                     'style': 'modified-component',
                                     'value': u'again again mycomp again'},
                                 {   'col': 'description',
                                     'style': 'modified-description',
                                     'value': u'description1 modified'},
                                 {   'col': 'comment',
                                     'style': 'comment',
                                     'value': u'comment with some modified fields'}],
                    'style': ''},
                {   'cells': [   {   'col': 'ticket',
                                     'style': '',
                                     'value': 1245},
                                 {   'col': 'summary',
                                     'style': 'summary',
                                     'value': u'sum2'},
                                 {   'col': 'owner',
                                     'style': 'owner',
                                     'value': u'you'},
                                 {   'col': 'priority',
                                     'style': 'priority',
                                     'value': u'yourpriority'},
                                 {   'col': 'component',
                                     'style': 'component',
                                     'value': u'yourcomp'},
                                 {   'col': 'description',
                                     'style': 'modified-description',
                                     'value': u'description2'},
                                 {   'col': 'comment',
                                     'style': 'comment',
                                     'value': u'comment with no field modified'}],
                    'style': ''},
                {   'cells': [   {   'col': 'ticket',
                                     'style': '',
                                     'value': '(new)'},
                                 {   'col': 'summary',
                                     'style': 'summary',
                                     'value': u'newticket'},
                                 {   'col': 'owner',
                                     'style': 'owner',
                                     'value': u'you'},
                                 {   'col': 'priority',
                                     'style': 'priority',
                                     'value': u'yourpriority'},
                                 {   'col': 'component',
                                     'style': 'component',
                                     'value': u'yourcomp'},
                                 {   'col': 'description',
                                     'style': 'description',
                                     'value': u'new description'},
                                 {   'col': 'comment',
                                     'style': 'comment',
                                     'value': u'comment for a new ticket'}],
                    'style': 'color-new-even'}],
    'title': 'Preview Import'}
