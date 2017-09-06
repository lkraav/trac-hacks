"""
Copyright (C) 2008 Prognus Software Livre - www.prognus.com.br
Author: Diorgenes Felipe Grzesiuk <diorgenes@prognus.com.br>
"""

import os
import re
import shutil
import subprocess
import tempfile
import xml.sax.saxutils
from urllib import urlretrieve

from trac.config import Option
from trac.core import *
from trac.env import ISystemInfoProvider
from trac.mimeview.api import Context, IContentConverter
from trac.util import lazy
from trac.util.translation import _
from trac.wiki.formatter import format_to_html

EXCLUDE_RES = [
    re.compile(r'\[\[PageOutline([^]]*)\]\]'),
    re.compile(r'\[\[TracGuideToc([^]]*)\]\]'),
    re.compile(r'\[\[TOC([^]]*)\]\]'),
    re.compile(r'----(\r)?$\n^Back up: \[\[ParentWiki\]\]', re.M | re.I)
]


def tagattrfind(page, tag, attr, pos):
    tb_pos = page.find('<%s' % tag, pos)

    while tb_pos != -1:
        te_pos = page.find('>', tb_pos)
        tc_pos = page.find(attr, tb_pos, te_pos)

        if tc_pos != -1:
            return tb_pos, te_pos + 1

        tb_pos = page.find('<%s' % tag, te_pos + 1)

    return -1, -1


def wiki_to_pdf(text, env, req, tmp_dir, codepage):
    env.log.debug("WikiToPdf => Start function wiki_to_pdf")

    # Remove exclude expressions
    for r in EXCLUDE_RES:
        text = r.sub('', text)

    env.log.debug("WikiToPdf => Wiki input for WikiToPdf: %r", text)

    context = Context.from_request(req, resource='wiki',
                                   id=req.args.get('page', 'False'))
    page = format_to_html(env, context, text)

    page = page.replace('<img', '<img border="0"')
    page = page.replace('?format=raw', '')

    """I need improve this... Ticket #3427"""
    page = page.replace(
        '<a class="wiki" href="/' +
        env.config.get('wikitopdf', 'folder_name') +
        '/wiki/',
        '<a class="wiki" href="' +
        env.config.get('wikitopdf', 'link') +
        '/wiki/')

    page = page.replace('<pre class="wiki">',
                        '<table align="center" width="95%" border="1" '
                        'bordercolor="#d7d7d7">'
                        + '<tr><td bgcolor="#f7f7f7"><pre class="wiki">')
    page = page.replace('</pre>', '</pre></td></tr></table>')
    page = page.replace('<table class="wiki">',
                        '<table class="wiki" border="1" width="100%">')

    imgpos = page.find('<img')

    imgcounter = 0

    img_cache = {}
    while imgpos != -1:
        addrpos = page.find('src="', imgpos)
        theimg = page[addrpos + 5:]
        thepos = theimg.find('"')
        theimg = theimg[:thepos]
        if theimg[:1] == '/':
            basepath = os.path.commonprefix([env.href(), theimg.lstrip()])
            theimg = env.abs_href(theimg[len(basepath):])
        try:
            newimg = img_cache[theimg]
        except:
            # newimg = tmp_dir + '%(#)d_' %{"#":imgcounter} + \
            #          theimg[theimg.rfind('/')+1:]
            prefix = '%(#)d_' % {"#": imgcounter}
            file = tempfile.NamedTemporaryFile(mode='w', prefix=prefix,
                                               dir=tmp_dir)
            newimg = file.name
            file.close()
            theimg = xml.sax.saxutils.unescape(theimg)
            theimg = theimg.replace(" ", "%20")
            urlretrieve(theimg, newimg)
            img_cache[theimg] = newimg
            env.log.debug("The image is %s new image is %s", theimg,
                          newimg)
            imgcounter += 1
            page = (page[:addrpos + 5] + newimg +
                    page[addrpos + 5 + thepos:])
            imgpos = page.find('<img', addrpos)

    # Add center tags, since htmldoc 1.9 does not handle align="center"
    tablepos, tableend = tagattrfind(page, 'table', 'align="center"', 0)
    while tablepos != -1:
        endpos = page.find('</table>', tablepos)
        page = page[:endpos + 8] + '</center>' + page[endpos + 8:]
        page = page[:tablepos] + '<center>' + page[tablepos:]

        endpos = page.find('</table>', tablepos)
        tablepos, tableend = \
            tagattrfind(page, 'table', 'align="center"', endpos)

    # Add table around '<div class="code">'
    tablepos, tableend = tagattrfind(page, 'div', 'class="code"', 0)
    while tablepos != -1:
        endpos = page.find('</div>', tablepos)
        page = page[:endpos + 6] + '</td></tr></table></center>' + \
               page[endpos + 6:]
        page = page[:tableend] + \
               '<center><table align="center" width="95%" border="1" ' \
               'bordercolor="#d7d7d7"><tr><td>' + \
               page[tableend:]

        endpos = page.find('</div>', tablepos)
        tablepos, tableend = tagattrfind(page, 'div', 'class="code"', endpos)

    # Add table around '<div class="system-message">'
    tablepos, tableend = tagattrfind(page, 'div', 'class="system-message"', 0)
    while tablepos != -1:
        endpos = page.find('</div>', tablepos)
        page = page[:endpos + 6] + '</td></tr></table>' + page[endpos + 6:]
        page = page[:tableend] + \
               '<table width="100%" border="2" bordercolor="#dd0000" ' \
               'bgcolor="#ffddcc"><tr><td>' + \
               page[tableend:]

        endpos = page.find('</div>', tablepos)
        tablepos, tableend = \
            tagattrfind(page, 'div', 'class="system-message"', endpos)

    # Add table around '<div class="error">'
    tablepos, tableend = tagattrfind(page, 'div', 'class="error"', 0)
    while tablepos != -1:
        endpos = page.find('</div>', tablepos)
        page = page[:endpos + 6] + '</td></tr></table>' + page[endpos + 6:]
        page = page[:tableend] + \
               '<table width="100%" border="2" bordercolor="#dd0000" ' \
               'bgcolor="#ffddcc"><tr><td>' + page[tableend:]

        endpos = page.find('</div>', tablepos)
        (tablepos, tableend) = tagattrfind(page, 'div', 'class="error"',
                                           endpos)

    # Add table around '<div class="important">'
    tablepos, tableend = tagattrfind(page, 'div', 'class="important"', 0)
    while tablepos != -1:
        endpos = page.find('</div>', tablepos)
        page = page[:endpos + 6] + '</td></tr></table>' + page[endpos + 6:]
        page = page[:tableend] + \
               '<table width="100%" border="2" bordercolor="#550000" ' \
               'bgcolor="#ffccbb"><tr><td>' + \
               page[tableend:]

        endpos = page.find('</div>', tablepos)
        tablepos, tableend = tagattrfind(page, 'div', 'class="important"',
                                         endpos)

    meta = '<meta http-equiv="Content-Type" content="text/html; ' \
           'charset=%s"/>' % codepage
    css = ''
    if env.config.get('wikitopdf', 'css_file'):
        css = ('<link rel="stylesheet" href="%s" type="text/css"/>'
               % env.config.get('wikitopdf', 'css_file')).encode(codepage)

    page = '<html><head>' + meta + css + '</head><body>' + page + \
           '</body></html>'
    page = page.encode(codepage, 'replace')

    env.log.debug("WikiToPdf => HTML output for WikiToPdf in charset %s "
                  "is: %r", codepage, page)
    env.log.debug("WikiToPdf => Finish function wiki_to_pdf")

    return page


def html_to_pdf(env, tmp_dir, htmldoc_args, files, codepage):
    env.log.debug("WikiToPdf => Start function html_to_pdf")

    htmldoc_path = env.config.get('wikitopdf', 'htmldoc_path')

    os.environ['HTMLDOC_NOCGI'] = 'yes'

    args_string = ' '.join('--%s %s' % (arg, value or '') for arg, value
                           in htmldoc_args.iteritems() if value is not None)

    pfile, pfilename = tempfile.mkstemp('wikitopdf', dir=tmp_dir)
    os.close(pfile)

    cmd_string = '%s %s %s -f %s' \
                 % (htmldoc_path, args_string, ' '.join(files), pfilename)
    env.log.debug("WikiToPdf => Htmldoc command line: %s", cmd_string)
    os.system(cmd_string.encode(codepage))

    with open(pfilename, 'rb') as infile:
        out = infile.read()

    env.log.debug("WikiToPdf => Finish function html_to_pdf")

    return out


def htmldoc_version(env):
    # Check existence and version of HTMLDOC.
    htmldoc_path = env.config.get('wikitopdf', 'htmldoc_path')
    try:
        version = subprocess.Popen((htmldoc_path, '--version'),
                                   stdout=subprocess.PIPE).communicate()[0]
    except OSError, e:
        raise TracError(e)
    except:
        raise TracError("Unexpected error while checking version of HTMLDOC.")
    else:
        env.log.debug("Using HTMLDOC version %s", version)
    return version


class WikiToPdfPage(Component):
    """Convert Wiki pages to PDF using HTMLDOC (http://www.htmldoc.org/)."""
    implements(IContentConverter, ISystemInfoProvider)

    htmldoc_path = Option('wikitopdf', 'htmldoc_path', 'htmldoc', """
        Path to HTMLDOC binary.""")

    # IContentConverter methods
    def get_supported_conversions(self):
        yield ('pdf', 'PDF', 'pdf', 'text/x-trac-wiki', 'application/pdf', 7)

    def convert_content(self, req, input_type, text, output_type):

        codepage = self.env.config.get('trac', 'default_charset', 'utf-8')

        tmp_dir = tempfile.mkdtemp(prefix='tracwikitopdf-')
        page = wiki_to_pdf(text, self.env, req, tmp_dir, codepage)

        hfile, hfilename = tempfile.mkstemp('wikitopdf', dir=tmp_dir)
        os.write(hfile, page)
        os.close(hfile)

        htmldoc_args = {
            'webpage': '',
            'format': 'pdf14',
            'charset': codepage
        }
        htmldoc_args.update(dict(self.env.config.options('wikitopdf-page')))

        out = html_to_pdf(self.env, tmp_dir, htmldoc_args, [hfilename],
                          codepage)

        shutil.rmtree(tmp_dir)

        return out, 'application/pdf'

    # ISystemInfoProvider methods

    def get_system_info(self):
        yield 'HTMLDOC', self.htmldoc_version

    @lazy
    def htmldoc_version(self):
        try:
            version = htmldoc_version(self.env)
        except TracError:
            version = _("Executable not found or unexpected error")
        return version
