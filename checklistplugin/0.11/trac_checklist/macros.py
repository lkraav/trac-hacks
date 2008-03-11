#
#   macros.py -- Guts that support the wiki-zation of checklists.
#

from genshi.builder import tag

from trac.wiki.macros import WikiMacroBase
from trac.wiki.formatter import Formatter
from trac.util.html import Markup
from trac.core import ExtensionPoint

from db import IChecklistDBObserver

import re, StringIO

checklistRE = re.compile('\[cl:(.*?)\{(.*?)\}\]', re.M | re.S)

class ChecklistMacro(WikiMacroBase):
    clobservers = ExtensionPoint(IChecklistDBObserver)

    def expand_macro(self, formatter, name, args):
        lines = iter(args.split('\n'))
        flags = {}
        for line in lines:
            line = line.strip()
            if line[:1] == '#':
                continue
            elif line[:1] == '-':
                name, value = (line[1:].split('=', 1) + [True])[:2]
                flags[name.strip()] = \
                    isinstance(value, basestring) and value.strip() or value
            else:
                break
        text = '\n'.join(lines)
        context = flags.get('context', formatter.req.path_info)
        section = flags.get('section')
        if section:
            context += '::' + section
        data = self.fetchContext(context)
        notes = dict(
            name=(section or 'Checklist')
            )

        def replacer(match):
            op, field = match.groups()
            fn = getattr(self, 'op_' + (op or 'checkbox'), None)
            if fn is not None:
                return fn(field, data, notes)
            else:
                return 'ERROR: No function for operation %r' % op

        # Replace cl fields.
        html = ''.join(checklistRE.sub(replacer, self.wikize(formatter, text)))

        action = formatter.req.href('checklist/update')

        return ''.join((
            '<FORM method="POST" action=%r' % action,
                '>',
            '<INPUT type="hidden" name="__context__" value=%r>' % context
            html,
            not notes.get('submit') and self.op_submit(None, data, notes) or '',
            '</FORM>',
            ))

    def wikize(self, formatter, text):
        out = StringIO.StringIO()
        Formatter(formatter.env, formatter.context).format(text, out)
        return out.getvalue()

    def fetchContext(self, context):
        for observer in self.clobservers:
            result = observer.checklist_getValues(context)
            if result is not None:
                return result

    def op_checkbox(self, field, data, notes):
        checked = data.get(field, (False, None, None))[0]
        return ''.join((
            '<INPUT type="checkbox" name=%r' % str(field),
                checked and ' checked' or '',
                '>',
            ))

    def op_who(self, field, data, notes):
        return data.get(field, (False, None, '<noone>'))[2]

    def op_when(self, field, data, notes):
        return str(data.get(field, (False, '<unknown>', None))[1])[:19]

    def op_submit(self, field, data, notes):
        notes['submit'] = True
        field = str(field or 'Update ' + notes['name'])
        return ''.join((
            '<INPUT type="submit" value=%r>' % field
            ))

