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
    parser.add_argument('xsdfile', type=str, help='XSD schema file')
    parser.add_argument('--depth', type=int, help='Recursive levels in plot', default=999)
    parser.add_argument('--top-element', type=str, help='Name of top element of plot')
    parser.add_argument('--stop-list', type=str, help='comma-separated list of element names where descent shall stop')
    parser.add_argument('--outfile', type=str, help='output file name')

    args = parser.parse_args()

    if not isfile(args.xsdfile):
        print >>stderr,'Error: Input file %s does not exist or is inaccessible' \
                                                    % args.xsdfile
        exit(-1)

    try:
        xsd2svg(args.xsdfile, args.outfile, 
                top_element=args.top_element, depth=args.depth,
                stop_list = args.stop_list.split(',') if args.stop_list else [])
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
    global _stop_list
    _stop_list = stop_list

    if not isfile(xsdfile):
        raise Xsd2SvgException('XSD file not found: ' + xsdfile)

    if outfile:
        xsdplot.set_outputfile(open(outfile, 'w'))
    if colours:
        xsdplot.set_colours(colours)

    schema = ET.parse(xsdfile).getroot()

    if top_element:
        elems = schema.findall(".//*[@name='%s']" % top_element)
        if len(elems) == 0:
            raise Xsd2SvgException('top-element %s not found in XSD' % top_element)
        if len(elems) > 1:
            raise Xsd2SvgException('More than one top-element named %s in XSD' % top_element)
        if elems[0].tag == '{http://www.w3.org/2001/XMLSchema}element':
            plot = parse_element(elems[0], depth)
        elif elems[0].tag == '{http://www.w3.org/2001/XMLSchema}complexType':
            plot = parse_complexType(elems[0], depth)
        else:
            raise Xsd2SvgException('top-element %s must be either xs:element or xs:complexType' % top-element)
    else:
        for e in schema.findall(
            '{http://www.w3.org/2001/XMLSchema}complexType'):
            plot = parse_complexType(e, depth)
    revinfo = get_revinfo(schema)
    xsdplot.output(plot, caption=revinfo)
    

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
    #print >>stderr,'get_restriction', elt.get('name', 'Unnamed')

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
                               elt_type
                               )
#    if depth <= 1 or (elt_name in stop_list):
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
