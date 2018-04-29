import io
from xml.etree.cElementTree import XML
import zipfile

from trac.core import implements, Component
from trac.mimeview.api import IHTMLPreviewRenderer, ct_mimetype
from trac.util.html import tag

DOCX_MIME_TYPE = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
XLSX_MIME_TYPE = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
PPTX_MIME_TYPE = 'application/vnd.openxmlformats-officedocument.presentationml.presentation'
OFFICE_MIME_TYPES = {
    DOCX_MIME_TYPE: ['docx'],
    XLSX_MIME_TYPE: ['xlsx'],
    PPTX_MIME_TYPE: ['pptx'],
}
DOCX_NS = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
XLSX_NS = '{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'
PPTX_NS = '{http://schemas.openxmlformats.org/presentationml/2006/main}'
DRAW_NS = '{http://schemas.openxmlformats.org/drawingml/2006/main}'

class BasicOfficePreviewRenderer(Component):
    implements(IHTMLPreviewRenderer)

    def get_extra_mimetypes(self):
        return OFFICE_MIME_TYPES.items()

    def get_quality_ratio(self, mimetype):
        if mimetype in OFFICE_MIME_TYPES:
            return 5
        return 0

    def render(self, context, mimetype, content, filename=None, url=None):
        mimetype = ct_mimetype(mimetype)
        if mimetype == DOCX_MIME_TYPE:
            return self._render_docx(content)
        elif mimetype == XLSX_MIME_TYPE:
            return self._render_xlsx(content)
        elif mimetype == PPTX_MIME_TYPE:
            return self._render_pptx(content)

    def _render_docx(self, content):
        with self._zip(content) as zip:
            document = XML(zip.read('word/document.xml'))
        return tag.div(class_='basic-office-docx trac-content')([
            tag.p([
                tag.span(node.text)
                for node in paragraph.iter(DOCX_NS + 't')
                if node.text])
            for paragraph in document.iter(DOCX_NS + 'p')])

    def _render_xlsx(self, content):
        with self._zip(content) as zip:
            strings = XML(zip.read('xl/sharedStrings.xml'))
            sheet = XML(zip.read('xl/worksheets/sheet1.xml'))
        strings = [node.text for node in strings.iter(XLSX_NS + 't')]
        cols = set()
        rows = []
        for row_node in sheet.iter(XLSX_NS + 'row'):
            row = {}
            for cell_node in row_node.iter(XLSX_NS + 'c'):
                value_node = cell_node.find(XLSX_NS + 'v')
                value = ''
                if value_node is not None:
                    value = value_node.text
                    if cell_node.attrib.get('t') == 's':
                        value = strings[int(value)]
                column = ''.join(c for c in cell_node.attrib['r'] if c.isalpha())
                cols.add(column)
                row[column] = tag.td(value)
            rows.append(row)
        cols = sorted(cols, key=lambda head: (len(head), head))
        rows = [[row.get(col, tag.td('')) for col in cols] for row in rows]
        return tag.table(class_='basic-office-xlsx trac-content wiki')(
            tag.thead(tag.th(col) for col in cols),
            tag.tbody(tag.tr(row) for row in rows))

    def _render_pptx(self, content):
        slides = []
        with self._zip(content) as zip:
            while True:
                filename = 'ppt/slides/slide%s.xml' % (len(slides) + 1,)
                try:
                    slide = XML(zip.read(filename))
                except KeyError:
                    break
                slides.append(slide)
        return tag.div(class_='basic-office-pptx')([
            tag.div(class_='slide trac-content')([
                tag.p([
                    tag.span(node.text)
                    for node in paragraph.iter(DRAW_NS +'t')
                    if node.text])
                for paragraph in slide.iter(DRAW_NS + 'p')])
            for slide in slides])

    def _zip(self, content):
        return zipfile.ZipFile(io.BytesIO(content.read()))
