# Created by Noah Kantrowitz on 2007-04-02.
# Modified by Iker Jimenez on 2008-12-18. Based on a patch submited to
# http://trac-hacks.org/ticket/1920 by user kkas.
# Copyright (c) 2007 Noah Kantrowitz. All rights reserved.
# Copyright (c) 2008 Iker Jimenez. All rights reserved.

from trac.core import Component, implements
from trac.web.api import IRequestFilter

try:
    set = set
except NameError:
    from sets import Set as set

from api import HideValsSystem


class HideValsFilter(Component):
    """A filter to hide certain ticket field values."""

    implements(IRequestFilter)

    # IRequestFilter methods
    def pre_process_request(self, req, handler):
        return handler

    def post_process_request(self, req, template, data, content_type):
        if 'TRAC_ADMIN' in req.perm or \
                'TICKET_HIDEVALS' not in req.perm or \
                not req.path_info.startswith(('/newticket', '/ticket',
                                              '/query')) or \
                (template, data, content_type) == (None, None, None):
            # TRAC_ADMIN would have the filterer permissions by inheritance
            return template, data, content_type
        else:
            visible_fields = HideValsSystem(self.env).visible_fields(req)
            self.log.debug("visible_fields: %s", visible_fields)
            dont_filter = set(HideValsSystem(self.env).dont_filter)
            self.log.debug("dont_filter: %s", dont_filter)
            to_delete = []
            fields = data['fields']

            def filter_field(field):
                if field['options']:
                    opts = field['options']
                    valid_opts = visible_fields[field['name']]
                    opts_to_delete = []
                    for opt in opts:
                        if opt not in valid_opts:
                            opts_to_delete.append(opt)

                    for opt in opts_to_delete:
                        self.log.debug(
                            "HideValsFilter: '%s' option removed "
                            "from '%s' field", opt, field['name'])
                        opts.remove(opt)
                elif field['optgroups']:
                    groups = field['optgroups']
                    valid_opts = visible_fields[field['name']]
                    opts_to_delete = []
                    for grp in groups:
                        for opt in grp['options']:
                            if opt not in valid_opts:
                                opts_to_delete.append(opt)

                    for grp in groups:
                        for opt in opts_to_delete:
                            if opt in grp['options']:
                                self.log.debug(
                                    "HideValsFilter: '%s' option removed "
                                    "from '%s' field",
                                    opt, field['name'])
                                grp['options'].remove(opt)

            if req.path_info.startswith('/newticket') or \
                    req.path_info.startswith('/ticket'):
                for field in fields:
                    if (field.get('options') or field.get('optgroups')) and \
                            field['name'] not in dont_filter:
                        if field['name'] in visible_fields:
                            filter_field(field)
                        else:
                            # If there are no values for this user, remove
                            # the field entirely
                            # NOTE: Deleting in place screws up the
                            # iteration, so do it all afterwards.
                            to_delete.append(field)
                for field in to_delete:
                    self.env.log.debug(
                        "HideValsFilter: '%s' field removed", field['name'])
                    fields.remove(field)
            elif req.path_info.startswith('/query'):
                for field in fields.itervalues():
                    if (field.get('options') or field.get('optgroups')) and \
                            field['name'] not in dont_filter:
                        if field['name'] in visible_fields:
                            filter_field(field)
                        else:
                            # If there are no values for this user, remove
                            # the field entirely
                            # NOTE: Deleting in place screws up the
                            # iteration, so do it all afterwards.
                            to_delete.append(field['name'])
                for field_name in to_delete:
                    self.log.debug(
                        "HideValsFilter: '%s' field removed", field_name)
                    del fields[field_name]
            return template, data, content_type
