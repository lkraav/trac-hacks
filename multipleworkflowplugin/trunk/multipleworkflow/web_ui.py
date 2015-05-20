# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 Cinc
#
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

__author__ = 'Cinc'

import json
import io
from ConfigParser import SafeConfigParser, ParsingError
from pkg_resources import resource_filename
from trac.core import Component, implements
from trac.admin import IAdminPanelProvider
from trac.web.chrome import ITemplateProvider, add_script_data, add_script
from trac.web.api import IRequestHandler
from trac.util.translation import _, dgettext
from trac.ticket.model import Type
from genshi.builder import tag
from genshi.output import HTMLSerializer
from workflow import get_workflow_config_default, get_workflow_config_by_type, parse_workflow_config


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
        config.readfp(io.BytesIO("[ticket-workflow]\n"+wf_txt.encode('utf-8')))
        raw_actions = [(key, config.get('ticket-workflow', key)) for key in config.options('ticket-workflow')]
    except ParsingError, err:
        error_txt = u"Parsing error: %s" % get_line_txt(unicode(err).replace('\\n', '').replace('<???>', ''))

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


# This function is taken from WorkflowMacro and modified for the multiple workflow display
def create_graph_data(self, req):

    txt = req.args.get('text')
    if txt:
        actions, error_txt = get_workflow_actions_from_text(txt)
        if error_txt:
            t = error_txt
        else:
            t = "New custom workflow (not saved)"
        if not actions:
            # We should never end here...
            actions = get_workflow_config_default(self.config)
            t = "Custom workflow is broken. Showing default workflow"
    else:
        t = "Workflow for '%s'" % req.args.get('type')
        actions = get_workflow_config_by_type(self.config, req.args.get('type'))
        if not actions:
            actions = get_workflow_config_default(self.config)
            if not req.args.get('type'):
                t = u"Showing default workflow"
            else:
                t = u"'%s' uses default workflow" % req.args.get('type')

    states = list(set(
        [state for action in actions.itervalues()
         for state in action['oldstates']] + [action['newstate'] for action in actions.itervalues()]))

    action_labels = [action_info['name'] for action_name, action_info in actions.items()]
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


def workflow_graph(self, req):

    res, scr_data, graph = create_graph_data(self, req)

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
    """Implements the admin page for workflow editing. See 'Ticket System' section."""

    implements(IAdminPanelProvider, ITemplateProvider, IRequestHandler)

    # IRequestHandler methods
    # Theses methods are used for the preview rendering
    def match_request(self, req):
        return req.path_info == '/multipleworkflow/workflow_render'

    def process_request(self, req):
        req.perm.require('TICKET_ADMIN')

        div, scr_data, graph = create_graph_data(self, req)
        rendered = "".join(HTMLSerializer()(div.generate()))
        data = {'html': rendered.encode("utf-8"), 'graph_data': graph}
        write_json_response(req, data)

    # IAdminPanelProvider methods
    def get_admin_panels(self, req):
        if 'TICKET_ADMIN' in req.perm:
            yield ('ticket', dgettext("messages", ("Ticket System")),
                   'workflowadmin', _("Workflows"))

    def render_admin_panel(self, req, cat, page, path_info):
        req.perm.assert_permission('TICKET_ADMIN')

        if req.method == 'POST':
            # Save button clicked
            print req.args.get('workflow-actions')
            tkt_type = req.args.get('type')
            if tkt_type == 'default':
                name = 'ticket-workflow'
            else:
                name = 'ticket-workflow-%s' % tkt_type

            for key, val in self.config.options(name):
                self.config.remove(name, key)

            for line in req.args.get('workflow-actions').split('\n'):
                try:
                    key, val= line.split('=')
                    self.config.set(name, key, val)
                except ValueError:
                    # Empty line or missing val
                    pass
            self.config.save()

            req.redirect(req.href.admin(cat, page)+'?type='+req.args.get('type'))

        # GET, show admin page
        if req.args.get('type'):
            selected = req.args.get('type')
            raw_actions = ["%s = %s\n" % (key, val) for key, val in self.config.options('ticket-workflow-%s' % selected)]
        else:
            raw_actions = []
            selected = ""

        types = [enum.name for enum in Type.select(self.env)]
        if not raw_actions:
            raw_actions = ["%s = %s\n" % (key, val) for key, val in self.config.options('ticket-workflow')]

        data = {'types': types, 'workflowgraph': workflow_graph(self, req),
                'selected': selected, 'workflow': raw_actions, 'panel_path': '/'+cat+'/'+page}

        add_script(req, 'common/js/resizer.js')
        add_script_data(req, {
            'auto_preview_timeout': 2,
            'form_token': req.form_token})

        return "multipleworkflowadmin.html", data

    # ITemplateProvider methods
    def get_htdocs_dirs(self):
        return [('multipleworkflow', resource_filename(__name__, 'htdocs'))]

    def get_templates_dirs(self):
        return [resource_filename(__name__, 'templates')]
