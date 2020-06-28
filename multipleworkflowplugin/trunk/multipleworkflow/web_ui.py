# -*- coding: utf-8 -*-
#
# Copyright (C) 2015-2020 Cinc
#
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

import io
import json
from ConfigParser import SafeConfigParser, ParsingError
from pkg_resources import resource_filename, get_distribution, parse_version
try:
    from genshi.output import HTMLSerializer
except ImportError:
    pass

from trac.admin import IAdminPanelProvider
from trac.core import Component, implements
from trac.ticket.model import Type
from trac.util.html import Markup, html as tag
from trac.util.translation import _, dgettext
from trac.web.api import IRequestHandler
from trac.web.chrome import (add_notice, add_warning,
    ITemplateProvider, add_script_data, add_script)

from workflow import get_workflow_config_by_type, parse_workflow_config


def get_workflow_actions_for_error():
    """This is a small workflow just showing an 'Error' state"""
    txt = "? = Error -> Error"
    return get_workflow_actions_from_text(txt, True)


def get_workflow_actions_from_text(wf_txt, is_error_wf=False):
    """Parse workflow actions in a text snippet
    Note that no section header [ticket-workflow_xxx] must be provided"""

    def get_line_txt(txt):
        try:
            msg = txt.split(']:')[1]
        except IndexError:
            msg = txt

        return msg

    error_txt = ""
    config = SafeConfigParser()
    try:
        config.readfp(
            io.BytesIO("[ticket-workflow]\n" + wf_txt.encode('utf-8')))
        raw_actions = [(key, config.get('ticket-workflow', key)) for key in
                       config.options('ticket-workflow')]
    except ParsingError, err:
        error_txt = u"Parsing error: %s" % get_line_txt(
            unicode(err).replace('\\n', '').replace('<???>', ''))

        if not is_error_wf:  # prevent recursion
            actions, tmp = get_workflow_actions_for_error()
        else:
            actions = []
        return actions, error_txt

    try:
        actions = parse_workflow_config(raw_actions)
    except BaseException, err:
        error_txt = unicode(err)
        if not is_error_wf:  # prevent recursion
            actions, tmp = get_workflow_actions_for_error()
        else:
            actions = []

    return actions, error_txt


def create_workflow_name(name):
    if name == 'default':
        return 'ticket-workflow'
    else:
        return 'ticket-workflow-%s' % name


# This function is taken from WorkflowMacro and modified for the multiple
# workflow display
def create_graph_data(self, req, name=''):
    txt = req.args.get('text')
    if txt:
        actions, error_txt = get_workflow_actions_from_text(txt)
        if error_txt:
            t = error_txt
        else:
            t = "New custom workflow (not saved)"
        if not actions:
            # We should never end here...
            actions = get_workflow_config_by_type(self.config, 'default')
            t = "Custom workflow is broken. Showing default workflow"
    else:
        t = u""
        print(name)
        if name == 'default':
            actions = get_workflow_config_by_type(self.config, 'default')
        else:
            actions = get_workflow_config_by_type(self.config, name)

    states = list(set(
        [state for action in actions.itervalues()
         for state in action['oldstates']] + [action['newstate'] for action in
                                              actions.itervalues()]))

    action_labels = [action_info['label'] for action_name, action_info in
                     actions.items()]
    action_names = actions.keys()

    edges = []
    for name, action in actions.items():
        new_index = states.index(action['newstate'])
        name_index = action_names.index(name)
        for old_state in action['oldstates']:
            old_index = states.index(old_state)
            edges.append((old_index, new_index, name_index))

    args = {}
    width = args.get('width', 800)
    height = args.get('height', 600)
    graph = {'nodes': states, 'actions': action_labels, 'edges': edges,
             'width': width, 'height': height}
    graph_id = '%012x' % id(self)  # id(graph)

    scr_data = {'graph_%s' % graph_id: graph}

    res = tag(
        tag.p(t),
        tag.div('', class_='multiple-workflow-graph trac-noscript',
                id='trac-workflow-graph-%s' % graph_id,
                style="display:inline-block;width:%spx;height:%spx" %
                      (width, height)),
        tag.noscript(
            tag.div(_("Enable JavaScript to display the workflow graph."),
                    class_='system-message')))
    return res, scr_data, graph


def workflow_graph(self, req, name):
    res, scr_data, graph = create_graph_data(self, req, name)

    # add_script(req, 'multipleworkflow/js/excanvas.js', ie_if='IE')
    add_script(req, 'multipleworkflow/js/workflow_graph.js')
    add_script_data(req, scr_data)

    return res


def write_json_response(req, data_dict, httperror=200):
    data = json.dumps(data_dict).encode('utf-8')
    req.send_response(httperror)
    req.send_header('Content-Type', 'application/json; charset=utf-8')
    req.send_header('Content-Length', len(data))
    req.end_headers()
    req.write(data)


class MultipleWorkflowAdminModule(Component):
    """Implements the admin page for workflow editing. See 'Ticket System'
    section.
    """

    implements(IAdminPanelProvider, ITemplateProvider, IRequestHandler)

    # Api changes regarding Genshi started after v1.2. This not only affects templates but also fragment
    # creation using trac.util.html.tag and friends
    pre_1_3 = parse_version(get_distribution("Trac").version) < parse_version('1.3')

    # IRequestHandler methods

    def match_request(self, req):
        return req.path_info == '/multipleworkflow/workflow_render'

    def process_request(self, req):
        req.perm.require('TICKET_ADMIN')

        # div may be a Genshi fragment or a new Trac 1.3 fragment
        div, scr_data, graph = create_graph_data(self, req)
        if self.pre_1_3:
            rendered = "".join(HTMLSerializer()(div.generate()))
            data = {'html': rendered.encode("utf-8"), 'graph_data': graph}
        else:
            rendered = unicode(div)
            data = {'html': rendered, 'graph_data': graph}
        write_json_response(req, data)

    # IAdminPanelProvider methods

    def get_admin_panels(self, req):
        if 'TICKET_ADMIN' in req.perm:
            yield ('ticket', dgettext("messages", ("Ticket System")),
                   'workflowadmin', _("Workflows"))

    def _get_all_types_with_workflow(self, to_upper=False):
        """Returns a list of all ticket types with custom workflow.

        Note that a ticket type is not necessarily available during ticket
        creation if it was deleted in the meantime.
        """
        types = []
        for section in self.config.sections():
            if section.startswith('ticket-workflow-'):
                if to_upper:
                    types.append(section[len('ticket-workflow-'):].upper())
                else:
                    types.append(section[len('ticket-workflow-'):])
        return types

    def install_workflow_controller(self, req):
        """Set MultipleWorkflowPlugin as the current workflow controller in trac.ini.

        Note that the current setting will be replaced and saved using the key 'workflow_mwf_install'. If
        you want to use several workflow controllers at the same time you have to create a list on your own.

        A notice will be shown to the user on success.
        """
        save_key = 'workflow_mwf_install'  # key in section [ticket] to keep the previous setting
        prev_controller = self.config.get('ticket', 'workflow', '')
        self.config.set('ticket', 'workflow', 'MultipleWorkflowPlugin')
        self.config.set('ticket', save_key, prev_controller)
        self.config.save()
        add_notice(req, Markup(_(u'Workflow controller installed by setting <em>workflow=MultipleWorkflowPlugin</em> '
                                 u'in section <em>[ticket]</em>.')))
        add_notice(req, Markup(_(u'Previous workflow controller was saved as '
                                 u'<em>%s=%s</em> in section <em>[ticket]</em>.') % (save_key, prev_controller)))

    def render_admin_panel(self, req, cat, page, path_info):
        req.perm.assert_permission('TICKET_ADMIN')

        if req.method == 'POST':
            if req.args.get('add'):
                cur_types = self._get_all_types_with_workflow(True)
                name = req.args.get('name')
                if name.upper() in cur_types:
                    add_warning(req, _(
                        "There is already a workflow for ticket type '%s'. "
                        "Note that upper/lowercase is ignored"), name)
                else:
                    src_section = create_workflow_name(req.args.get('type'))
                    # Now copy the workflow
                    section = 'ticket-workflow-%s' % name
                    for key, val in self.config.options(src_section):
                        self.config.set(section, key, val)
                    self.config.save()
            elif req.args.get('remove'):
                workflow = 'ticket-workflow-%s' % req.args.get('sel')
                for key, val in self.config.options(workflow):
                    self.config.remove(workflow, key)
                self.config.save()
            elif req.args.get('save'):
                name = req.args.get('name', '')
                if name:
                    section = 'ticket-workflow-%s' % name
                else:
                    # If it's the default workflow the input is disabled and
                    # no value sent
                    section = 'ticket-workflow'

                # Change of workflow name. Remove old data from ini
                if name and name != path_info:
                    old_section = 'ticket-workflow-%s' % path_info
                    for key, val in self.config.options(old_section):
                        self.config.remove(old_section, key)

                # Save new workflow
                for key, val in self.config.options(section):
                    self.config.remove(section, key)
                for line in req.args.get('workflow-actions').split('\n'):
                    try:
                        key, val = line.split('=')
                        self.config.set(section, key, val)
                    except ValueError:
                        # Empty line or missing val
                        pass
                self.config.save()
            elif req.args.get('install'):
                self.install_workflow_controller(req)

            req.redirect(req.href.admin(cat, page))

        # GET, show admin page
        wf_controllers = self.config.getlist('ticket', 'workflow', [])
        data = {'types': self._get_all_types_with_workflow(),
                'trac_types': [enum.name for enum in Type.select(self.env)],
                'wf_controller_installed': u'MultipleWorkflowPlugin' in wf_controllers}
        if not path_info:
            data.update({'view': 'list', 'name': 'default'})
        else:
            data.update({'view': 'detail',
                         'name': path_info,
                         'workflowgraph': workflow_graph(self, req, path_info)})
            if path_info == 'default':
                data['workflow'] = ["%s = %s\n" % (key, val) for key, val in
                                    self.config.options('ticket-workflow')]
            else:
                data['workflow'] = ["%s = %s\n" % (key, val) for key, val in
                                    self.config.options('ticket-workflow-%s' %
                                                        path_info)]
            add_script(req, 'common/js/resizer.js')
            add_script_data(req, {
                'auto_preview_timeout': 2,
                'form_token': req.form_token,
                'trac_types': data['trac_types']})

        if self.pre_1_3:
            return 'multipleworkflowadmin.html', data
        else:
            return 'multipleworkflowadmin_jinja.html', data, {}

    # ITemplateProvider methods

    def get_htdocs_dirs(self):
        return [('multipleworkflow', resource_filename(__name__, 'htdocs'))]

    def get_templates_dirs(self):
        return [resource_filename(__name__, 'templates')]
