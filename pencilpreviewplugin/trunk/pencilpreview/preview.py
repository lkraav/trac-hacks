# -*- coding: utf-8 -*-

import xml.dom.minidom

from genshi.core import Markup
from genshi.builder import tag

from trac.core import implements, Component
from trac.mimeview.api import IHTMLPreviewRenderer

class PencilPreviewRenderer(Component):
    """HTML preview for EvolusPencil .ep mockup files."""

    implements(IHTMLPreviewRenderer)

    def get_extra_mimetypes(self):
        return [('application/evoluspencil+xml', ['ep'])]
    
    def get_quality_ratio(self, mimetype):
        if mimetype == 'application/evoluspencil+xml':
            return 8
        return 0

    def render(self, context, mimetype, content, filename=None, url=None):
        doc = xml.dom.minidom.parseString(content.read())
        
        pages = doc.getElementsByTagName("Page")

        def getText(nodelist):
            rc = []
            for node in nodelist:
                if node.nodeType == node.TEXT_NODE:
                    rc.append(node.data)
            return ''.join(rc)
            
        def getProperty(page, name):
            props = page.getElementsByTagName("Property")
            for prop in props:
                if prop.getAttribute("name") == name:
                    return getText(prop.childNodes)

        def getContent(page):
            return ''.join(n.toxml() for n in page.getElementsByTagName("Content")[0].childNodes)
            
        def preventEmptyElementForm(page, elementName):
            """HTML does not like the short form for e.g. empty <div/> nodes and prefers <div></div> instead.
            However XML does not differentiate between these, so a trick has to be used to prevent the XML library from collapsing these.
            """
            for e in page.getElementsByTagName(elementName):
                if not e.childNodes:
                    e.appendChild(doc.createTextNode(u""))

        for page in pages:
            preventEmptyElementForm(page, 'div')

        return tag.div(
                    tag.div(
                        tag.h2(getProperty(page, "name")),
                        tag.svg(Markup(getContent(page)), width=getProperty(page, "width"), height=getProperty(page, "height")))
                    for page in pages)
