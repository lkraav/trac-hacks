# -*- coding: utf-8 -*-
#
# Copyright (C) 2016 Cinc
# All rights reserved.
#
# This software is licensed as described in the file COPYING.txt, which
# you should have received as part of this distribution.
#
# Author: Cinc
#

import unittest

__author__ = 'Cinc'
__copyright__ = "Copyright 2016"
__license__ = "BSD"



def suite():

    from tests.new_review import new_review_suite
    from tests.db import db_suite
    from tests.comment_callback import comment_callback_suite

    suite = unittest.TestSuite()
    suite.addTest(new_review_suite())
    suite.addTest(db_suite())
    suite.addTest(comment_callback_suite())

    return suite


if __name__ == '__main__':

    print("Test started...")
    unittest.main(defaultTest='suite')