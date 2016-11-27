# -*- coding: utf-8 -*-
#
# Copyright (C) 2014 Steffen Hoffmann <hoff.st@web.de>
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

import unittest
from trac.wiki.web_ui import WikiModule


def test_suite():
    suite = unittest.TestSuite()

    import tracdiscussion.tests.admin
    suite.addTest(tracdiscussion.tests.admin.test_suite())

    import tracdiscussion.tests.ajax
    suite.addTest(tracdiscussion.tests.ajax.test_suite())

    import tracdiscussion.tests.api
    suite.addTest(tracdiscussion.tests.api.test_suite())

    import tracdiscussion.tests.core
    suite.addTest(tracdiscussion.tests.core.test_suite())

    import tracdiscussion.tests.init
    suite.addTest(tracdiscussion.tests.init.test_suite())

    import tracdiscussion.tests.model
    suite.addTest(tracdiscussion.tests.model.test_suite())

    import tracdiscussion.tests.notification
    suite.addTest(tracdiscussion.tests.notification.test_suite())

    msg_fail = '%s not found: skipping tracdiscussion.tests.%s'
    try:
        import tracdiscussion.tests.spamfilter
    except ImportError:
        print(msg_fail % ('SpamFilter', 'spamfilter'))
    else:
        suite.addTest(tracdiscussion.tests.spamfilter.test_suite())

    try:
        import tracdiscussion.tests.tags
    except ImportError:
        print(msg_fail % ('TracTags', 'tags'))
    else:
        suite.addTest(tracdiscussion.tests.tags.test_suite())

    import tracdiscussion.tests.timeline
    suite.addTest(tracdiscussion.tests.timeline.test_suite())

    import tracdiscussion.tests.util
    suite.addTest(tracdiscussion.tests.util.test_suite())

    import tracdiscussion.tests.wiki
    suite.addTest(tracdiscussion.tests.wiki.test_suite())

    return suite


# Start test suite directly from command line like so:
#   $> PYTHONPATH=$PWD python tracdiscussion/tests/__init__.py
if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
