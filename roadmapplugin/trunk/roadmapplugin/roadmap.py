# -*- coding: utf-8 -*-
#
# Copyright (C) 2010 daveappendix
# Copyright (C) 2010-2012 Franz Mayer <franz.mayer@gefasoft.de>
#
# "THE BEER-WARE LICENSE" (Revision 42):
# <franz.mayer@gefasoft.de> wrote this file.  As long as you retain this
# notice you can do whatever you want with this stuff. If we meet some day,
# and you think this stuff is worth it, you can buy me a beer in return.
# Franz Mayer
#
# Author: Franz Mayer <franz.mayer@gefasoft.de>

import re
from operator import attrgetter
from pkg_resources import resource_filename  # @UnresolvedImport

from trac.core import Component, implements
from trac.ticket.roadmap import RoadmapModule
from trac.util.html import Markup, tag
from trac.util.translation import domain_functions
from trac.web.api import IRequestFilter
from trac.web.chrome import Chrome


__all__ = ('SetupRoadmap', 'FilterRoadmap', 'SortRoadMap')


_, tag_, N_, add_domain = domain_functions(
    'roadmapplugin', '_', 'tag_', 'N_', 'add_domain')


_use_jinja2 = hasattr(Chrome, 'jenv')

if _use_jinja2:
    from trac.web.chrome import ITemplateProvider, add_script, add_script_data
    ITemplateStreamFilter = Transformer = None
else:
    from genshi.filters import Transformer
    from trac.web.api import ITemplateStreamFilter
    ITemplateProvider = add_script = add_script_data = None


keys = [u'noduedate', u'completed']
showkeys = {'noduedate': 'hidenoduedate', 'completed': 'showcompleted'}

# returns the name of the attribute plus the prefix roadmap.filter


def _get_session(req, name, default):
    return req.session.get(_get_session_key_name(name), default)


def _get_session_key_name(name):
    return "roadmap.filter.%s" % name
# saves a single attribute as a session key


def _set_session_attrib(req, name, value):
    req.session[_get_session_key_name(name)] = value


def _save_show_to_session(req):
    if 'show-roadmap' in req.args:
        for key in keys:
            if key in req.args['show-roadmap']:
                _set_session_attrib(req, showkeys[key], '1')
            else:
                _set_session_attrib(req, showkeys[key], '0')
    else:
        for key in keys:
            _set_session_attrib(req, showkeys[key], '0')


def _get_show(req):
    show = []
    for key in keys:
        erg = req.session.get(_get_session_key_name(showkeys[key]), '0')
        if erg == '1':
            if len(show) == 0:
                show = [key]
            else:
                show.append(key)
    return show


def _get_settings(req, name, default):
    session_key = _get_session_key_name(name)
    # user pressed submit button in the config area so this settings have to be used
    if 'user_modification' in req.args:
        if name not in req.args:  # key with given name does not exist in request
            return default
        else:  # value of the given key is saved to session keys
            req.session[session_key] = req.args[name]
            return req.args[name]
    # user reloaded the page or gave no attribs, so session keys will be given, if existing
    elif session_key in req.session:
        return req.session[session_key]
    else:
        return default


_directions = (N_('Descending'), N_('Ascending'))
_criterias = (N_('Name'), N_('Due'))


class SetupRoadmap(Component):

    if _use_jinja2:
        implements(IRequestFilter, ITemplateProvider)
    else:
        implements(ITemplateStreamFilter)

    def __init__(self):
        try:
            locale_dir = resource_filename(__name__, 'locale')
        except:
            pass
        else:
            add_domain(self.env.path, locale_dir)

    # IRequestFilter methods

    def pre_process_request(self, req, handler):
        return handler

    def post_process_request(self, req, template, data, content_type):
        if req.path_info == '/roadmap':
            add_script(req, 'roadmapplugin/prefs.js')
            add_script_data(req, roadmapplugin=Markup(self._get_inputs(req)))
        return template, data, content_type

    # ITemplateProvider methods

    def get_htdocs_dirs(self):
        yield 'roadmapplugin', resource_filename(__name__, 'htdocs')

    def get_templates_dirs(self):
        return ()

    # ITemplateStreamFilter methods

    def filter_stream(self, req, method, filename, stream, data):
        if filename == 'roadmap.html':
            # Insert the new field for entering user names
            filter_ = Transformer('//form[@id="prefs"]/div[@class="buttons"]')
            stream |= filter_.before(self._get_inputs(req))
        return stream

    # Internal methods

    def _get_inputs(self, req):
        return tag(self._get_filter_inputs(req), self._get_sort_inputs(req))

    def _get_sort_inputs(self, req):
        sortcrit = _get_settings(req, 'sortcrit', _criterias[0])
        sortdirect = _get_settings(req, 'sortdirect', _directions[0])

        div = tag.div(_('Sort by: '))
        select = tag.select(name='sortcrit')
        for crit in _criterias:
            selected = 'selected' if sortcrit == crit else None
            select.append(tag.option(_(crit), value=crit, selected=selected))
        div.append(select)
        select = tag.select(name='sortdirect')
        for dir_ in _directions:
            selected = 'selected' if sortdirect == dir_ else None
            select.append(tag.option(_(dir_), value=dir_, selected=selected))
        div.append(select)
        return div

    def _filterBox(self, req, label, name):
        title = _("available prefixes: contains: ~, starts with: ^, ends with: $")
        value = _get_session(req, name, '')
        input_ = tag.input(type="text", name=name, value=value,
                           style_="width:60%", title=title)
        return tag.label(label, input_)

    def _toggleBox(self, req, label, name, default):
        checked = _get_session(req, name, default) == '1'
        checkbox = tag.input(type='checkbox', id=name, name=name, value='true',
                             checked='checked' if checked else None)
        return tag(checkbox, ' ', tag.label(label, for_=name))

    def _hackedHiddenField(self):
        # Hack: shove a hidden field in so we can tell if the update
        # button has been hit.
        return tag.input(type='hidden',
                         name='user_modification',
                         value='true')

    def _get_filter_inputs(self, req):
        return tag.div(
            self._hackedHiddenField(),
            self._toggleBox(req, _('Show milestone descriptions'),
                            'show_descriptions', 'true'),
            tag.br(),
            self._filterBox(req, _('Filter: '), "inc_milestones"),
        )


class FilterRoadmap(Component):
    """Filters roadmap milestones.

Existing Trac convention says that the following prefixes on the filter
do different things:
 - `~` contains
 - `^` starts with
 - `$` ends with

This plugin uses same convention.

For more information about this plugin, see
[http://trac-hacks.org/wiki/RoadmapPlugin trac-hacks page].

Mainly copied from [https://trac-hacks.org/wiki/RoadmapFilterPlugin RoadmapFilterPlugin]
and modified a bit.

Thanks to [http://trac-hacks.org/wiki/daveappendix daveappendix]."""

    implements(IRequestFilter)

    # Internal methods

    def _getCheckbox(self, req, name, default):
        session_key = _get_session_key_name(name)
        result = '0'

        if 'user_modification' in req.args:
            # User has hit the update button on the form,
            # so update the session data.
            if name in req.args:
                result = '1'
            if result == '1':
                req.session[session_key] = '1'
            else:
                req.session[session_key] = '0'
        elif req.session.get(session_key, default) == '1':
            result = '1'

        return result

    def _matchFilter(self, name, filters):
        # Existing Trac convention says that the following prefixes
        # on the filter do different things:
        #   ~  - contains
        #   ^  - starts with
        #   $  = ends with
        for filter_ in filters:
            if filter_.startswith('^'):
                if name.startswith(filter_[1:]):
                    return True
            elif filter_.startswith('$'):
                if name.endswith(filter_[1:]):
                    return True
            elif filter_.startswith('~'):
                if name.find(filter_[1:]) >= 0:
                    return True
            elif name == filter_:
                return True
        return False

    # IRequestFilter methods

    def pre_process_request(self, req, handler):
        if handler is RoadmapModule:
            if 'user_modification' in req.args:
                _save_show_to_session(req)
            else:
                req.args['show-roadmap'] = _get_show(req)
        return handler

    def post_process_request(self, req, template, data, content_type):
        if template == 'roadmap.html':
            inc_milestones = _get_settings(req, 'inc_milestones', '')
            exc_milestones = _get_settings(req, 'exc_milestones', '')
            show_descriptions = self._getCheckbox(
                req, 'show_descriptions', '1') == '1'

            if inc_milestones != '':
                inc_milestones = [m.strip() for m in inc_milestones.split('|')]
                filteredMilestones = []
                filteredStats = []
                for i in range(len(data['milestones'])):
                    m = data['milestones'][i]
                    if self._matchFilter(m.name, inc_milestones):
                        filteredMilestones.append(m)
                        filteredStats.append(data['milestone_stats'][i])
                data['milestones'] = filteredMilestones
                data['milestone_stats'] = filteredStats

            if exc_milestones != '':
                exc_milestones = [m.strip() for m in exc_milestones.split('|')]
                filteredMilestones = []
                filteredStats = []
                for i in range(len(data['milestones'])):
                    m = data['milestones'][i]
                    if not self._matchFilter(m.name, exc_milestones):
                        filteredMilestones.append(m)
                        filteredStats.append(data['milestone_stats'][i])
                data['milestones'] = filteredMilestones
                data['milestone_stats'] = filteredStats

            if not show_descriptions:
                for m in data['milestones']:
                    m.description = ''

        return template, data, content_type


class SortRoadMap(Component):
    """Shows another checkbox in roadmap view,
which allows you to sort milestones in descending order of due date."""

    implements(IRequestFilter)

    # Internal methods

    def _comparems(self, m1, m2, sort_crit):
        if sort_crit == _criterias[0]:
            # the milestone names are divided at the dots to compare (sub)versions
            v1 = m1.name.upper().split('.')
            v2 = m2.name.upper().split('.')
            depth = 0
            # As long as both have entries and no result so far
            while depth < len(v1) and depth < len(v2):
                # if (sub)version is different
                if v1[depth] != v2[depth]:
                    # Find leading Numbers in both entrys
                    leadnum1 = re.search(r"\A\d+", v1[depth])
                    leadnum2 = re.search(r"\A\d+", v2[depth])
                    if leadnum1 and leadnum2:
                        if leadnum1 != leadnum2:
                            return int(leadnum1.group(0)) - int(leadnum2.group(0))
                        else:
                            r1 = v1[depth].lstrip(leadnum1.group(0))
                            r2 = v2[depth].lstrip(leadnum2.group(0))
                            return 1 if (r1 > r2) else -1
                    elif leadnum1:
                        return 1
                    elif leadnum2:
                        return -1
                    else:
                        return 1 if (v1[depth] > v2[depth]) else -1
                # otherwise look in next depth
                depth += 1
                # End of WHILE

            # At least one of the arrays ended and all numbers were equal so far
            # milestone with more numbers is bigger
            return len(v1) - len(v2)
        # other criteria not needed. Can be sorted easier by buildin methods
        else:
            return 0

    # IRequestFilter methods

    def pre_process_request(self, req, handler):
        if handler is RoadmapModule:
            if 'user_modification' in req.args:
                _save_show_to_session(req)
            else:
                req.args['show-roadmap'] = _get_show(req)
        return handler

    def post_process_request(self, req, template, data, content_type):
        if template == 'roadmap.html':
            sort_direct = _get_settings(req, 'sortdirect', _directions[0])
            sort_crit = _get_settings(req, 'sortcrit', _criterias[0])

            milestones = data['milestones']
            sortedmilestones = []

            if sort_crit == _criterias[0]:
                for m in milestones:
                    if len(sortedmilestones) == 0:
                        sortedmilestones.append(m)
                    else:
                        index = 0
                        inserted = False
                        while not inserted and index < len(sortedmilestones):
                            sm = sortedmilestones[index]
                            if self._comparems(m, sm, sort_crit) >= 0:
                                sortedmilestones.insert(index, m)
                                inserted = True
                            else:
                                index += 1
                            if inserted:
                                break
                        # All milestonenames were lower so append the milestone
                        if not inserted:
                            sortedmilestones.append(m)
            else:
                ms_with_due = []
                ms_wo_due = []
                for m in milestones:
                    if m.due:
                        ms_with_due.append(m)
                    else:
                        ms_wo_due.append(m)
                stats = data['milestone_stats']
                new_stats = []
                sortedmilestones = sorted(ms_with_due, key=attrgetter('due'))
                sortedmilestones.extend(ms_wo_due)

            if sort_direct == _directions[1]:
                sortedmilestones.reverse()

            stats = data['milestone_stats']
            new_stats = []

            for m in sortedmilestones:
                for j, om in enumerate(milestones):
                    if m.name == om.name:
                        new_stats.append(stats[j])
                        continue
            data['milestones'] = sortedmilestones
            data['milestone_stats'] = new_stats
        return template, data, content_type
