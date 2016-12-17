# -*- coding: utf-8 -*-

import os
import site

_variables = None


def get_real_path(link, cut_by=2):
    """This function determines the real file that hides under symlinks.
    """
    hook_file = os.path.realpath(link)
    return os.path.sep.join(hook_file.split(os.path.sep)[:-cut_by])


def get_trac_path(link, cut_by=2):
    """This function determines the target of a symlink.
    """
    hook_file = os.readlink(link)
    return os.path.sep.join(hook_file.split(os.path.sep)[:-cut_by])


PYTHONPATH = ''
production = False
try:
    from svnpolicies import api
except ImportError:
    # Get the python path from the pth file and load site-packages.
    packages_pth = os.path.join(get_real_path(__file__, 1), 'packages.pth')
    with open(packages_pth) as fh:
        python_path = fh.readlines()
    for path in python_path:
        site.addsitedir(path.strip())
    PYTHONPATH = ':'.join(python_path)
    production = True
    from svnpolicies import api

AUTHOR_URL_TEMPLATE = api.get_global_configurations('AUTHOR_URL_TEMPLATE')
CHANGESET_URL = api.get_global_configurations('CHANGESET_URL')
SVNNOTIFY = api.get_global_configurations('SVNNOTIFY')
SVNLOOK = api.get_global_configurations('SVNLOOK')
SMTP_HOST = api.get_global_configurations('SMTP_HOST')
SMTP_USER = api.get_global_configurations('SMTP_USER')
SMTP_PASSWORD = api.get_global_configurations('SMTP_PASSWORD')
TRAC_ADMIN = api.get_global_configurations('TRAC_ADMIN')
CREDENTIALS = '-S' + \
              ' --smtp ' + SMTP_HOST + \
              ' --smtp-user ' + SMTP_USER + \
              ' --smtp-password ' + SMTP_PASSWORD
