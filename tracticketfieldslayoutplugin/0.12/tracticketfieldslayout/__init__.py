# -*- coding: utf-8 -*-
import pkg_resources
pkg_resources.require('Trac>=0.12,<1.4')
from trac.web.chrome import Chrome
if hasattr(Chrome, 'jenv'):
    raise pkg_resources.VersionConflict("Trac with Jinja2 isn't supported")
del pkg_resources, Chrome
