#!/usr/bin/python
# -*- coding: utf-8 -*-
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution. The terms
# are also available at http://trac.edgewall.org/wiki/TracLicense.
#
#
# Based on the main plugins code, Christopher Lenz, and the original DiaView Macro from arkemp.
# Modified for use with Trac 0.11b and now includes Visio and compressed
# file support by robert.martin@arqiva.com
#
# Modified for use with Trac 1.0 and configurable output filters
# by jaroslav.benkovsky@nic.cz


import os
import re
import subprocess
from datetime import datetime
from PIL import Image

from genshi.builder import Element, tag
from trac.attachment import Attachment, AttachmentModule
from trac.config import BoolOption, Option
from trac.resource import Resource, get_resource_summary, get_resource_url
from trac.util.datefmt import to_utimestamp, utc
from trac.wiki.formatter import extract_link
from trac.util.html import escape
from trac.wiki.macros import WikiMacroBase


class DiaVisViewMacro(WikiMacroBase):
    """Embed a Dia as an png image in wiki-formatted text.
    Will automatically convert a Dia to a png file.
    The first argument is the filename, after which
    the horizontal width can be given separated by a comma, as
    can other image parmaeters to position it.  Will now also accept
    vdx format drawings, as well as compressed files.

    One can select one or more layers with the layers parameter and a
    dot separated list, e.g.
    [[(DiaVisView(myfile, layers=0.1.2)]]
    (which shows only layers 0, 1, and 2.

    Please see the image macro for more details on arguments.

    Dia's output filter can be set in trac config thus:

      [diavisview]
      output_filter = png-libart

    Or even:

      [diavisview]
      output_filter = svg
      extension = svg
      skip_width_check = true

    ''Adapted from the Image.py macro created by Shun-ichi Goto
    <gotoh@taiyo.co.jp>''
    """

    bin_path = Option('diavisview', 'bin_path', 'dia',
                      doc="Path to the dia executable")

    output_filter = Option('diavisview', 'output_filter', default='png',
                          doc='Dia output filter, usually should be one of png subfilters')

    extension = Option('diavisview', 'extension', default='png',
                          doc="""File extension of the rendered file. If you use output
                                to something else than png, set the extension accordingly.""")

    skip_width_check = BoolOption('diavisview', 'skip_width_check', default=False,
                          doc="""Do not check the width of existing rendered files.
                                This is useful if their format is not supported by PIL.""")

    # Regexps for parsing arguments

    filespec_re = re.compile('^[A-Za-z0-9][^/]*$')
    # NOTE: Allow only numbers as width, else t would not be possible to compare
    #   expected and actual width
    #size_re = re.compile('[0-9]+(%|px)?$')
    size_re = re.compile('[0-9]+$')
    attr_re = re.compile('(align|border|width|height|alt'
                         '|title|longdesc|class|id|usemap)=(.+)')
    quoted_re = re.compile("(?:[\"'])(.*)(?:[\"'])$")
    layers_re = re.compile("^[0-9]+(\.[0-9]+)*$")

    # WikiMacroBase methods

    def expand_macro(self, formatter, name, content):
         # args will be null if the macro is called without parenthesis.
        if not content:
            return ''
        # parse arguments
        # we expect the 1st argument to be a filename (filespec)
        args = content.split(',')
        if len(args) == 0:
            raise Exception("No argument.")
        filespec = args[0]

        # style information
        attr = {}
        style = {}
        link = ''
        width = None
        layers = None
        for arg in args[1:]:
            arg = arg.strip()
            if self.size_re.match(arg):
                if width:
                    raise Exception("Argument 'width' appears more than once.")
                width = arg
                attr['width'] = arg
                continue
            if arg == 'nolink':
                link = None
                continue
            if arg.startswith('link='):
                val = arg.split('=', 1)[1]
                elt = extract_link(self.env, formatter.context, val.strip())
                link = None
                if isinstance(elt, Element):
                    link = elt.attrib.get('href')
                continue
            if arg in ('left', 'right', 'top', 'bottom'):
                style['float'] = arg
                continue
            if arg.startswith('layers='):
                if layers:
                    raise Exception("Argument 'layers' appears more than once.")
                layers = arg.split('=', 1)[1]
                if not self.layers_re.match(layers):
                    raise Exception("Wrong layer list format, use dot separated list of integer numbers.")
            match = self.attr_re.match(arg)
            if match:
                key, val = match.groups()
                m = self.quoted_re.search(val) # unquote "..." and '...'
                if m:
                    val = m.group(1)
                if key == 'align':
                    style['float'] = val
                elif key == 'border':
                    style['border'] = ' %dpx solid' % int(val);
                else:
                    attr[str(key)] = val # will be used as a __call__ keyword

        # Got the args now do some processing

        if ':' in filespec:
            # fully qualified resource name
            realm, resource_id, filespec = filespec.split(':')
            attachment = Resource(realm, resource_id).child('attachment', filespec)
        else:
            attachment = formatter.resource.child('attachment', filespec)
            realm = formatter.resource.realm
            resource_id = formatter.resource.id

        if not self.filespec_re.match(filespec):
            self.env.log.info("Invalid filespec: %s", filespec)
            raise Exception("Invalid filespec")

        # FIXME: very suspect - if user has no permissions, url
        #   will not be defined
        if attachment and 'ATTACHMENT_VIEW' in formatter.perm(attachment):
            url = get_resource_url(self.env, attachment, formatter.href)
            description = get_resource_summary(self.env, attachment)

        dia_attachment = Attachment(self.env, realm, resource_id, filespec)
        dia_path = dia_attachment.path
        dia_filename = dia_attachment.filename

        #png_attachment = Attachment(self.env, realm, resource_id, filespec)
        out_type = self.config.get('diavisview', 'extension')
        png_ext = (('.' + layers) if layers else '') + '.' + out_type
        png_filename = os.path.splitext(dia_filename)[0] + png_ext
        png_path = Attachment._get_path(self.env.path, realm, str(resource_id), png_filename)
        png_url = url.replace(dia_filename, png_filename)

        self.env.log.debug('Source path: %s' % dia_path)
        self.env.log.debug('Output path: %s' % png_path)

        if len(description) <= 0:
            description = out_type.upper() + ' render of ' + dia_filename

        skip_width_check = self.config.get('diavisview', 'skip_width_check')

        self.env.log.debug('Getting file modification times.')
        try:
            dia_mtime = os.path.getmtime(dia_path)
        except Exception:
            raise Exception('File does not exist: %s', dia_path)

        existing_width = None
        try:
            png_mtime = os.path.getmtime(png_path)
        except Exception:
            png_mtime = 0
        else:
            if width and not skip_width_check:
                im = Image.open(png_path)
                try:
                    im = Image.open(png_path)
                except Exception, e:
                    self.env.log.info('Error checking original png file width for Dia = %s',e)
                    raise Exception('Error checking original png file width for Dia.')
                existing_width = unicode(im.size[0])  # Coerce to unicode to compare expected and actual width

        self.env.log.debug('Dia and %s file modification times: %s, %s', out_type, dia_mtime, png_mtime)
        self.env.log.debug('%s and requested widths: %s, %s', out_type, repr(existing_width), repr(width))

        if (dia_mtime > png_mtime) or (width and existing_width != width):
            self._render_dia_file(dia_path, png_path, width, layers)
            self._update_database(dia_attachment, png_path, png_filename, description)

            # This has been included in the hope it would help update
            # the current page being displayed, but no effect noticed

            # Reload the attachment
            png_attachment = Attachment(self.env, realm, resource_id, png_filename)
            for listener in AttachmentModule(self.env).change_listeners:
                listener.attachment_added(png_attachment)

        for key in ('title', 'alt'):
            if not key in attr:
                attr[key] = description
        if style:
            attr['style'] = '; '.join(['%s:%s' % (k, escape(v))
                                       for k, v in style.iteritems()])
        result = tag.img(src=png_url + "?format=raw", **attr)
        if link is not None:
            result = tag.a(result, href=link or url,
                           style='padding:2; border:none')

        return result


    def _render_dia_file(self, dia_path, png_path, width=None, layers=None):
        """Render DIA file to PNG.

        :param dia_path: path to source DIA file
        :param png_path: path to result PNG file
        :param width: specify PNG image width, else use Dia's default
        :param layers: period-separated list of layer numbers to render"""

        output_filter = self.config.get('diavisview', 'output_filter')

        try:
            diacmd = [self.bin_path, '--log-to-stderr',
                      '--filter=%s' % output_filter,
                      '--export=%s' % png_path, dia_path]
            if width:
                diacmd.insert(1, '--size=%dx' % int(width))
            if layers:
                diacmd.insert(1, '--show-layers=%s' % layers.replace(".", ","))
            self.env.log.info('Running Dia : %s', ' '.join(diacmd))
            rc = subprocess.call(diacmd)
            self.env.log.info('Exiting Dia : %d', rc)

        except Exception, e:
            self.env.log.info('Dia failed with exception= %s',e)
            raise Exception('Dia execution failed.')

        if os.path.getsize(png_path) == 0:
            self.env.log.warning('Dia created an empty file')
            os.unlink(png_path)
            raise Exception('Dia created an empty file.')



    def _update_database(self, png_attachment, png_path, png_filename, description):
        file_size = os.path.getsize(png_path)
        timestamp = to_utimestamp(datetime.utcfromtimestamp(os.path.getmtime(png_path)).replace(tzinfo=utc))

        # Based on attachment.py, insert
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        # if an entry exists, based on the columns:- type, id, and filename
        # then it needs updating, rather than creating
        cursor.execute("SELECT filename,description,size,time,author,ipnr "
                   "FROM attachment WHERE type=%s AND id=%s "
                   "AND filename=%s ORDER BY time",
                   (png_attachment.parent_realm, unicode(png_attachment.parent_id), png_filename))
        row = cursor.fetchone()
        if row:
            cursor.execute("UPDATE attachment SET size=%s, time=%s, description=%s, author=%s, ipnr=%s "
                           "WHERE type=%s AND id=%s AND filename=%s",
                           (file_size, timestamp, description, png_attachment.author, png_attachment.ipnr,
                            png_attachment.parent_realm, unicode(png_attachment.parent_id), png_filename))
            self.env.log.info('Updated attachment: %s by %s', png_filename, png_attachment.author)
        else:
            # Insert as new entry
            cursor.execute("INSERT INTO attachment VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
                    (png_attachment.parent_realm, png_attachment.parent_id, png_filename,
                        file_size, timestamp, description,
                        png_attachment.author, png_attachment.ipnr))
            self.env.log.info('New attachment: %s by %s', png_filename, png_attachment.author)

        db.commit()
        cursor.close()
