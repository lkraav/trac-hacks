# -*- coding: utf-8 -*-

import os
from string import Template
from trac.admin import IAdminPanelProvider
from trac.config import PathOption
from trac.core import Component, implements
from trac.mimeview.api import IContentConverter, Mimeview
from trac.util.translation import _
from trac.web.api import IRequestHandler
from trac.web.chrome import add_notice, add_warning
from model import PeerReviewModel, ReviewDataModel

try:
    from docx import Document
    from docx_export import create_docx_for_review
    docx_support = True
except ImportError:
    docx_support = False


__author__ = 'Cinc'
__copyright__ = "Copyright 2016"
__license__ = "BSD"


def escape_chars(txt):
    repl = {u'ä': u'ae', u'ü': u'ue', u'ö': u'oe',
            u'ß': u'ss', u'(': u'', u')': u'',
            u'Ä': u'Ae', u'Ü': u'Ue', u'Ö': u'Oe'}
    for key in repl:
        txt = txt.replace(key, repl[key])
    return txt


class PeerReviewDocx(Component):
    """Export reviews as a document in Word 2010 format (docx).

    [[BR]]
    == Overview
    When enabled a download link (''Download in other formats'') for a Word 2010 document is added to
    review pages.
    The document holds all the information from the review page and the file content of each file.
    File comments are printed inline.

    It is possible to provide default template documents for new environments by providing the path
    in ''trac.ini'':
    {{{#!ini
    [peerreview]
    review.docx = path/to/report/template.docx
    filelist.docx = path/to/filelist/template.docx
    }}}
    The path must be readable by Trac. It will be used only on first start to populate the database and is
    meant to make automated deployment easier.
    You may use the admin page to change it later on.

    When no path is found in the database when trying to export a report the standard ''templates'' directory of the
    environment is used.

    == Template document format for reports
    Markers are used to signify the position where to add information to the document.

    The following is added to predefined tables:
    * Review info
    * Reviewer info
    * File info

    File contents with inline comments is added as text.

    === Review info table
    The table must have the following format.

    ||= Name =|| $REVIEWNAME$ ||
    ||= Status =|| $STATUS$ ||
    ||= ID =|| $ID$ ||
    ||= Project =|| $PROJECT$ ||
    ||= Author =|| $AUTHOR$ ||
    ||= Date =|| $DATE$ ||
    ||= Followup from =|| $FOLLOWUP$ ||
    [[BR]]
    Any formatting will be preserved. Note that the order of rows is not important. You may also omit
    rows.

    === Reviewer info table
    The table must have the following format.

    || $REVIEWER$ || ||

    You may add a header row:

    ||= Reviewer =||= Status =||
    || $REVIEWER$ || ||
    [[BR]]
    Formatting for headers will be preserved. Note that a predefined text style is used for the information
    added.

    === File info table

    ||= ID =||= Path =||= Hash =||= Revision =||= Comments =||= Status =||
    ||  || $FILEPATH$ ||  ||  ||  ||  ||
    [[BR]]
    === File content marker
    File content is added at the position marked by the paragraph ''$FILECONTENT$''.

    For each file a heading ''Heading 2'' with the file path is added.

    === Defining styles
    The plugin uses different paragraph styles when adding file contents with inline comments. If the styles are not
    yet defined in the template document they will be added using some defaults. You may use your own style definitions
    by defining a style in the document.

    The following styles are used:
    * ''Code'': for printing file contents
    * ''Reviewcomment'': for comments printed inline
    * ''Reviewcommentinfo'': information like author, date about an inline comment

    == Prerequisite
    The python package ''python-docx'' (https://python-docx.readthedocs.org/en/latest/index.html) must
    be installed. If it isn't available the feature will be silently disabled.
    """
    implements(IAdminPanelProvider, IContentConverter, IRequestHandler,)

    PathOption('peerreview', 'review.docx', doc=u"Path to template document in ''docx'' format used for generating "
                                                u"review documents. '''Note:''' this setting is only used during "
                                                u"first startup to make automated deployment easier.")
    PathOption('peerreview', 'filelist.docx', doc=u"Path to template document in ''docx'' format used for generating "
                                                  u" file list documents. '''Note:''' this setting is only used during "
                                                  u"first startup to make automated deployment easier.")

    def __init__(self):
        if not docx_support:
            self.env.log.info("PeerReviewPlugin: python-docx is not installed. Review report creation as docx is not "
                              "available.")
        else:
            # Create default database entries
            defaults = ['reviewreport.title', 'reviewreport.subject', 'reviewreport.template']
            rdm = ReviewDataModel(self.env)
            rdm.clear_props()
            rdm['type'] = "reviewreport.%"
            keys = [item['type'] for item in rdm.list_matching_objects(False)]
            for d in defaults:
                if d not in keys:
                    if d == 'reviewreport.template':
                        # Admins may set this value in trac.ini to specify a default which will be used on first
                        # start.
                        data = self.env.config.get('peerreview', 'review.docx', '')
                    else:
                        data = u""
                    rdm = ReviewDataModel(self.env)
                    rdm['type'] = d
                    rdm['data'] = data
                    rdm.insert()
                    self.env.log.info("PeerReviewPlugin: added '%s' with value '%s' to 'peerreviewdata' table",
                                      d, data)
            defaults = ['filelist.template']
            rdm = ReviewDataModel(self.env)
            rdm.clear_props()
            rdm['type'] = "filelist.%"
            keys = [item['type'] for item in rdm.list_matching_objects(False)]
            for d in defaults:
                if d not in keys:
                    if d == 'filelist.template':
                        # Admins may set this value in trac.ini to specify a default which will be used on first
                        # start.
                        data = self.env.config.get('peerreview', 'filelist.docx', '')
                    else:
                        data = u""
                    rdm = ReviewDataModel(self.env)
                    rdm['type'] = d
                    rdm['data'] = data
                    rdm.insert()
                    self.env.log.info("PeerReviewPlugin: added '%s' with value '%s' to 'peerreviewdata' table",
                                      d, data)

    def _get_template_path(self, template, default_tmpl='review_report.docx'):
        if not os.path.exists(template):
            self.log.info(u"Report template '%s' does not exist.", template)
            template = os.path.join(self.config.getpath('inherit', 'templates_dir', ''), default_tmpl)
            template = os.path.abspath(template)
        if not os.path.exists(template):
            self.log.info('No inherited templates directory. Using default templates directory.')
            template = os.path.join(self.env.templates_dir, default_tmpl)
            if not os.path.exists(template):
                template = 'No template found'
        return template

    # IAdminPanelProvider methods

    def get_admin_panels(self, req):
        if docx_support and 'CODE_REVIEW_MGR' in req.perm:
            yield ('codereview', 'Code review', 'reporttemplates', 'Report Templates')

    def render_admin_panel(self, req, cat, page, path_info):
        req.perm.require('CODE_REVIEW_MGR')

        report_data = self.get_report_defaults()
        filelist_data = self.get_filelist_defaults()

        if req.method=='POST':
            if req.args.get('save', ''):
                report_data['reviewreport.title']['data'] = req.args.get('title', u'')
                report_data['reviewreport.title'].save_changes()
                report_data['reviewreport.subject']['data'] = req.args.get('subject', u'')
                report_data['reviewreport.subject'].save_changes()
                report_data['reviewreport.template']['data'] = req.args.get('template', u'')
                report_data['reviewreport.template'].save_changes()
                add_notice(req, _("Your changes have been saved."))
            elif req.args.get('save_filelist', ''):
                filelist_data['filelist.template']['data'] = req.args.get('template', u'')
                filelist_data['filelist.template'].save_changes()
                add_notice(req, _("Your changes have been saved."))
            req.redirect(req.href.admin(cat, page))

        data = {'title': report_data['reviewreport.title']['data'],
                'subject': report_data['reviewreport.subject']['data'],
                'template': report_data['reviewreport.template']['data'],
                'template_valid': os.path.exists(report_data['reviewreport.template']['data']),
                'template_default': self._get_template_path(report_data['reviewreport.template']['data'] or ''),
                'filelist_template': filelist_data['filelist.template']['data'],
                'filelist_template_valid': os.path.exists(filelist_data['filelist.template']['data']),
                'filelist_default': self._get_template_path(filelist_data['filelist.template']['data'] or '',
                                                            'review_filelist.docx')
                }
        return 'admin_review_report.html', data

    def get_report_defaults(self):
        """
        @return: dict with default values. Key: one of [reviewreport.title, reviewreport.subject], value: unicode
        """
        rdm = ReviewDataModel(self.env)
        rdm.clear_props()
        rdm['type'] = "reviewreport%"
        d = {}
        for item in rdm.list_matching_objects(False):
            d[item['type']] = item
        return d

    def get_filelist_defaults(self):
        """
        @return: dict with default values. Key: one of [reviewreport.title, reviewreport.subject], value: unicode
        """
        rdm = ReviewDataModel(self.env)
        rdm.clear_props()
        rdm['type'] = "filelist%"
        d = {}
        for item in rdm.list_matching_objects(False):
            d[item['type']] = item
        return d

    # IRequestHandler methods

    def match_request(self, req):
        if not docx_support:
            return False
        return req.path_info == '/peerreview'

    def process_request(self, req):

        format_arg = req.args.get('format')
        review_id = req.args.get('reviewid', None)
        referrer=req.get_header("Referer")
        if review_id and format_arg == 'docx':
            review = PeerReviewModel(self.env, review_id)
            if review:
                def proj_name():
                    return review['project'] + u'_' if review['project'] and review['project'].upper() != 'MC000000' \
                        else u''
                def review_name():
                    return escape_chars(review['name'].replace(' ', '_'))
                doc_name = u"%sSRC-REV_%s_Review_%s_V1.0" % (proj_name(), review_name(), review_id)
            else:
                doc_name = u"Review %s" % review_id
            content_info = {'review_id': review_id,
                            'review': review}
            Mimeview(self.env).send_converted(req,
                                              'text/x-trac-peerreview',
                                              content_info, format_arg, doc_name)

        self.env.log.info("PeerReviewPlugin: Export of Review data in format 'docx' failed because of missing "
                          "parameters. Review id is '%s'. Format is '%s'.", review_id, format_arg)
        req.redirect(referrer)

    # IContentConverter methods

    def get_supported_conversions(self):
        if docx_support:
            yield ('docx', 'MS-Word 2010', 'docx', 'text/x-trac-peerreview',
                   'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 4)

    def convert_content(self, req, mimetype, content, key):
        """
        @param content: dict holding information about the review, see request processing code for more information
        """
        if mimetype == 'text/x-trac-peerreview':
            report_data = self.get_report_defaults()
            template = self._get_template_path(report_data['reviewreport.template']['data'] or '')

            review = content['review']
            # Data for title and subject templates
            tdata = {'reviewid': content['review_id'],
                     'review_name': review['name'],
                     'review_name_escaped': escape_chars(review['name'])}

            info = {'review_id': content['review_id'],
                    'review': review,
                    'author': review['owner'],
                    'title': Template(report_data['reviewreport.title']['data']).safe_substitute(tdata),
                    'subject': Template(report_data['reviewreport.subject']['data']).safe_substitute(tdata)}
            data = create_docx_for_review(self.env, info, template)
            return data, 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'

        return None # This will cause a Trac error displayed to the user
