# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 Theodor Norup, theodor.norup@gmail.com
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

from trac.core import TracError
from trac.wiki.macros import WikiMacroBase
from trac.resource import Resource, get_resource_url
from trac.attachment import Attachment

from xsd2svg import xsd2svg, Xsd2SvgException

import os, hashlib
from string import strip

class XsdPlotMacro(WikiMacroBase):
    """
    Plot the data structure of an XSD schema file into an SVG/PNG-image; insert result into a wikipage or ticket.

Requires `convert` from [http://www.imagemagick.org ImageMagick], `convert` may fail on specific files.

The macro part of the code is a !PdfImg rip-off - thanks to https://trac-hacks.org/wiki/ursaw

== Examples:
{{{
[[XsdPlot(schema.xsd,width=400,page=100,caption="Page 100 from Book Example")]]
[[XsdPlot(source:repo/schema.xsd@10,width=600,caption="SVG-image from repository in version 10")]]
[[XsdPlot(source:repo/schema.xsd@10,width=600,stop-list=Element1|Element2|Element3)]]
[[XsdPlot(ticket:1:schema.xsd)]]
}}}


== Possible trac links for input files/resources:

||= Trac link =||= Alternatives =||= Comment              =||
|| wiki:        ||  !JustPageName || Wiki page attachment ||
|| ticket:      ||  !#1           || Ticket attachment    ||
|| source:      ||  browser,repos || File stored in subversion ||
|| file:        ||                || Local file. Path prefix read from `file.prepath` in trac.ini  ||


== XSD layout selectiveness control parameters:
||= Parameter =||= Value                 =||= Default =||
|| top-element || select specific top XSD element or complextype of plot || Value can be a single element/complextype name, a pipe-separated ('|') list of element/complextype names or '*' (meaning all top-level elements ||
|| depth       || maximum depth counted in elements || infinity ||
|| stop-list   || Pipe-separated list of XSD element names where recursive descent shall stop || empty ||


== Other parameters:
||= Parameter =||= Value                 =||= Default =||= Note =||
|| img-type    || 'png' or 'svg'          || svg       || case INsensitive ||
|| width       || width in pixel          || 600       || must be absolute value ||
|| caption     || Caption under image     || ''none''  ||       ||
|| label       || anchor to link to       ||           ||       ||
|| cache       || build once or each time || True      || time consumption or changing vector graphics  ||
|| align       || left|right              || nothing   ||       ||
"""


    ## Parameters inspired by LaTeX-includegraphics
    page   = 1
    width  = 400
    pdffile=None
    caption=None
    label  =None

    cache  =True
    align  =None


    def expand_macro(self, formatter, name, content):
        if not content:
            return ''

        ## Filenames
        self.filenamehash  = hashlib.sha224(content).hexdigest()
        self.images_folder = os.path.join(os.path.normpath(self.env.get_htdocs_dir()), 'xsd2svg-images')

        # Arguments
        self.formatter = formatter

        images_url = self.formatter.href.chrome('site', '/xsd2svg-images')

        if not os.path.exists(self.images_folder):
            self.env.log.debug('Creating directory ' + self.images_folder)
            os.mkdir(self.images_folder)
            if not os.access(self.images_folder, os.W_OK):
                raise TracError(self.images_folder + ' is not writable. UMASK problem??')

        self.get_configuration()
        self.parse_arguments(content)

        # generate PNG if not existing
        if not os.access('%s/%s.png' % (self.images_folder, self.filenamehash),
                         os.F_OK) or not self.cache:
            # human starts with page 1 ; convert with 0
            if self.page > 0:
                self.page -= 1
            
            cmd= "convert -density %d SVG:\"%s\" -limit area 0  -scale %s PNG:\"%s/%s.png\"" \
                 % (self.png_density, self.svginput , self.width,
                    self.images_folder, self.filenamehash)
            res = os.system(cmd)

            self.env.log.info('convert command:', cmd)

            if res > 0 :
                raise TracError("ImageMagick.convert(%s) exit code = %d, command=%s" % (self.wikilink, res, cmd))


        # start generate HTML-Output
        html_strg   = "\n <!-- XsdPlot  %s -->" %(self.url)

        # For Debug purpose
        # html_strg += "\n<br/>[[XsdPlot(%s)]]<br/>\n"%(content)

        lwitdh=int(self.width) + 3
        html_strg  += '\n <div style="border: 1px solid #CCCCCC;padding: 3px !important;width:%ipx ' \
                    %( lwitdh )
        if self.align:
            html_strg += ' ;float:%s'%(self.align)
        html_strg += ' " ' #close div

        if self.label:
            html_strg +=  ' id="%s"' %(self.label)

        # This is the Hover with "wikilink,page"
        if self.page > 1 :
            img_hover ="%s,%s"%(self.wikilink,self.page)
        else:
            img_hover ="%s"%(self.wikilink)

        html_strg  += '> \n  <a  style="padding:0; border:none"'
        if self.rawurl:
            html_strg  += ' href="%s" '%(self.rawurl)
        html_strg  += '>\n    <img style="border: 1px solid #CCCCCC;" title="%s" src="%s/%s.png" />\n  </a> ' \
             %(img_hover,images_url,self.filenamehash)

        if self.caption:
            html_strg += '\n  <div>%s</div>' %(self.caption)

        html_strg += '\n </div>\n <!-- End XsdPlot -->\n'
        return html_strg

    def get_configuration(self):
        def assert_valid_rgb(name):
            import re
            if not re.search('^#[a-fA-F0-9]{6,6}$', self.colours[name]):
                raise TracError(
                    'Colour configuration value not RGB (eg. #123DEF): %s = % s' \
                                    % (name, self.colours[name])) 

        self.colours = dict()
        self.colours['element']     = self.config.get('tracxsdplot', 
                                                      'colour.element', '#D3D3D3')
        self.colours['complextype'] = self.config.get('tracxsdplot', 
                                                      'colour.complextype', '#B3B3B3')
        self.colours['container']   = self.config.get('tracxsdplot', 
                                                      'colour.container', '#F59EA0')
        self.colours['stroke']      = self.config.get('tracxsdplot', 
                                                      'colour.stroke', '#2F4F4F')
        assert_valid_rgb('element')
        assert_valid_rgb('complextype')
        assert_valid_rgb('container')
        assert_valid_rgb('stroke')

        try:
            pd = int(self.config.get('tracxsdplot', 'png-density', '400'))
            if pd < 100 or pd > 1000:
                raise ValueError('value out of [100-1000] bounds')
            self.png_density = pd
        except ValueError, e:
            raise TracError('Illegal png-density config value: %s' % e)


    def extract_argument(self,argument):
        """
            input   'arg="aasd asdasd"'
            output  'aasd asdasd'
        """
        ret_strg = argument.split('=', 1)[1]
        # remove quotes
        ret_strg = strip(ret_strg, "\"'")
        return ret_strg


    def parse_arguments(self,content):
        """ parse arguments
          * see also ImageMacro Parse Arguments
        """
        # we expect the 1st argument to be a filename (filespec)
        args = content.split(',')
        if len(args) == 0:
            raise Exception("No argument.")

        # clean all "LaTeX" - Properties
        self.page        = 1
        self.width       = 400
        self.pdffile     = None
        self.img_type    = 'svg'
        self.caption     = None
        self.top_element = None
        self.depth       = 9999
        self.stop_list   = []
        self.label       = None
        self.cache       = True
        self.align       = None

        filespec = args[0]

        for arg in args[1:]:
            arg = arg.strip()
            if arg.startswith('img-type'):
                self.img_type = self.extract_argument(arg).lower()
            if arg.startswith('caption'):
                self.caption = self.extract_argument(arg)
            if arg.startswith('top-element'):
                self.top_element = self.extract_argument(arg)
            if arg.startswith('depth'):
                self.depth = int(self.extract_argument(arg))
            if arg.startswith('stop-list'):
                self.stop_list = self.extract_argument(arg).split('|')
            if arg.startswith('width'):
                self.width = self.extract_argument(arg)
            if arg.startswith('page'):
                self.page = int(self.extract_argument(arg))
            if arg.startswith('label'):
                self.label = self.extract_argument(arg)
            if arg.startswith('align'):
                self.align = self.extract_argument(arg)
            if arg.startswith('cache'):
                # strg -> boolean
                strg_cache = self.extract_argument(arg)
                self.cache = strg_cache.lower()  in ("yes", "true", "t", "1")

        self.env.log.debug("depth = %s", self.depth)
        self.env.log.debug("top-element = %s", self.top_element)
        self.env.log.debug("stop-list = %s", '&'.join(self.stop_list))

        parts = filespec.split(':')
        partszero_lower=parts[0].lower()

        ## Check for special Keys
        if partszero_lower in ('file'):
            self.parse_file(parts[1])
        else :
            # default trac options
            self.parse_trac(filespec)

        if self.img_type not in ['svg', 'png']:
            raise TracError('Img-type parameter must be either svg or png')


    def parse_trac(self,filespec):
        """
         Parse arguments like in the ImageMacro (trac/wiki/macros.py)
        """
        parts = filespec.split(':')

        url = raw_url =  None
        attachment = None
        if len(parts) == 3:  # realm:id:attachment-filename
            realm, id, filename = parts
            attachment = Resource(realm, id).child('attachment', filename)
        elif len(parts) == 2:
            # TODO howto Access the Subversion / Browser ...
            # FIXME: somehow use ResourceSystem.get_known_realms()
            #        ... or directly trac.wiki.extract_link
            from trac.versioncontrol.web_ui import BrowserModule
            try:
                browser_links = [res[0] for res in
                                 BrowserModule(self.env).get_link_resolvers()]
            except Exception:
                browser_links = []
                # TODO what to do with browserlinks...
            if parts[0] in browser_links:   # source:path
                ##  ['repos', 'export', 'source', 'browser']
                # TODO: use context here as well

                # set standard properties

                self.cache = False # No caching to handle new revisions
                self.svginput = "%s/%s" %(self.images_folder,self.filenamehash)
                self.url=url
                self.rawurl=raw_url
                self.wikilink=filespec
                realm, filename = parts
                rev = None
                if '@' in filename:
                    filename, rev = filename.split('@')
                url = self.formatter.href.browser(filename, rev=rev)
                raw_url = self.formatter.href.browser(filename, rev=rev, format='raw')

                from trac.versioncontrol.web_ui import get_existing_node
                from trac.versioncontrol import RepositoryManager

                if hasattr(RepositoryManager, 'get_repository_by_path'): # Trac 0.12
                    self.env.log.debug('Looking up repo for %s' % filename)
                    reponame, repo, res_path = RepositoryManager(self.env).get_repository_by_path(filename)
                else:
                    repo = RepositoryManager(self.env).get_repository(self.formatter.req.authname)
                obj = get_existing_node(self.formatter.req, repo, res_path, rev)
                svn_core_stream=obj.get_processed_content(keyword_substitution=True)

                import tempfile
                svnfile = tempfile.NamedTemporaryFile(bufsize=0, delete=False)
                svnfile.write(svn_core_stream.read())
                if os.path.getsize(svnfile.name) < 2:
                    raise TracError('Cannot read contents of SVN repo for ' + filename)

                self.env.log.debug("Plotting SVN file:%s -> %s", svnfile.name, self.svginput )

                try:
                    xsd2svg(svnfile.name, 
                            outfile     = self.svginput,
                            top_element = self.top_element, 
                            depth       = self.depth,
                            stop_list   = self.stop_list,
                            colours     = self.colours)
                except Xsd2SvgException, e:
                    raise TracError(e.message)

                return
                    #            else: # #ticket:attachment or WikiPage:attachment
            else : # #ticket:attachment or WikiPage:attachment
                # FIXME: do something generic about shorthand forms...
                realm = None
                id, filename = parts
                if id and id[0] == '#':
                    realm = 'ticket'
                    id = id[1:]
                else:
                    realm = 'wiki'
                if realm:
                    attachment = Resource(realm, id).child('attachment',
                                                           filename)

        elif len(parts) == 1: # it's an attachment of the current resource
            attachment = self.formatter.resource.child('attachment', filespec)
        else:
            raise TracError('No filespec given')
        if attachment and 'ATTACHMENT_VIEW' in self.formatter.perm(attachment):
            url = get_resource_url(self.env, attachment, self.formatter.href)
            raw_url = get_resource_url(self.env, attachment, self.formatter.href,
                                       format='raw')

        self.wikilink=filespec
        self.url=url
        self.rawurl=raw_url

        self.svginput=( Attachment(self.env,attachment) ).path
        self.env.log.debug("trac-Attachment  %r", self.svginput )


    def parse_file(self,rel_filename):
        """
        Display a (internal) file in the file system.

        To use the Resource 'file:' the following configuration must set!
    {{{
    [tracxsdplot]
    file.prepath = /relative/entry/directory
    file.preurl  = http://example.com/entrydir
    colour.element = #D3D3D3 
    colour.complextype = #B3B3B3
    colour.container = #F59EA0
    colour.stroke = #2F4F4F

    }}}
        """

        file_prepath = self.config.get('tracxsdplot', 'file.prepath',None)
        url_prepath  = self.config.get('tracxsdplot', 'file.preurl' ,None)
        self.env.log.debug("Location file with file_prepath %r", file_prepath )

        if not file_prepath :
            raise TracError ('Can\'t use Resource \'file:\' without configuration for xsdplot->file.prepath')

        self.wikilink="file:%s"%(rel_filename)

        if url_prepath:
            self.rawurl = self.url = '%s/%s'%( url_prepath , rel_filename)
        else:
            self.rawurl = self.url = None

        xsdinput = '%s/%s'%( file_prepath, rel_filename)

        self.env.log.debug("Plotting file system file: %s -> %s", xsdinput, self.svginput )

        try:
            xsd2svg(xsdinput, 
                    outfile     = self.svginput,
                    top_element = self.top_element, 
                    depth       = self.depth,
                    stop_list   = self.stop_list,
                    colours     = self.colours)
        except Xsd2SvgException, e:
            raise TracError(e.message)

        return
