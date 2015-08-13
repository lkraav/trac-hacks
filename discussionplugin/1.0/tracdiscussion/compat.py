# -*- coding: utf-8 -*-
#
# Copyright (C) 2011 Edgewall Software
# Copyright (C) 2014 Steffen Hoffmann <hoff.st@web.de>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

try:
    from trac.util.text import exception_to_unicode
# Provide the function for compatibility (available since Trac 0.11.3).
except:
    def exception_to_unicode(e, traceback=False):
        """Convert an `Exception` to an `unicode` object.

        In addition to `to_unicode`, this representation of the exception
        also contains the class name and optionally the traceback.
        This replicates the Trac core function for backwards-compatibility.
        """
        message = '%s: %s' % (e.__class__.__name__, to_unicode(e))
        if traceback:
            from trac.util import get_last_traceback
            traceback_only = get_last_traceback().split('\n')[:-2]
            message = '\n%s\n%s' % (to_unicode('\n'.join(traceback_only)),
                                    message)
        return message

# Compatibility code for `ComponentManager.is_enabled`
# (available since Trac 0.12)
def is_enabled(env, cls):
    """Return whether the given component class is enabled.

    For Trac 0.11 the missing algorithm is included as fallback.
    """
    try:
        return env.is_enabled(cls)
    except AttributeError:
        if cls not in env.enabled:
            env.enabled[cls] = env.is_component_enabled(cls)
        return env.enabled[cls]
