# -*- coding: utf-8 -*-
#
# Copyright (C) 2005-2008 Alec Thomas
# Copyright (C) 2009-2010 Michael Renzmann
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

import re

from genshi.builder import tag as builder
from trac.core import TracError
from trac.resource import Resource, ResourceNotFound, render_resource_link
from trac.util.translation import _
from trac.web.chrome import add_stylesheet
from trac.wiki.formatter import format_to_oneliner, wiki_to_html,\
                                wiki_to_oneliner
from trac.wiki.macros import WikiMacroBase, parse_args
from trac.wiki.model import WikiPage

from trachacks.util import natural_sort
from tractags.api import TagSystem


class ListHacksMacro(WikiMacroBase):
    """Provides a list of registered hacks.

    If no arguments are specified, the list will be grouped by hack type
    (category). The user may choose from a list of known Trac releases to filter
    which hacks are displayed; the default is to list hacks that work with Trac
    `0.11`.

    Hack types and Trac releases may be specified as parameter to the macro to
    limit which types and/or releases are specified. Please note:

     * If one or more releases are specified, the "version picker" is not
       displayed.
     * Specified releases are 'OR'-based, i.e. `0.11 0.12` will show hacks
       which are tagged for `0.11` OR `0.12`.
     * If exactly one category is specified, the fieldset legend is not
       displayed.

    See [wiki:type] for a list of hack types, [wiki:release] for a list of
    supported Trac releases.

    Other tags may be passed as well. They will be used as additional filter
    for displayed hacks, but - other than types and releases - have no
    side-effects otherwise.

    For example, the following shows hacks of type `integration` and
    `plugin` for Trac `0.12`:
    {{{
    [[ListHacks(integration plugin 0.12)]]
    }}}
    """
    title_extract = re.compile(r'=\s+([^=]*)=', re.MULTILINE | re.UNICODE)
    self_extract = re.compile(r'\[\[ListHacks[^\]]*\]\]\s?\n?',
                              re.MULTILINE | re.UNICODE)

    def expand_macro(self, formatter, name, args):
        req = formatter.req
        tag_system = TagSystem(self.env)

        all_releases = natural_sort(
            [r.id for r, _ in tag_system.query(req, 'realm:wiki release')])
        all_categories = sorted(
            [r.id for r, _ in tag_system.query(req, 'realm:wiki type')])

        hide_release_picker = False
        hide_fieldset_legend = False
        hide_fieldset_description = False
        other = []
        if args:
            categories = []
            releases = []
            for arg in args.split():
                if arg in all_releases:
                    hide_release_picker = True
                    releases.append(arg)
                elif arg in all_categories:
                    categories.append(arg)
                else:
                    other.append(arg)

            if len(categories) or len(releases):
                hide_fieldset_description = True

            if not len(categories):
                categories = all_categories
            elif len(categories) == 1:
                hide_fieldset_legend = True

            if not len(releases):
                releases = all_releases
        else:
            categories = all_categories
            releases = all_releases

        if 'update_th_filter' in req.args:
            show_releases = req.args.get('release', ['0.11'])
            if isinstance(show_releases, basestring):
                show_releases = [show_releases]
            req.session['th_release_filter'] = ','.join(show_releases)
        else:
            show_releases = \
                req.session.get('th_release_filter', '0.11').split(',')

        output = builder.tag()
        if not hide_release_picker:
            style = "text-align:right; padding-top:1em; margin-right:5em;"
            form = builder.form('\n', style=style, method="get")

            style = "font-size:xx-small;"
            span = builder.span("Show hacks for releases:", style=style)

            for version in releases:
                inp = builder.input(version, type_="checkbox", name="release",
                                    value=version)
                if version in show_releases:
                    inp(checked="checked")
                span(inp, '\n')

            style = "font-size:xx-small; padding:0; border:solid 1px black;"
            span(builder.input(name="update_th_filter", type_="submit",
                               style=style, value="Update"), '\n')
            form('\n', span, '\n')
            output.append(form)

        def link(resource):
            return render_resource_link(self.env, formatter.context,
                                        resource, 'compact')

        for category in categories:
            page = WikiPage(self.env, category)
            match = self.title_extract.search(page.text)
            if match:
                cat_title = '%s' % match.group(1).strip()
                cat_body = self.title_extract.sub('', page.text, 1)
            else:
                cat_title = '%s' % category
                cat_body = page.text
            cat_body = self.self_extract.sub('', cat_body).strip()

            style = 'padding:1em; margin:0em 5em 2em 5em; border:1px solid #999;'
            fieldset = builder.fieldset('\n', style=style)
            if not hide_fieldset_legend:
                legend = builder.legend(style="color: #999;")
                legend(builder.a(cat_title, href=self.env.href.wiki(category)))
                fieldset(legend, '\n')
            if not hide_fieldset_description:
                fieldset(builder.p(wiki_to_html(cat_body, self.env, req)))

            ul = builder.ul('\n', class_='listtagged')
            query = 'realm:wiki (%s) %s %s' % \
                (' or '.join(show_releases), category, ' '.join(other))

            lines = 0
            for resource, tags in tag_system.query(req, query):
                # filter out the page used to make important tags
                # persistent
                if resource.id == 'tags/persistent':
                    continue

                lines += 1
                li = builder.li(link(resource), ': ')

                page = WikiPage(self.env, resource)
                match = self.title_extract.search(page.text)
                description = "''no description available''"
                if match:
                    if match.group(1):
                        description = match.group(1).strip()

                li(wiki_to_oneliner(description, self.env, req=req))
                if tags:
                    if hide_fieldset_legend is False and category in tags:
                        tags.remove(category)
                        self.log.debug("hide %s: no legend" % category)
                    for o in other:
                        if o in tags:
                            tags.remove(o)
                    rendered_tags = [link(resource('tag', tag))
                                     for tag in natural_sort(tags)]

                    span = builder.span(style="font-size:xx-small;")
                    span(' (tags: ', rendered_tags[0],
                       [(', ', tag) for tag in rendered_tags[1:]], ')')
                    li(span)
                ul(li, '\n')

            if lines:
                fieldset(ul, '\n')
            else:
                message = "No results for %s." % \
                    (hide_release_picker and "this version" or "your selection")
                fieldset(builder.p(builder.em(message)), '\n')
            output.append(fieldset)

        return output


class ListHackTypesMacro(WikiMacroBase):
    """Provides a list of known hack types (categories)."""
    title_extract = re.compile(r'=\s+([^=]*)=', re.MULTILINE | re.UNICODE)
    self_extract = re.compile(r'\[\[ListHacks[^\]]*\]\]\s?\n?',
                              re.MULTILINE | re.UNICODE)

    def expand_macro(self, formatter, name, args):
        req = formatter.req
        add_stylesheet(req, 'hacks/css/trachacks.css')

        tag_system = TagSystem(self.env)

        categories = natural_sort([r.id for r, _ in
                                   tag_system.query(req, 'realm:wiki type')])

        def link(resource):
            return render_resource_link(self.env, formatter.context,
                                        resource, 'compact')

        dl = builder.dl(class_='hacktypesmacro')
        for category in categories:
            page = WikiPage(self.env, category)
            match = self.title_extract.search(page.text)
            if match:
                cat_title = '%s' % match.group(1).strip()
                cat_body = self.title_extract.sub('', page.text, 1)
            else:
                cat_title = '%s' % category
                cat_body = page.text
            cat_body = self.self_extract.sub('', cat_body).strip()
            dl(builder.dt(link(Resource('wiki', category))))
            dl(builder.dd(wiki_to_html(cat_body, self.env, req)))

        return dl


class ListTracReleasesMacro(WikiMacroBase):
    """Provides a list of known Trac releases."""
    title_extract = re.compile(r'=\s+([^=]*)=', re.MULTILINE | re.UNICODE)

    def expand_macro(self, formatter, name, args):
        req = formatter.req
        add_stylesheet(req, 'hacks/css/trachacks.css')

        tag_system = TagSystem(self.env)
        releases = natural_sort([r.id for r, _ in
                                 tag_system.query(req, 'realm:wiki release')])

        def link(resource):
            return render_resource_link(self.env, formatter.context,
                                        resource, 'compact')

        dl = builder.dl(class_='tracreleasesmacro')
        for release in releases:
            page = WikiPage(self.env, release)
            match = self.title_extract.search(page.text)
            if match:
                rel_title = '%s' % match.group(1).strip()
            else:
                rel_title = '%s' % release

            dl(builder.dt(link(Resource('wiki', release))))
            dl(builder.dd(wiki_to_html(rel_title, self.env, req)))

        return dl


class MaintainerMacro(WikiMacroBase):
    """Returns the maintainer of a hack.

    The macro accepts the hack name as an optional parameter. If not
    specified, the context must be a wiki page and the hack name is inferred
    from the wiki page name.
    """

    def expand_macro(self, formatter, name, args):
        largs = parse_args(args)[0]
        if len(largs) > 1:
            raise TracError(_("Invalid number of arguments"))
        resource = formatter.context.resource
        if resource.realm == 'wiki' or largs and largs[0]:
            id = largs[0] if largs and largs[0] else resource.id
            from trac.ticket.model import Component
            try:
                component = Component(self.env, id)
            except ResourceNotFound:
                return builder.em(_('Component "%(name)s" does not exist',
                                    name=id))
            else:
                maintainer = component.owner
        else:
            raise TracError(_("Hack name must be specified as argument when "
                              "the context realm is not 'wiki'"))
        return format_to_oneliner(self.env, formatter.context, maintainer)
