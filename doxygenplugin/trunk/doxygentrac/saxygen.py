# -*- coding: utf-8 -*-
#
# Copyright (C) 2016 Emmanuel Saint-James <esj@rezo.net>
#

import xml.sax
import os
import re

class DoxygenTracHandler(xml.sax.ContentHandler):
    """
    A class using SAX for scanning the XML index produced by Doxygen.
    """

    to_where = ''
    to_date = ''
    to_multi = ''
    last_field_name = ''
    fields = {}
    multi = []

    def __init__(self, find, where, all, index):
        self.to_where = where
        self.to_date = os.path.getctime(index)
        self.to_multi = all
        self.to_find = find.replace('::', '\\')
        if all:
            self.to_find = re.compile(r'''%s''' % self.to_find)

    def characters(self, content):
        if self.last_field_name != "":
            self.fields[self.last_field_name] += content

    def startElement(self, name, attrs):
        if name == 'field':
            self.last_field_name = attrs['name']
            self.fields[self.last_field_name] = ''
        else: self.last_field_name = ''

    def endElement(self, name):
        if name == "doc":
            self.fields['occ'] = 0
            self.fields['target'] = ''
            self.fields['date'] = self.to_date
            for field in self.to_where:
                if not self.to_multi:
                    p = self.to_find == self.fields[field]
                else:
                    p = self.to_find.findall(self.fields[field])

                if p:
                    if '#' in self.fields['url']:
                        url, target = self.fields['url'].split('#', 2)
                        self.fields['url'] = url
                        self.fields['target'] = target
                    if not self.to_multi:
                        raise IndexFound(self.fields)
                    else:
                        self.fields['occ'] += len(list(set(p)))

            if self.fields['occ']:
                self.multi.append(self.fields)
            self.fields = {}
        elif name == "add" and self.to_multi:
            raise IndexFound(self.multi)
        elif self.last_field_name == 'keywords':
            # Doxygen produces duplicates in this field !
            self.fields['keywords'] = ' '.join(list(set(self.fields['keywords'].split(' '))))
        self.last_field_name = ''

class IndexFound(Exception):
    def __init__( self, msg ):
        Exception.__init__(self, msg)

def search_in_doxygen(file, name, where, multi, log):
        if not file:
            return {}
        parser = xml.sax.make_parser()
        parser.setContentHandler(DoxygenTracHandler(name, where, multi, file))
        res = {}
        try:
            parser.parse(file)
        except IndexFound, a:
            res = a.args[0]
        except xml.sax.SAXException, a:
           log.debug("SAX %s" % (a))
        return res
