# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 Cinc
#
# License: 3-clause BSD
#


def get_filter_settings(req, context, name):
    """Get filter setting from request or session attribute. Delete filter
    from session when appropriate.

    This function works for checkbox controls. The parameter name must not
    resolve to a list in req.args.

    @param req: a Request object
    @param context: string, will be part of the session key
    @param name: string, will be part of the session key. It's the name of
                 the HTML form input.

    @returns: True if filter is activated, False else.

    The settings key is constructed the following way:
    "%s.filter.%s" % (context, name).
    """
    session_key = "%s.filter.%s" % (context, name)

    cur_filter = name if name in req.args else None
    if not cur_filter and req.session.get(session_key) == '1':
        cur_filter = name

    if 'smp_update' in req.args:
        if cur_filter in req.args:
            req.session[session_key] = '1'
        elif session_key in req.session:
            del req.session[session_key]
            cur_filter = None

    return cur_filter is not None


def get_list_from_req_or_session(req, context, name, default=None):
    """Extract the current filter settings from the request if available or
    use settings stored in session.

    Remarks:
    If the setting is stored as a list, a list is returned otherwise a
    unicode string.
    If default is a list and it is stored in the session data it will
    only be stored as a list if len > 1. If len == 1
    it is stored as a unicode string.

    @param req: a Request object
    @param context: string, will be part of the session key
    @param name: string, will be part of the session key
    @param default: returned value if no settings are found in the request
                    or session

    @returns a stored list of settings or a unicode string if the list
             contained only one item.

    The settings key is constructed the following way:
    "%s.filter.%s" % (context, name).
    """
    session_key = "%s.filter.%s" % (context, name)

    cur_filter = name if name in req.args else None
    session_data = req.session.get(session_key)

    if not cur_filter:
        if session_data:
            if session_data.endswith(',///,'):
                # V0.0.4 saved with trailing ',///,'
                session_data = session_data[:-5]
            cur_filter = name
        else:
            session_data = default
    else:
        session_data = req.args.getlist(name)  # This is a list

    if 'smp_update' in req.args:
        if cur_filter in req.args:
            session_data = ',///,'.join(req.args.getlist(name))
            req.session[session_key] = session_data
        elif session_key in req.session:
            del req.session[session_key]
            session_data = default

    # We deal with a saved list here
    if session_data and ',///,' in session_data:
            return session_data.split(',///,')

    return session_data


def get_project_filter_settings(req, context, name, default=None):
    """Extract the current project filter settings from the request
    if available or use settings stored in session.

    @param req: a Request object
    @param context: string, will be part of the session key
    @param name: string, will be part of the session key. Also name of
                 form control.
    @param default: returned value if no settings are found in the
                    request or session

    @returns setting as a list. Meant to ask for saved lists
    .
    Note that default is returned as a list even when default parameter
    is not a list.
    """
    filter_setting = get_list_from_req_or_session(req, context, name, default)

    if filter_setting and not isinstance(filter_setting, list):
        filter_setting = [filter_setting]

    return filter_setting
