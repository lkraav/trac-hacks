#!/usr/bin/python

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
    parser.add_argument('--stop-at-element', type=str, help='XSD schema file')
    parser.add_argument('--begin-at-element', type=str, help='XSD schema file')
    parser.add_argument('--outfile', type=str, help='output file name')

    args = parser.parse_args()

    if not isfile(args.xsdfile):
        print >>stderr,'Error: Input file %s does not exist or is inaccessible' \
                                                    % args.xsdfile
        exit(-1)
    xsd2svg(args.xsdfile, args.outfile, args.begin_at_element, args.stop_at_element)


class FileNotFoundException(Exception):
    def __init__(self, msg):
        self.message = msg

def xsd2svg(xsdfile, outfile=None, begin_at_element=None, stop_at_element=None):
    if not isfile(xsdfile):
        raise FileNotFoundException('XSD file not found: ' + xsdfile)

    if outfile:
        xsdplot.set_outputfile(open(outfile, 'w'))
    schema = ET.parse(xsdfile).getroot()

    if begin_at_element:
        for e in schema.findall(
            ".//{http://www.w3.org/2001/XMLSchema}element[@name='%s']" % args.begin_at_element):
            #print >>stderr, 'AT TOP'
            plot = parse_element(e)
    else:
        for e in schema.findall(
            '{http://www.w3.org/2001/XMLSchema}complexType'):
            plot = parse_complexType(e)
    revinfo = get_revinfo(schema)
    xsdplot.output(plot, caption=revinfo)
    

def parse_complexType(cplx):
    #print >>stderr, 'complexType, name = %s' % cplx.get('name', 'None')
    cplx_plot = xsdplot.CplxType(typename=cplx.get('name', 'None'))
    substruct = None
    for e in cplx.findall('*'):
        if e.tag.split('}')[-1] in ['all','sequence','choice']:
            substruct = parse_structure(e)
    if substruct: cplx_plot.add_child(substruct);
    return cplx_plot

def parse_structure(struct):
    #print >>stderr,'parse_structure', struct.tag
    create_struct_plot = {'all' : xsdplot.All,
                          'sequence' : xsdplot.Sequence,
                          'choice' : xsdplot.Choice
                          }
    struct_plot = \
        create_struct_plot[struct.tag.split('}')[-1]] (struct.get('minOccurs'),
                                                       struct.get('maxOccurs')
                                                       )
#    struct_plot = \
#        xsdplot.Sequence (struct.get('minOccurs'),
#                          struct.get('maxOccurs')
#                          )
                                   
    elts = []
    for e in struct.findall('*'):
        if e.tag == '{http://www.w3.org/2001/XMLSchema}element':
            res = parse_element(e)
            if res: elts.append(res);

    for e in elts:
        struct_plot.add_child(e)
    return struct_plot

def child_attr(parent, namespace, tag,  attr):
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
                    minlen = child_attr(re, xs_ns, 'minLength', 'value')
                    maxlen = child_attr(re, xs_ns, 'maxLength', 'value')
                    mininc = child_attr(re, xs_ns, 'minInclusive', 'value')
                    maxinc = child_attr(re, xs_ns, 'maxInclusive', 'value')
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
    
def parse_element(elt):
    #print >>stderr,'parse_element', elt.get('name', 'Unnamed')
    elt_type = elt.get('type', None)
    if not elt_type:
        elt_type = get_restriction(elt)

    elt_plot = xsdplot.Element(elt.get('name', 'Unnamed'),
                               elt.get('minOccurs'),
                               elt.get('maxOccurs'),
                               elt_type
                               )
    for e in elt.findall('*'):
        if e.tag in ['{http://www.w3.org/2001/XMLSchema}complexType',
                     ]:
            elt_plot.add_child(parse_complexType(e))
    return elt_plot

def get_revinfo(xsd):
    for d in xsd.findall('.//'+xs_ns+'documentation'):
        if d.text.find('$Header') or d.text.find('$Revision'):
            return d.text


if __name__ == '__main__':
    main()
