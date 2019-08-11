# -*- coding: utf-8 -*-
# Copyright (c) 2019 Cinc
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

import unittest
from codereview.tests import comment_callback, db, new_review, \
    review_model, reviewfile_model, test_resource, test_reviewer, \
    test_reviewcomment, test_report


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(comment_callback.comment_callback_suite())
    suite.addTest(db.db_suite())
    suite.addTest(new_review.test_suite())
    suite.addTest(review_model.review_model_suite())
    suite.addTest(reviewfile_model.reviewfile_model_suite())
    suite.addTest(test_resource.test_suite())
    suite.addTest(test_reviewer.test_suite())
    suite.addTest(test_reviewcomment.test_suite())
    suite.addTest(test_report.test_suite())
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
