# -*- coding: utf-8 -*-
import re
from genshi.core import Markup
from genshi.builder import tag
from trac.resource import Resource
from trac.attachment import Attachment
from trac.mimeview.api import Mimeview
from trac.wiki.macros import WikiMacroBase
from trac.util.text import stripws 
from trac.wiki import Formatter
import StringIO
import logging


# Code based on:
# - [WikiMacros#Macrowitharguments WikiMacros]
# - includemacro/trunk/includemacro/macros.py from 
#   [https://trac-hacks.org/wiki/IncludeMacro IncludeMacro – Trac Hacks]
# - ImageMacro from trac/wiki/macros.py
# - trac/attachment.py
# TODO: I would like to include attachmetns of the following mime types too, but how to do it securely?:
# - application/x-python


class IncludeAttachmentMacro(WikiMacroBase):
    """Embed the text of an attachment in wiki-formated text.

    Currently only attachments of mime types starting with `text/` are accepted.

    The first argument is the file specification as `module:id:file`, where
    module can be either '''wiki''' or '''ticket''', to refer to the attachment
    named ''file'' of the specified wiki page or ticket.

    Examples:
    {{{
    IncludeAttachment(wiki:MyPage:attachment.txt)
    }}}

    {{{
    IncludeAttachment(ticket:42:somefile.c)
    }}}
    """

    revision = "$Rev$"
    url = "$URL$"

    _split_re = r'''((?:[^%s"']|"[^"]*"|'[^']*')+)'''
    _split_args_re = re.compile(_split_re % ',')
    _split_filespec_re = re.compile(_split_re % ':')
    _quoted_re = re.compile("(?:[\"'])(.*)(?:[\"'])$")
    _usage = 'usage: IncludeAttachment(realm:id:filename) e.g. IncludeAttachment(wiki:MyPage:attachment.txt)'

    def expand_macro(self, formatter, name, content):
        """Return the contents of an attachment formatted as HTML,
        syntax-highlighted according to its MIME type

        `name` is the actual name of the macro (IncludeAttachment)
        `content` are the parameters for the macro passed as realm:id:filename
          e.g. `wiki:MyPage:attachment.txt` or `ticket:42:somefile.c`.
        """

        # args will be null if the macro is called without parenthesis.
        if not content:
            return self._usage
        # parse arguments
        # we expect the 1st argument to be a filename (filespec)
        args = [stripws(arg) for arg
                             in self._split_args_re.split(content)[1::2]]
        # strip unicode white-spaces and ZWSPs are copied from attachments
        # section (#10668)
        filespec = args.pop(0)

        if self._quoted_re.match(filespec):
            filespec = filespec.strip('\'"')
        # parse filespec argument to get realm and id if contained.
        parts = [i.strip('''['"]''')
                 for i in self._split_filespec_re.split(filespec)[1::2]]

        if not parts or len(parts) != 3:
                return self._usage

        realm, id, filename = parts

        resource = Resource(realm, id).child('attachment', filename)
        if 'ATTACHMENT_VIEW' not in formatter.perm(resource):
                logging.warn('%s: no ATTACHMENT_VIEW permission for %s' % (name, filename))
                return ''
        attachment = Attachment(self.env, resource)

        with attachment.open() as fd:
                mimeview = Mimeview(self.env)

                # MIME type detection
                str_data = fd.read(1000)
                fd.seek(0)

                mime_type = mimeview.get_mimetype(attachment.filename, str_data)
                if not mime_type.startswith('text/'):
                    logging.warn('%s: attachment mime type not supported: %s' % (name, mime_type))
                    return ''
#                if 'charset=' not in mime_type:
#                       charset = mimeview.get_charset(str_data, mime_type)
#                       mime_type = mime_type + '; charset=' + charset
#               text = mime_type or 'NONE'

                text = fd.read()

        text = '{{{\n#!'+mime_type+'\n'+text+'\n}}}'

        out = StringIO.StringIO()
        Formatter(self.env, formatter.context).format(text, out)
        return Markup(out.getvalue())
