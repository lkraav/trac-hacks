# -*- coding: utf-8 -*-

import re

from genshi.builder import tag

from trac.core import *
from trac.web import IRequestHandler
from trac.web.chrome import INavigationContributor, ITemplateProvider
from trac.admin import IAdminPanelProvider

from trac.env import open_environment

from intertrac import InterTrac

TICKET_CUSTOM = "ticket-custom"

ADMIN_PANEL_TRACDEP = u'Trac Dependency'
ADMIN_PANEL_INTERTRAC = "Inter Trac"
ADMIN_PANEL_CUSTOMFIELD = u'Custom Field'
ERROR_PROJECT_EXIST = 'Project already exists.'
ERROR_PROJECT_NOT_SEL = 'No intertrac setting selected'
LABEL_SUMMARY_TICKET = "Summary Ticket"
LABEL_DEPENDENCIES = "Dependencies"
LABEL_BASELINE_START = "Baseline start"
LABEL_BASELINE_FINISH = "Baseline finish"

class TracDependencyAdminWebUI(Component):
    implements(IAdminPanelProvider, ITemplateProvider)

    def __init__(self):
        self.intertrac = InterTrac(self.config)

    def customfield_panel_enable(self):
        dependencies_enabled = ( self.config.get( TICKET_CUSTOM, "summary_ticket") or \
                     self.config.get( TICKET_CUSTOM, "dependencies"))
        baseline_enabled = ( self.config.get( TICKET_CUSTOM, "baseline_start") or \
                     self.config.get( TICKET_CUSTOM, "baseline_finish"))
        return not(dependencies_enabled and baseline_enabled)

    # IAdminPanelProvider
    def get_admin_panels(self, req):
        if 'TRAC_ADMIN' in req.perm:
            # �Ǘ��p�l���Ɏ��̓�̃��j���[��ǉ����܂��D
            yield ('Dependency', ADMIN_PANEL_TRACDEP, 'intertrac', ADMIN_PANEL_INTERTRAC)
            if self.customfield_panel_enable():
                # �J�X�^���t�B�[���h�͒ǉ������������Ă��Ȃ����߁C�K�v��������Ε\�����܂���D
                yield ('Dependency', ADMIN_PANEL_TRACDEP, 'customfield', ADMIN_PANEL_CUSTOMFIELD)

    def render_admin_panel(self, req, cat, page, path_info):
        custom_field = (page == 'customfield')
        if req.method == 'POST':
            if req.args.get('add'):
                # �t�H�[���ɓ��͂��ꂽinterTrac�̐ݒ��ǉ����܂��D
                name = req.args.get('name')
                description = req.args.get('description')
                url = req.args.get('url')
                path = req.args.get('path')
                title = self.config.get('intertrac', name + '.title')
                if title: #�v���W�F�N�g�����łɑ��݂��Ă����ꍇ�̓G���[�ɂ���D
                    raise TracError(ERROR_PROJECT_EXIST)
                self.config.set('intertrac', name + '.title', description)
                self.config.set('intertrac', name + '.url', url)
                self.config.set('intertrac', name + '.path', path)
                self.config.set('intertrac', name + '.label', name)
                self.config.save();
                req.redirect(req.href.admin(cat, page))

            elif req.args.get('remove'):
                # �I�����ꂽinterTrac�̐ݒ���폜���܂��D
                sel = req.args.get('sel')
                if not sel:
                    raise TracError(ERROR_PROJECT_NOT_SEL)
                if not isinstance(sel, list):
                    sel = [sel]
                for name in sel:
                    self.config.remove('intertrac', name + '.title')
                    self.config.remove('intertrac', name + '.url')
                    self.config.remove('intertrac', name + '.path')
                    self.config.remove('intertrac', name + '.label')
                self.config.save();

            elif req.args.get('dependencies_create'):
                # �ˑ��֌W�̃J�X�^���t�B�[���h��ǉ����܂�
                self.config.set(TICKET_CUSTOM,"summary_ticket", "text")
                self.config.set(TICKET_CUSTOM,"summary_ticket.order", "50")
                self.config.set(TICKET_CUSTOM,"summary_ticket.label", LABEL_SUMMARY_TICKET)
                self.config.set(TICKET_CUSTOM,"dependencies", "text")
                self.config.set(TICKET_CUSTOM,"dependencies.order", "51")
                self.config.set(TICKET_CUSTOM,"dependencies.label", LABEL_DEPENDENCIES)
                self.config.save();

            elif req.args.get('baseline_create'):
                # ��v��֘A�̃J�X�^���t�B�[���h��ǉ����܂��D
                self.config.set(TICKET_CUSTOM,"baseline_start", "text")
                self.config.set(TICKET_CUSTOM,"baseline_start.order", "52")
                self.config.set(TICKET_CUSTOM,"baseline_start.label", LABEL_BASELINE_START)
                self.config.set(TICKET_CUSTOM,"baseline_finish", "text")
                self.config.set(TICKET_CUSTOM,"baseline_finish.order", "53")
                self.config.set(TICKET_CUSTOM,"baseline_finish.label", LABEL_BASELINE_FINISH)
                # TODO:�Ȃɂ��m�F�����ɒǉ����Ă��邾���Ȃ̂ł������������Ƃ���K�v������D
                calendar_fields = self.config.get( "decorator", "calendar_fields")
                self.config.set("decorator", "calendar_fields", calendar_fields + ",baseline_start,baseline_finish")
                self.config.save();

        dependencies_enabled = ( self.config.get( TICKET_CUSTOM, "summary_ticket") or \
                     self.config.get( TICKET_CUSTOM, "dependencies"))

        baseline_enabled = ( self.config.get( TICKET_CUSTOM, "baseline_start") or \
                     self.config.get( TICKET_CUSTOM, "baseline_finish"))

        intertracs = self.intertrac.project_information()

        return 'admin_intertrac.html',{'intertracs': intertracs, 
                                       'dependencies_enabled': dependencies_enabled, 
                                       'baseline_enabled': baseline_enabled,
                                       'custom_field': custom_field}
    
    #ITemplateProvider
    def get_templates_dirs(self):
        from pkg_resources import resource_filename
        return [resource_filename('tracdependency', 'templates')]
