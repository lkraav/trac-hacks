# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 Cinc
#
# License: 3-clause BSD
#
from trac.core import Interface


class IRoadmapDataProvider(Interface):
    """Extension point for preparing and filtering data used to create
    the roadmap page.
    """

    def add_data(self, req, data):
        """Add data to or remove data from the data dictionary. Returns
        the modified data dictionary.
        """

    def filter_data(self, req, data):
        """Filter the given data. returns the modified data dictionary."""
