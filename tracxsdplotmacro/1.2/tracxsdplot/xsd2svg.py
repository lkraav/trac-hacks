#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 Theodor Norup, theodor.norup@gmail.com
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

import os, sys
from sys import stderr
from os.path import dirname,realpath,isfile,basename
from argparse import ArgumentParser
import xml.etree.ElementTree as ET

import xsdplot

xs_ns = '{http://www.w3.org/2001/XMLSchema}'

img = xsdplot.Element('top')

def main():
    parser = ArgumentParser('xsd2svg')
    parser.add_argument('xsdfile', type=str, 
                        help='XSD schema file')
    parser.add_argument('--depth', type=int, 
                        help='Recursive levels in plot', default=999)
    parser.add_argument('--top-element', type=str, 
                        help='Pipe-separated list of top element names to plot. Or "*"')
    parser.add_argument('--stop-list', type=str, 
                        help='Pipe-separated list of element names where descent shall stop')
    parser.add_argument('--outfile', type=str, 
                        help='output file name')

    args = parser.parse_args()

    if not isfile(args.xsdfile):
        print >>stderr,'Error: Input file %s does not exist or is inaccessible' \
            % args.xsdfile
        exit(-1)

    try:
        xsd2svg(args.xsdfile, 
                args.outfile, 
                top_element=args.top_element, 
                depth=args.depth,
                stop_list = args.stop_list.split('|') if args.stop_list else [])
    except Xsd2SvgException, e:
        print >>sys.stderr, 'ERROR:', e.message
        exit(-1)


class FileNotFoundException(Exception):
    def __init__(self, msg):
        self.message = msg

class Xsd2SvgException(Exception):
    def __init__(self, msg):
        self.message = msg

_stop_list = []
def xsd2svg(xsdfile, outfile=None, 
            depth=999, top_element=None, stop_list=[], 
            colours=None):

    def _get_all_top_elements(schema, param):
        """ Return a list of all top_level XML entities whose name
        appears in *param*
        :param schema: a parsed XML/XSD
        :type schema:  DOM tree
        :param param: Pipe-separated list of elements to plot. Or '*'
        :type param: string
        :rtype: List of DOM objects
        """

        all = [e for e in schema.findall(
                '{http://www.w3.org/2001/XMLSchema}element[@name]')] \
            + [e for e in schema.findall(
                '{http://www.w3.org/2001/XMLSchema}complexType[@name]')]
        all_names = [e.attrib['name'] for e in all]
        if param == '*' or param is None:
            return [e for e in all]

        # Now, search the whole tree in depth and see if any name matches
        # the contents of param
        param = param.split('|')
        all = [e for e in schema.findall(
                './/{http://www.w3.org/2001/XMLSchema}element[@name]')] \
            + [e for e in schema.findall(
                './/{http://www.w3.org/2001/XMLSchema}complexType[@name]')]
        all_names = [e.attrib['name'] for e in all]

        missing = [p for p in param if p not in all_names]
        if missing:
            raise Xsd2SvgException(
                'One or more top-elements missing from XSD: %s' % missing
                )
        return [e for e in all if e.attrib['name'] in param]
    
    global _stop_list
    _stop_list = stop_list

    if not isfile(xsdfile):
        raise Xsd2SvgException('XSD file not found: ' + xsdfile)

    if outfile:
        xsdplot.set_outputfile(open(outfile, 'w'))
    if colours:
        xsdplot.set_colours(colours)

    xsdplot.init()

    schema = ET.parse(xsdfile).getroot()

    for t in _get_all_top_elements(schema, top_element):
        elems = schema.findall(".//*[@name='%s']" % top_element)
        if t.tag == '{http://www.w3.org/2001/XMLSchema}element':
            xsdplot.add_plot(parse_element(t, depth))
        elif t.tag == '{http://www.w3.org/2001/XMLSchema}complexType':
            xsdplot.add_plot(parse_complexType(t, depth))
        else:
            raise Xsd2SvgException(
                'top-element %s must be either xs:element or xs:complexType' \
                    % top-element)

    revinfo = get_revinfo(schema)
    xsdplot.output(caption=revinfo)
    

def parse_complexType(cplx, depth):
    cplx_plot = xsdplot.CplxType(typename=cplx.get('name', None))
    substruct = None
    for e in cplx.findall('*'):
        if e.tag.split('}')[-1] in ['all','sequence','choice']:
            substruct = parse_structure(e, depth)
    if substruct: cplx_plot.add_child(substruct);
    return cplx_plot

def parse_structure(struct, depth):
    #print >>stderr,'parse_structure', struct.tag
    create_struct_plot = {'all' : xsdplot.All,
                          'sequence' : xsdplot.Sequence,
                          'choice' : xsdplot.Choice
                          }
    struct_plot = \
        create_struct_plot[struct.tag.split('}')[-1]] (struct.get('minOccurs'),
                                                       struct.get('maxOccurs')
                                                       )
    elts = []
    for e in struct.findall('*'):
        if e.tag == '{http://www.w3.org/2001/XMLSchema}element':
            res = parse_element(e, depth)
            if res: elts.append(res);

    for e in elts:
        struct_plot.add_child(e)
    return struct_plot

def get_child_attr(parent, namespace, tag,  attr):
    """ return ATTR of first immediate child of PARENT tagged with NAMESPACE:TAG
    """
    for c in parent.findall('*'):
        if c.tag == namespace+tag:
            return c.get(attr, '')
    return ''

def get_restriction(elt):
    """Pretty-print xs:simpleType.xs:restriction """

    for st in elt.findall('*'):
        if st.tag in ['{http://www.w3.org/2001/XMLSchema}simpleType',
                     ]:
            for re in st.findall('*'):
                if re.tag in [xs_ns+'restriction',
                             ]:
                    minlen = get_child_attr(re, xs_ns, 'minLength', 'value')
                    maxlen = get_child_attr(re, xs_ns, 'maxLength', 'value')
                    mininc = get_child_attr(re, xs_ns, 'minInclusive', 'value')
                    maxinc = get_child_attr(re, xs_ns, 'maxInclusive', 'value')
                    size = ''
                    try:
                        if minlen and maxlen:
                            size = ' [%s..%s]' % (minlen, maxlen)
                        elif mininc and maxinc:
                            size = ' [%s-%s]' % (mininc, maxinc)
                    except:
                        size = 'Non-integer size data'
                    return re.get('base', 'No restriction base type') + size
    return ''
    
def parse_element(elt, depth):
    #print >>stderr,'parse_element', elt.get('name', 'Unnamed')
    stop_descent = False
    elt_name = elt.get('name', 'Unnamed')
    if depth <= 1 or (elt_name in _stop_list):
        elt_name += ' ...'
        stop_descent = True

    elt_type = elt.get('type', None)

    if not elt_type:
        elt_type = get_restriction(elt)

    elt_plot = xsdplot.Element(elt_name,
                               elt.get('minOccurs'),
                               elt.get('maxOccurs'),
                               typename=elt_type
                               )
    if stop_descent:
        return elt_plot

    for e in elt.findall('*'):
        if e.tag in ['{http://www.w3.org/2001/XMLSchema}complexType',
                     ]:
            elt_plot.add_child(parse_complexType(e, depth-1))
    return elt_plot

def get_revinfo(xsd):
    for d in xsd.findall('.//'+xs_ns+'documentation'):
        if d.text.find('$Header') or d.text.find('$Revision'):
            return d.text


if __name__ == '__main__':
    main()
