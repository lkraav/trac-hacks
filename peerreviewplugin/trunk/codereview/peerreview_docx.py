# -*- coding: utf-8 -*-

from trac.core import Component, implements
from trac.mimeview.api import IContentConverter, Mimeview
from trac.web.main import IRequestHandler
try:
    from docx import Document
    from docx_export import create_docx_for_review
    docx_support = True
except ImportError:
    docx_support = False

# from docx_export import

__author__ = 'Cinc'
__copyright__ = "Copyright 2016"
__license__ = "BSD"


class PeerReviewDocx(Component):

    implements(IContentConverter, IRequestHandler,)

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
            data = create_docx_for_review(self.env, content) # create_docx_from_testcases(self.env, req.authname, content)
            return data, 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'

        return None # This will cause a Trac error displayed to the user
