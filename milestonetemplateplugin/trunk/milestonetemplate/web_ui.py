# -*- coding: utf-8 -*-

__author__ = 'Cinc'

from trac.core import implements, TracError
from trac.resource import ResourceNotFound
from trac.ticket.admin import MilestoneAdminPanel
from trac.ticket.model import Milestone
from trac.util.datefmt import parse_date
from trac.util.text import _
from trac.web.api import IRequestFilter
from trac.web.chrome import add_notice, add_script, add_script_data, add_stylesheet, \
    ITemplateProvider, ITemplateStreamFilter
from trac.wiki import WikiSystem, WikiPage
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

    admin_page_template = u"""
        <div xmlns:py="http://genshi.edgewall.org/" class="field">
            <label>Template:
            <select id="ms-templates" name="template">
                <option value="">(blank)</option>
                <option py:for="tmpl in templates" value="$tmpl">
                    ${tmpl}
                </option>
            </select>
            <span class="hint">For Milestone description</span>
            </label>
        </div>
        """
    edit_page_template = u"""
        <div xmlns:py="http://genshi.edgewall.org/" class="field">
            <div id="mschange" class="ticketdraft" style="display: none">
                <h3 id="ms-change-h3">Preview:</h3>
                    <div class="notes-preview comment searchable">
                    </div>
            </div>
            <p>Or use a template for the description:</p>
            <label>Template:
            <select id="ms-templates" name="template">
                <option value="" selected="${sel == None or None}">(Use given Description)</option>
                <option py:for="tmpl in templates" value="$tmpl" selected="${sel == tmpl or None}">
                    ${tmpl}
                </option>
            </select>
            <span class="hint">The description will be replaced with the template contents on submit.</span>
            </label>
        </div>
        """
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
                if data.get('view') == 'list':
                    templates = self.get_milestone_templates(req)
                    if templates:
                        filter_ = Transformer('//form[@id="addmilestone"]//div[@class="buttons"]')
                        stream = stream | filter_.before(self.create_templ_select_ctrl(templates, self.admin_page_template))
                elif data.get('view') == 'detail':
                    # Add preview div
                    templates = self.get_milestone_templates(req)
                    tmpl = MarkupTemplate(self.preview_tmpl)
                    self._add_preview(req, req.base_path+'/preview_render')
                    filter_ = Transformer('//form[@id="modifymilestone"]//div[@class="buttons"]')
                    stream = stream | filter_.before(tmpl.generate())
        elif req.args.get('action') == 'new' and len(path) > 1 and path[1] == 'milestone':
            # Milestone creation from roadmap page
            templates = self.get_milestone_templates(req)
            if templates:
                self._add_preview(req, 'preview_render')
                filter_ = Transformer('//form[@id="edit"]//p')
                stream = stream | filter_.after(self.create_templ_select_ctrl(templates, self.edit_page_template))
        elif filename == 'milestone_edit.html' and req.method == 'POST':
            # Milestone creation from roadmap page. Duplicate name redirected to edit page.
            templates = self.get_milestone_templates(req)
            if templates:
                filter_ = Transformer('//form[@id="edit"]//p')
                stream = stream | filter_.after(self.create_templ_select_ctrl(templates, self.edit_page_template,
                                                                              req.args.get('template', None)))
        return stream

    def _add_preview(self, req, render_url):
        scr_data = {'auto_preview_timeout': self.env.config.get('trac', 'auto_preview_timeout', '2.0'),
                    'form_token': req.form_token,
                    'ms_preview_renderer': render_url}
        add_script_data(req, scr_data)
        add_script(req, 'common/js/auto_preview.js')
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

    def create_templ_select_ctrl(self, templates, tmpl, cur_sel=None):
        """Create a selct control to be added to add milestone page or edit milestone page.

        :param templates: list of templates (wikipage names)
        :param tmpl: Genshi template to be used for creating the select control
        :param cur_sel: tempalte selected by the user of None if using description

        :return <div> tag holding a select control with label
        """
        sel = MarkupTemplate(tmpl)
        return sel.generate(templates=templates, sel=cur_sel)

    # IRequestFilter methods

    # IRequestFilter is used to add the template contents as description when adding from the roadmap page
    def pre_process_request(self, req, handler):

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
        if req.path_info.startswith('/milestone') and req.args.get('__FORM_TOKEN') == req.form_token:
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