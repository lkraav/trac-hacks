# -*- coding: utf8 -*-
#
# Copyright (C) Cauly Kan, mail: cauliflower.kan@gmail.com
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

from trac.core import Component, implements
from CatagorizedFields import Catagory
from tracrpc.api import IXMLRPCHandler


class CatagorizedFieldsRPC(Component):
    implements(IXMLRPCHandler)

    def __init__(self):
        pass

    def xmlrpc_namespace(self):
        return 'catfields'

    def xmlrpc_methods(self):
        yield 'WIKI_VIEW', ((dict,),), self.getCatagories

    def getCatagories(self, req):

        catagories = {"_uncatagorized": Catagory('_uncatagorized', '')}

        catagories['_uncatagorized'].index = 0

        for opt_name, opt_value in self.config.options('catagorized-fields'):

            if not '.' in opt_name:

                catagories[opt_name] = Catagory(opt_name, opt_value)

            elif opt_name.split('.')[-1].startswith('hide_when_'):

                catagory_name, hide_condition = opt_name.split('.')

                catagories[catagory_name].hide_condition.setdefault(hide_condition[len('hide_when_'):], []) \
                    .extend(filter(lambda x: x != '', opt_value.strip().split(',')))

            elif opt_name.split('.')[-1] == 'index':

                catagory_name = opt_name.split('.')[0]

                catagories[catagory_name].index = int(opt_value)

        result = dict([(k, dict(v)) for k,v in catagories.items()])

        return result
