#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 Theodor Norup, theodor.norup@gmail.com
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

import sys
from sys import stderr

of = sys.stdout


def set_outputfile(f):
    global of
    of = f


left_margin = 5 # distance from boxes' left margin to text or glyph begin
font_height = 10
font_size = 4
bold_capital_font_size = 7

### SVG Style definitions #####################

svg_styles = {
'caption' : """
   font-size : 5px; 
   font-family : helvetica;
   font-style : italic; 
   font-weight : bold
   font-color : red;
""",
'cardinality' : """
   font-size : 5px; 
   font-family : helvetica;
   font-style : italic; 
   font-color : red;
""",
'typename' : """
   font-size : 6px; 
   font-family : helvetica;
""",
'elementname' : """
   font-size : 6px; 
   font-family : helvetica;
""",
'struct-glyph' : """
   font-size : 6px; 
   font-family : helvetica;
   font-weight : bold
""",
}

def styles2xml():
    styles = '\n'.join(['%s {\n%s\n}' % (name, defs) for (name, defs) in svg_styles.items()])
    of.write('<style type="text/css"><![CDATA[\n%s]]></style>' % styles)

### Display classes #########################

class Colours:
    element = '#D3D3D3' # X11: Light grey
    complextype = '#B3B3B3'
    container = '#FFFFFF' #'#F59EA0' # X11: Cadet blue
    stroke = '#2F4F4F' # X11: Dark slate blue

def set_colours(colours):
        Colours.element     = colours.get('element','#D3D3D3')
        Colours.complextype = colours.get('complextype', '#B3B3B3')
        Colours.container   = colours.get('container', '#FFFFFF')
        Colours.stroke      = colours.get('stroke', '#2F4F4F')

class Point(object):
    def __init__(self, x, y):
        self.x = x
        self.y = y

class Element(object):

    def __init__(self, name, minoccurs=None, maxoccurs=None, typename=''):
        #print >>stderr, 'Creating plot element, name = ', name
        self.name = name
        self.typename = typename
        self.children = []
        self.colour = Colours.element
        self.stroke = Colours.stroke
        self.x = None
        self.y = None
        self.w = None
        self.h = None
        self.cardinality_pos = Point(0,0)
        self.minoccurs = minoccurs
        self.maxoccurs = '&#8734;' if maxoccurs == 'unbounded' else maxoccurs
        self.borderstyle = '' if self.minoccurs != '0' else 'stroke-dasharray:4,1'
        self.textstyle = svg_styles['elementname']
        self.indent = len(name) * font_size # distance from left edge to children's left edge

    def add_child(self, element):
        self.children.append(element)
        return self

    def text_position(self):
        if self.children:
            return (self.x + left_margin, self.y + (font_height/2) + self.h/2 -3)
        else:
            return (self.x + left_margin, self.y + (font_height/2) + 1)

    def layout(self, x, y):
        """ Return (width,height) """
        self.x = x
        self.y = y
        y_padding = 10
        rhs = 3 # right-hand side
        x_pos = x + self.indent
        y_pos = y + y_padding
        max_child_w = 0
        for c in self.children:
            (cw, ch) = c.layout(x_pos, y_pos)
            y_pos = y_pos + ch + y_padding
            max_child_w = max(max_child_w, cw)
            #print max_child_w, cw
        self.h = y_pos - y
        self.w = max_child_w + self.indent + rhs
        self.cardinality_pos = Point(self.x+left_margin, self.y + self.h/2 + 10)
        return (self.w, self.h)

    def plot_cardinality(self):
        cardinality = \
            '%s&lt;%s..%s&gt;' % (self.typename + '  ' if self.typename else '',
                            str(self.minoccurs) if self.minoccurs else '?',
                            str(self.maxoccurs) if self.maxoccurs else '?')

        of.write('<text x="%d" y="%d" style="%s">%s</text>' \
                                  % (self.cardinality_pos.x, 
                                     self.cardinality_pos.y,
                                     svg_styles['cardinality'],
                                     cardinality
                                     )
                 )

    def plot(self):
        of.write('<rect x="%d" y="%d"  width="%d" height="%d" style="stroke:%s; fill: %s; %s"/>' % \
                     (self.x, self.y, self.w, self.h, self.stroke, 
                      self.colour, self.borderstyle)
                 )
        (tx, ty) = self.text_position()
        of.write('<text x="%d"  y="%d" style="%s">%s</text>' % \
                     (tx, ty, self.textstyle, self.name)
                 )
        self.plot_cardinality()
        for c in self.children:
            c.plot()

class CplxType(Element):
    def __init__(self, typename='', minoccurs=None, maxoccurs=None):
        super(CplxType,self).__init__(' ',
                                      minoccurs, maxoccurs)
        self.colour = Colours.complextype
        self.indent = len(' ') * font_size
        self.typename = typename

    def plot(self):
        super(CplxType, self).plot()
        of.write('<text x="%d"  y="%d" style="%s">complexType %s</text>' \
                        % (self.x+3,
                           self.y+6, 
                           svg_styles['typename'],
                           self.typename if self.typename else ''
                           )
                 )

class All(Element):
    def __init__(self, minoccurs=None, maxoccurs=None):
        glyph = 'ALL'
        super(All, self).__init__('ALL',
                                minoccurs, maxoccurs)
        self.colour = Colours.container
        self.indent = len('ALL') * bold_capital_font_size
        self.textstyle = svg_styles['struct-glyph']

        
    def layout(self, x, y):
        super(All, self).layout(x, y)
        self.cardinality_pos = Point(self.x+left_margin, self.y + self.h/2 + 8)
        return (self.w, self.h)

class Sequence(Element):
    def __init__(self, minoccurs=None, maxoccurs=None):
        glyph = 'SEQ'
        super(Sequence, self).__init__('SEQ',
                                minoccurs, maxoccurs)
        self.colour = Colours.container
        self.indent = len('SEQ') * bold_capital_font_size
        self.textstyle = svg_styles['struct-glyph']
        
    def layout(self, x, y):
        super(Sequence, self).layout(x, y)
        self.cardinality_pos = Point(self.x+left_margin, self.y + self.h/2 + 8)
        return (self.w, self.h)

class Choice(Element):
    def __init__(self, minoccurs=None, maxoccurs=None):
        glyph = 'CHOICE'
        super(Choice, self).__init__('CHOICE',
                                minoccurs, maxoccurs)
        self.colour = Colours.container
        self.indent = len('CHOICE') * bold_capital_font_size
        self.textstyle = svg_styles['struct-glyph']
        
    def layout(self, x, y):
        super(Choice, self).layout(x, y)
        self.cardinality_pos = Point(self.x+left_margin, self.y + self.h/2 + 8)
        return (self.w, self.h)


def output(xsd, caption=''):
    xsd.layout(0,0)

    of.write('<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">')
    #print '<defs>'
    #styles2xml()
    #print '</defs>'

    xsd.plot()
    if caption:
        of.write('<text x="%d"  y="%d" style="%s">%s</text>' %  \
                     (0, xsd.h+10, svg_styles['caption'], caption)
                 )
    of.write('</svg>\n')
    of.flush()

def main():
    H = Element('E0')
    H.add_child(Element('E1'))
    H.add_child(Element('E2').add_child(CplxType('sdrgs').add_child(Element('rightmost'))))
    all = All('')
    H.add_child(all)
    all.add_child(Element('AE1'))
    all.add_child(Element('AE2'))
    all.add_child(Element('AE3'))
    H.add_child(Element('E4',1,7))

    output(H)


if __name__ == '__main__':
    main()
