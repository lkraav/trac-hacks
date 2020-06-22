# -*- coding: utf-8 -*-
# Copyright (c) 2016-2020 Cinc
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
# 3. The name of the author may not be used to endorse or promote products
#    derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE AUTHOR ``AS IS'' AND ANY EXPRESS OR
# IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES
# OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
# IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT
# NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF
# THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

__author__ = 'Cinc'

from trac.core import implements, TracError
from trac.resource import ResourceNotFound
from trac.ticket.admin import MilestoneAdminPanel
from trac.ticket.model import Milestone
from trac.util.datefmt import parse_date
from trac.util.translation import _
from trac.web.api import IRequestFilter
from trac.web.chrome import Chrome, ITemplateProvider, ITemplateStreamFilter, \
    add_script, add_script_data, add_notice, add_stylesheet
from trac.wiki import WikiSystem, WikiPage
from genshi import HTML
from genshi.filters import Transformer
from genshi.template.markup import MarkupTemplate
from string import Template


class MilestoneTemplatePlugin(MilestoneAdminPanel):
    """Use templates when creating milestones.

    Any wiki page with a name starting with ''!MilestoneTemplates/'' can be used as a template. This works in a
    similar way as wiki templates work (see PageTemplates).

    Examples for milestone templates:

    * !MilestoneTemplates/MsTemplate
    * !MilestoneTemplates/MyMilestoneTemplate

    Milestone template may use the variable ''$MILESTONE'' for inserting the chosen milestone name into the
    description. This may be useful if the template contains a TracQuery with milestone parameter.

    {{{
    [[TicketQuery(max=5,status=closed,milestone=$MILESTONE,format=table,col=resolution|summary|milestone)]]
    }}}
    """

    implements(ITemplateStreamFilter, IRequestFilter, ITemplateProvider)

    MILESTONE_TEMPLATES_PREFIX = u'MilestoneTemplates/'

    admin_page_template = u"""<div class="field">
            <label>Template:
            <select id="ms-templates" name="template">
                <option value="">(blank)</option>
                {options}
            </select>
            <span class="hint">For Milestone description</span>
            </label>
        </div>"""
    admin_option_tmpl = u"""<option value="{templ}">
                    {templ}
                </option>"""

    milestone_page_template = u"""<div class="field">
            <p>Or use a template for the description:</p>
            <label>Template:
            <select id="ms-templates" name="template">
                <option value=""{sel}>(Use given Description)</option>
                {options}
            </select>
            <span class="hint">The description will be replaced with the template contents on submit.</span>
            </label>
        </div>"""
    milestone_option_tmpl = u"""<option value="{templ}"{sel}>
                    {templ}
                </option>"""

    preview_tmpl = u"""
            <div id="mschange" class="ticketdraft" style="display: none">
                <h3 id="ms-change-h3">Preview:</h3>
                    <div class="notes-preview comment searchable">
                    </div>
            </div>
    """
    def __init__(self):
        # Let our component handle the milestone stuff
        if self.env.is_enabled(MilestoneAdminPanel):
            self.env.disable_component(MilestoneAdminPanel)

    def render_admin_panel(self, req, cat, page, version):
        req.perm.require('MILESTONE_VIEW')

        templ = req.args.get('template', '')
        if req.method == 'POST' and templ:
            if req.args.get('add') and req.args.get('name'):
                req.perm.require('MILESTONE_CREATE')
                name = req.args.get('name')
                try:
                    mil = Milestone(self.env, name=name)
                except ResourceNotFound:
                    mil = Milestone(self.env)
                    mil.name = name
                    mil.description = self.get_description_from_template(req, templ, name)
                    if req.args.get('duedate'):
                        mil.due = parse_date(req.args.get('duedate'),
                                             req.tz, 'datetime')
                    mil.insert()
                    add_notice(req, _(u'The milestone "%(name)s" has been '
                                      u'added.', name=name))
                    req.redirect(req.href.admin(cat, page))
                else:
                    if mil.name is None:
                        raise TracError(_(u'Invalid milestone name.'))
                    raise TracError(_(u'Milestone %(name)s already exists.',
                                      name=name))
        return super(MilestoneAdminPanel, self).render_admin_panel(req, cat, page, version)

    def get_description_from_template(self, req, template, ms_name):
        """Get template text from wiki and replace $MILESTONE with given milestone name

        :param req: Request object
        :param template: template name to be used. This is a wiki page name.
        :param ms_name: milestone name chosen by the user

        :return
        """
        template_page = WikiPage(self.env, self.MILESTONE_TEMPLATES_PREFIX+template)
        if template_page and template_page.exists and \
                'WIKI_VIEW' in req.perm(template_page.resource):
            return Template(template_page.text).safe_substitute(MILESTONE=ms_name)
        return u""

    # ITemplateStreamFilter methods

    def filter_stream(self, req, method, filename, stream, data):
        path = req.path_info.split('/')
        if filename == 'admin_milestones.html':
            # Milestone creation from admin page
            if data:
                view = data.get('view')
                if view == 'list':
                    templates = self.get_milestone_templates(req)
                    if templates:
                        filter_ = Transformer('//form[@id="addmilestone"]//div[@class="buttons"]')
                        stream = stream | filter_.before(HTML(self.create_admin_page_select_ctrl(templates)))
                elif view == 'detail':
                    # Add preview div
                    tmpl = MarkupTemplate(self.preview_tmpl)
                    self._add_preview(req)
                    filter_ = Transformer('//form[@id="edit"]//textarea')
                    stream = stream | filter_.after(tmpl.generate())
        elif len(path) > 1 and path[1] == 'milestone':
            action = req.args.get('action')
            if action == 'new':
                # Milestone creation from roadmap page
                templates = self.get_milestone_templates(req)
                self._add_preview(req)
                filter_ = Transformer('//form[@id="edit"]//div[contains(@class, "description")]')
                if templates:
                    stream = stream | filter_.after(HTML(self.create_milestone_page_select_ctrl(templates)))
                tmpl = MarkupTemplate(self.preview_tmpl)
                stream = stream | filter_.after(tmpl.generate())
            elif action == 'edit':
                self._add_preview(req)
                filter_ = Transformer('//form[@id="edit"]//textarea')
                if req.method == "POST":
                    # Milestone creation from roadmap page. Duplicate name redirected to edit page.
                    templates = self.get_milestone_templates(req)
                    if templates:
                        stream = stream | filter_.after(HTML(self.create_milestone_page_select_ctrl(templates,
                                                                                      req.args.get('template', None))))
                tmpl = MarkupTemplate(self.preview_tmpl)
                stream = stream | filter_.after(tmpl.generate())

        return stream

    def _add_preview(self, req):
        Chrome(self.env).add_auto_preview(req)
        scr_data = {'ms_preview_renderer': req.href.wiki_render()}
        add_script_data(req, scr_data)
        add_script(req, 'mstemplate/js/ms_preview.js')
        add_stylesheet(req, 'common/css/ticket.css')
        add_stylesheet(req, 'mstemplate/css/ms_preview.css')

    def get_milestone_templates(self, req):
        """Get milestone templates from wiki. You need WIKI_VIEW oermission to use templates"""
        prefix = self.MILESTONE_TEMPLATES_PREFIX
        ws = WikiSystem(self.env)
        templates = [template[len(prefix):]
                    for template in ws.get_pages(prefix)
                    if 'WIKI_VIEW' in req.perm('wiki', template)]
        return templates

    def create_admin_page_select_ctrl(self, templates):
        """Create a select control to be added to 'Add milestone' page in the admin area.

        :param templates: list of templates (wiki page names)
        :return <div> tag holding a select control with label (unicode)
        """
        tmpl = self.admin_page_template
        opt = ''
        for item in templates:
            opt += self.admin_option_tmpl.format(templ=item)
        return tmpl.format(options=opt)

    def create_milestone_page_select_ctrl(self, templates, cur_sel=None):
        """Create a select control to be added to 'Add milestone' page or 'Edit milestone' page. USed when creating
           milestones from the Roadmap page.

        :param templates: list of templates (wiki page names)
        :param cur_sel: template selected by the user or None if using description field. Note that this is always
                        None for admin page
        :return <div> tag holding a select control with label (unicode)
        """
        tmpl = self.milestone_page_template
        opt = ''
        for item in templates:
            opt += self.milestone_option_tmpl.format(templ=item, sel=' selected="selected"' if cur_sel == item else '')
        return tmpl.format(sel=' selected="selected"' if not cur_sel else '', options=opt)

    # IRequestFilter methods

    def pre_process_request(self, req, handler):
        """Add the template contents as description when adding from the
        roadmap page.
        """
        # Fill milestone description with contents of template.
        if req.method == 'POST' and self._is_valid_request(req):
            template = req.args.get('template')
            if req.args.get('add') and template:
                # The name of the milestone is given as a parameter to the template
                req.args[u'description'] = self.get_description_from_template(req, template, req.args.get('name'))
        return handler

    @staticmethod
    def _is_valid_request(req):
        """Check request for correct path and valid form token"""
        if req.path_info.startswith('/milestone') and \
                req.args.get('__FORM_TOKEN') == req.form_token:
            return True
        return False

    def post_process_request(self, req, template, data, content_type):
        return template, data, content_type

    # ITemplateProvider methods

    def get_templates_dirs(self):
        return []

    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('mstemplate', resource_filename(__name__, 'htdocs'))]
