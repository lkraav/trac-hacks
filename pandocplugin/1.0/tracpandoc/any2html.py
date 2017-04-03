# -*- coding: utf-8 -*-
#
# Copyright (C) 2016 tkob <ether4@gmail.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

import tempfile, shutil, os
import pypandoc

from_formats, to_formats = pypandoc.get_pandoc_formats()


class Any2HtmlTemp:
    """Translate some format into HTML using pandoc through a temporary file."""
    def get_from(self):
        raise NotImplementedError('Use a subclass of Any2HtmlTemp instead')

    def get_tmpdir(self):
        return None

    def get_text(self):
        """True if the temporary file should be opened in text mode."""
        return False

    def is_available(self):
        return self.get_from() in from_formats

    def render(self, content):
        """ Render content as HTML. content should have read() method."""
        suffix = '.' + self.get_from()
        tmpdir = self.get_tmpdir()
        text = self.get_text()
        fd, temp_path = tempfile.mkstemp(suffix = suffix, dir = tmpdir, text = text)
        try:
            with os.fdopen(fd, 'w') as f:
                shutil.copyfileobj(content, f)
            output = pypandoc.convert_file(temp_path, 'html')
            return output
        finally:
            os.remove(temp_path)

class Docx2Html(Any2HtmlTemp):
    def get_from(self):
        return 'docx'
