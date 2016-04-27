# -*- coding: utf-8 -*-

from string import Template
from trac.admin import IAdminPanelProvider
from trac.config import ListOption
from trac.core import Component, implements
from trac.mimeview.api import IContentConverter, Mimeview
from trac.util.text import _
from trac.web.api import IRequestHandler
from trac.web.chrome import add_notice, add_warning
from model import ReviewDataModel

try:
    from docx import Document
    from docx_export import create_docx_for_review
    docx_support = True
except ImportError:
    docx_support = False


__author__ = 'Cinc'
__copyright__ = "Copyright 2016"
__license__ = "BSD"


class PeerReviewDocx(Component):
    """Export reviews as a document in Word 2010 format (docx).

    == Overview
    When enabled a download link (''Download in other formats'') for a Word 2010 document is added to
    review pages.
    The document holds all the information from the review page and the file content of each file.
    File comments are printed inline.

    It is possible to provide a default template document for new environments by providing the path
    in ''trac.ini'':
    [[TracIni(peer-review, review.docx)]]

    The path must be readable by Trac. It will be used only on first start to populate the database and is
    meant to make automated deploying easier.
    You may use the admin page to change it later on.

    == Template document format
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

    ListOption('peer-review', 'review.docx', doc=u"Path to template document in ''docx'' format used for generating "
                                                 u"review documents.")
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
                        data = self.env.config.get('peer-review', 'review.docx', '')
                    else:
                        data = u""
                    rdm = ReviewDataModel(self.env)
                    rdm['type'] = d
                    rdm['data'] = data
                    rdm.insert()
                    self.env.log.info("PeerReviewPlugin: added '%s' with value '%s' to 'peerreviewdata' table",
                                      d, data)

    # IAdminPanelProvider methods

    def get_admin_panels(self, req):
        if docx_support and 'CODE_REVIEW_MGR' in req.perm:
            yield ('codereview', 'Code review', 'reviewreport', 'Review Report')

    def render_admin_panel(self, req, cat, page, path_info):
        req.perm.require('CODE_REVIEW_MGR')

        report_data = self.get_report_defaults()

        if req.method=='POST':
            save = req.args.get('save', '')
            if save:
                # First check for ASCII only text
                try:
                    dummy = str(req.args.get('title', u''))
                    dummy = str(req.args.get('subject', u''))
                except UnicodeEncodeError:
                    add_warning(req, u"You can't use non ASCII characters like 'ü', 'ä', 'ö' in title or subject.")
                    req.redirect(req.href.admin(cat, page))

                report_data['reviewreport.title']['data'] = req.args.get('title', u'')
                report_data['reviewreport.title'].save_changes()
                report_data['reviewreport.subject']['data'] = req.args.get('subject', u'')
                report_data['reviewreport.subject'].save_changes()
                report_data['reviewreport.template']['data'] = req.args.get('template', u'')
                report_data['reviewreport.template'].save_changes()
                add_notice(req, _("Your changes have been saved."))
            req.redirect(req.href.admin(cat, page))

        data = {'title': report_data['reviewreport.title']['data'],
                'subject': report_data['reviewreport.subject']['data'],
                'template': report_data['reviewreport.template']['data']}
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
            Mimeview(self.env).send_converted(req,
                                              'text/x-trac-peerreview',
                                              review_id, format_arg, u"Review %s" % review_id)

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
        @param content: This is the review id
        """
        if mimetype == 'text/x-trac-peerreview':
            report_data = self.get_report_defaults()
            template = report_data['reviewreport.template']['data']
            tdata = {'reviewid': content}
            info = {'review_id': content,
                    'author': req.authname,
                    'title': Template(report_data['reviewreport.title']['data']).safe_substitute(tdata),
                    'subject': Template(report_data['reviewreport.subject']['data']).safe_substitute(tdata)}
            data = create_docx_for_review(self.env, info, template)
            return data, 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'

        return None # This will cause a Trac error displayed to the user
