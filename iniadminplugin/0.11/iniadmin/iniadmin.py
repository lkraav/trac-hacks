# -*- coding: utf-8 -*-
#
# Copyright (C) 2006-2008 Alec Thomas
# Copyright (C) 2010-2011 Ryan Ollos
# Copyright (C) 2012-2014 Jun Omae
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

from pkg_resources import parse_version, resource_filename
import inspect
import re

from trac import __version__ as VERSION
from trac.core import Component, implements, TracError
from trac.admin.api import IAdminPanelProvider
from trac.config import Option, ListOption
from trac.util.compat import set, sorted, any
from trac.util.text import to_unicode
from trac.web.chrome import Chrome, ITemplateProvider, add_stylesheet
try:
    from trac.util.translation import dgettext
except ImportError:
    dgettext = lambda domain, string: string


_parsed_version = parse_version(VERSION)

if _parsed_version >= parse_version('1.4'):
    _use_jinja2 = True
elif _parsed_version >= parse_version('1.3'):
    _use_jinja2 = hasattr(Chrome, 'jenv')
else:
    _use_jinja2 = False

if _use_jinja2:
    _template_dir = resource_filename(__name__, 'templates/jinja2')
else:
    _template_dir = resource_filename(__name__, 'templates/genshi')

_htdoc_dir = resource_filename(__name__, 'htdocs')


class IniAdminPlugin(Component):

    implements(ITemplateProvider, IAdminPanelProvider)

    excludes = ListOption('iniadmin', 'excludes', 'iniadmin:*,inherit:*',
        doc="""Excludes this options.
        Comma separated list as `section:name` with wildcard characters
        (`*`, `?`).
        """)

    passwords = ListOption('iniadmin', 'passwords',
                           'trac:database,notification:smtp_password',
        doc="""Show input-type as password instead of text.
        Comma separated list as `section:name` with wildcard characters.
        """)

    # IAdminPageProvider methods
    def get_admin_panels(self, req):
        if req.perm.has_permission('TRAC_ADMIN'):
            excludes_match = self._patterns_match(self.excludes)
            for section in sorted(self._get_sections_set(excludes_match)):
                yield ('tracini', 'trac.ini', section, section)

    def render_admin_panel(self, req, cat, page, path_info):
        assert req.perm.has_permission('TRAC_ADMIN')

        excludes_match = self._patterns_match(self.excludes)
        if page not in self._get_sections_set(excludes_match):
            raise TracError("Invalid section %s" % page)

        options = sorted(
            [option for (section, name), option
                    in Option.registry.iteritems()
                    if section == page and \
                       not excludes_match('%s:%s' % (section, name))],
            key=lambda opt: opt.name)

        # Apply changes
        if req.method == 'POST':
            modified = False
            for name, value in req.args.iteritems():
                if any(name == opt.name for opt in options):
                    if self.config.get(page, name) != value:
                        self.config.set(page, name, value)
                        modified = True
            if modified:
                self.log.debug("Updating trac.ini")
                self.config.save()
            req.redirect(req.href.admin(cat, page))

        add_stylesheet(req, 'iniadmin/css/iniadmin.css')

        password_match = self._patterns_match(self.passwords)
        options_data = []
        for option in options:
            doc = self._get_doc(option)
            value = self.config.get(page, option.name)
            # We assume the classes all end in "Option"
            type = option.__class__.__name__.lower()[:-6] or 'text'
            if type == 'bool':
                value = self.config.getbool(page, option.name)
            elif type == 'list' and not isinstance(value,basestring):
                value = unicode(option.sep).join(list(value))
            option_data = {'name': option.name, 'default': option.default,
                           'doc': doc, 'value': value, 'type': type}
            if type == 'extension':
                option_data['options'] = sorted(
                    impl.__class__.__name__
                    for impl in option.xtnpt.extensions(self))
            elif type == 'choice':
                option_data['options'] = sorted([to_unicode(val)
                                                 for val in option.choices],
                                                key=unicode.lower)
            elif type == 'text' and \
                 password_match('%s:%s' % (option.section, option.name)):
                option_data['type'] = 'password'
            options_data.append(option_data)

        data = {'iniadmin': {'section': page, 'options': options_data}}
        return 'iniadmin.html', data

    # ITemplateProvider methods
    def get_templates_dirs(self):
        return [_template_dir]

    def get_htdocs_dirs(self):
        return [('iniadmin', _htdoc_dir)]

    def _get_sections_set(self, excludes_match):
        return set([section
                    for section, name in Option.registry
                    if not excludes_match('%s:%s' % (section, name))])

    def _get_doc(self, obj):
        doc = to_unicode(inspect.getdoc(obj))
        if doc and hasattr(obj, 'doc_domain') and obj.doc_domain:
            doc = dgettext(obj.doc_domain, doc)
        return doc

    def _patterns_match(self, patterns):
        if not patterns:
            return lambda val: False

        wildcard_re = re.compile('[*?]+|[^*?A-Za-z0-9_]+')
        def replace(match):
            text = match.group(0)
            if text.startswith('?'):
                return '[^:]' * len(text)
            if text.startswith('*'):
                return '[^:]*'
            return re.escape(text)

        patterns_re = r'\A(?:%s)\Z' % \
                      '|'.join([wildcard_re.sub(replace, pattern)
                               for pattern in patterns])
        return re.compile(patterns_re).match
