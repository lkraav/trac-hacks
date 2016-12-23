# -*- coding: utf-8 -*-
#
# Copyright (C) 2009 Andrei Culapov <aculapov@optaros.com>
# Copyright (C) 2016 Ryan J Ollos <ryan.j.ollos@gmail.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

from __future__ import with_statement

import os
import re
import stat

from trac.admin.api import IAdminPanelProvider
from trac.config import BoolOption, ListOption, Option
from trac.core import Component, implements
from trac.util import as_bool, as_int
from trac.util.translation import _
from trac.versioncontrol.api import RepositoryManager
from trac.web.chrome import ITemplateProvider, add_notice, add_script, \
                            add_stylesheet, add_warning
from trac.wiki.formatter import wiki_to_html

from svnpolicies import api


class SVNPoliciesAdminPlugin(Component):
    """Admin panel for configuring policies implemented as SVN hooks.
    """

    valid_email_flag = None
    errors = False

    implements(IAdminPanelProvider, ITemplateProvider)

    svnpolicies_enabled = BoolOption('svnpolicies', 'svnpolicies_enabled',
        False, "Enable the svnpolicies plugin")

    email_enabled = BoolOption('svnpolicies', 'email.enabled', False,
        "Enable email notifications")

    email_list = ListOption('svnpolicies', 'email.list', '',
        "Comma separated list of email recipients")

    email_from_enabled = BoolOption('svnpolicies', 'email_from_enabled',
        False, "Enable one address email for all the emails sent.")

    email_from_address = Option('svnpolicies', 'email_from_address', '',
        "Email address from which to send all the emails.")

    email_prefix = Option('svnpolicies', 'email.prefix', '[PROJECT NAME]',
        "Subject prefix for email messages")

    email_attachment = BoolOption('svnpolicies', 'email.attachment', False,
        "Attach diff file with changes")

    email_attachment_limit = Option('svnpolicies', 'email.attachment_limit',
        '10000', "Maximium attachment size (in bytes)")

    email_subject_cx = BoolOption('svnpolicies', 'email_subject_cx', False,
        "Include the context of the commit in the subject.")

    log_message_required = BoolOption('svnpolicies', 'log_message.required',
        False, "Require log messages on commit")

    log_message_minimum = Option('svnpolicies', 'log_message.minimum', '3',
        "Minimum number of characters required in a log message")

    log_message_pattern = Option('svnpolicies', 'log_message.pattern', '',
        "Regex pattern to match for log message (example: ^ticket #[0-9]+)")

    commands_enabled = BoolOption('svnpolicies', 'commands.enabled', False,
        "Enable ticket management control commands in log messages")

    advanced_precommit_enabled = BoolOption('svnpolicies',
        'advanced_precomit_enabled', False,
        "It enables the advanced commands on precommit.")

    advanced_postcomit_enabled = BoolOption('svnpolicies',
        'advanced_postcomit_enabled', False,
        "It enables the advanced commands on postcommit.")

    advanced_precommit_file = Option('svnpolicies', 'advanced_precomit_file',
        '', """The path to the advanced commands file that will be
        processed by the server before svn commit.
        """)

    advanced_postcommit_file = Option('svnpolicies',
        'advanced_postcomit_file', '',
        """The path to the advanced commands file that will be processed
        by the server after svn commit.
        """)

    svn_property = BoolOption('svnpolicies', 'svn_property', False,
        "Enable only authors to update their own checkin comments.")

    readonly_repository = BoolOption('svnpolicies', 'readonly_repository',
        False, "If enabled then the repository will not permit commits.")

    # IAdminPanelProvider methods

    def get_admin_panels(self, req):
        if 'TRAC_ADMIN' in req.perm('admin', 'general/svnpolicies'):
            yield ('versioncontrol', _("Version Control"),
                   'svnpolicies', _("SVN Policies"))

    def render_admin_panel(self, req, cat, page, path_info):
        req.perm('admin', 'general/svnpolicies').require('TRAC_ADMIN')

        # Create hooks directory, if needed.
        env_hooks_path = self._get_env_hooks_path()
        if not os.path.isdir(env_hooks_path):
            os.mkdir(env_hooks_path)

        # Check to see if this is a help request.
        if req.method == 'GET' and as_bool(req.args.get('help')):
            wiki_help_file_path = api.get_resource_path('svnpolicies/README')
            with file(wiki_help_file_path) as fh:
                wiki_help = fh.read()
            return 'help_svnpolicies.html', {
                'wiki_help': wiki_to_html(wiki_help, self.env, req)
            }

        self.valid_email_flag = True
        self.errors = False
        pre_commit_advanced_text = ""
        post_commit_advanced_text = ""
        if req.method == 'POST':
            self._validate_bool_options(req)
            for option in ('email.list', 'email.prefix',
                           'email.attachment_limit',
                           'log_message.minimum',
                           'log_message.pattern',
                           'advanced_postcomit_content',
                           'advanced_precomit_content'):
                if option == 'log_message.pattern':
                    value = req.args.get(option)
                    if re.compile(value):
                        self.config.set('svnpolicies', option, value)
                    else:
                        self._add_warning(req,
                            "%s was not saved because %s is not a valid "
                            "python regex.", option, value)
                elif option == 'log_message.minimum':
                    value = as_int(req.args.get(option), None, min=0)
                    if value:
                        self.config.set('svnpolicies', option, value)
                    else:
                        self._add_warning(req,
                            "%s was not saved because %s is not a valid "
                            "python integer.", option, req.args.get(option))
                        self.config.set('svnpolicies', option, '')
                        self.config.set('svnpolicies', 'log_message.required',
                                        False)
                elif not self.valid_email_flag and option == 'email.list':
                    pass
                elif option == 'advanced_postcomit_content':
                    if self.email_enabled and \
                            req.args.get(option) != '' and \
                            self.advanced_postcomit_enabled:
                        hooks_path = self._get_env_hooks_path()
                        if hooks_path:
                            file_name = os.path.join(hooks_path,
                                                     'advanced-post-commit')
                            self.config.set('svnpolicies',
                                            'advanced_postcomit_file',
                                            file_name)
                            post_commit_advanced_text = req.args.get(option)
                        else:
                            self.config.set('svnpolicies',
                                            'advanced_postcomit_file', '')
                    else:
                        self.config.set('svnpolicies',
                                        'advanced_postcomit_file', '')
                        self.config.set('svnpolicies',
                                        'advanced_postcomit_enabled', 'false')
                elif option == 'advanced_precomit_content':
                    if self.log_message_required and \
                            req.args.get(option) != '' and \
                            self.advanced_precommit_enabled:
                        hooks_path = self._get_env_hooks_path()
                        if hooks_path:
                            file_name = os.path.join(hooks_path,
                                                     'advanced-pre-commit')
                            self.config.set('svnpolicies',
                                            'advanced_precomit_file',
                                            file_name)
                            pre_commit_advanced_text = req.args.get(option)
                        else:
                            self.config.set('svnpolicies',
                                            'advanced_precomit_file', '')
                    else:
                        self.config.set('svnpolicies',
                                        'advanced_precomit_file', '')
                        self.config.set('svnpolicies',
                                        'advanced_precomit_enabled', False)
                else:
                    self.config.set('svnpolicies', option,
                                    req.args.get(option))

            if not self.errors:
                self._save_settings(req)
                self._process_new_settings(req)
        else:
            # Add the content of the advanced files to the textareas.
            try:
                if os.path.isfile(self.advanced_postcommit_file):
                    with open(self.advanced_postcommit_file) as fh:
                        post_commit_advanced_text = fh.readlines()
                if os.path.isfile(self.advanced_precommit_file):
                    with open(self.advanced_precommit_file) as fh:
                        pre_commit_advanced_text = fh.readlines()
            except Exception, e:
                self.log.error(e, exc_info=True)
        # add the css and js files
        add_script(req, 'svnpolicies/js/tabs.js')
        add_stylesheet(req, 'svnpolicies/css/tabs.css')
        add_script(req, 'svnpolicies/js/svnpolicies.js')
        return 'admin_svnpolicies.html', {
            'config': self.config,
            'postcomit_advanced_text': post_commit_advanced_text,
            'precomit_advanced_text': pre_commit_advanced_text
        }

    # ITemplateProvider methods

    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('svnpolicies', resource_filename(__name__, 'htdocs'))]

    def get_templates_dirs(self):
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]

    # Internal methods

    def _add_warning(self, req, msg, *args):
        msg %= args
        add_warning(req, msg)
        self.log.warning(msg)
        self.errors = True

    def _save_settings(self, req):
        """Saves the changes settings in the trac ini file."""
        config = self.config['svnpolicies']
        registry = Option.registry
        old_registry = {}
        # get them out
        for option, value in config.options():
            key = 'svnpolicies', option
            old_registry[key] = registry.pop(key)

        self.config.save()
        # put them back
        for option, value in config.options():
            key = 'svnpolicies', option
            registry[key] = old_registry[key]

        add_notice(req, _("Your changes have been saved."))

    def _process_new_settings(self, req):
        """Processes the new settings found in the config."""
        # Create the post commit links.
        if self.svnpolicies_enabled and \
                self.email_enabled or self.commands_enabled:
            if self._add_post_commit_hook(req):
                add_notice(req, _("The post-commit file was generated"))
            else:
                self._add_warning(req,
                    "The post-commit file couldn't be generated")
        else:
            # Delete the hook symlinks because the feature is disabled.
            self._delete_hook_links('post-commit')
        # Create the pre-commit links.
        if self.svnpolicies_enabled and \
                self.log_message_required or \
                self.readonly_repository:
            if self._add_pre_commit_hook(req):
                add_notice(req, _("The pre-commit file was generated"))
            else:
                self._add_warning(req,
                    "The pre-commit file couldn't be generated")
        else:
            # Delete the hook symlinks because the feature is disabled.
            self._delete_hook_links('pre-commit')

        # Create the pre-commit advanced script.
        if self.svnpolicies_enabled and self.advanced_precommit_enabled:
            if self.advanced_precommit_file != '':
                if self._create_advanced_hook(
                        self.advanced_precommit_file,
                        req.args.get('advanced_precomit_content')):
                    add_notice(req, _("The advanced pre commit file was "
                                      "generated."))
                else:
                    self._add_warning(req,
                        "The advanced pre-commit file couldn't be generated.")
            else:
                self._add_warning(req,
                    "The advanced pre commit file couldn't be generated.")

        # Create the post-commit advanced script.
        if self.svnpolicies_enabled and self.advanced_postcomit_enabled:
            if self.advanced_postcommit_file != '':
                if self._create_advanced_hook(
                        self.advanced_postcommit_file,
                        req.args.get('advanced_postcomit_content')):
                    add_notice(req, _("The advanced post commit file was "
                                      "generated."))
                else:
                    self._add_warning(req,
                        "The advanced post commit file couldn't be "
                        "generated.")
            else:
                self._add_warning(req,
                    "The advanced post commit file couldn't be generated.")

        # Create the pre-revprop-change links.
        if self.svnpolicies_enabled and self.svn_property:
            if self._add_pre_revprop_change_hook(req):
                add_notice(req, "A pre-revprop-change file was generated")
            else:
                self._add_warning(req,
                    "The pre-revprop-change file couldn't be generated")
        else:
            # delete the hook symlinks because the feature is disabled
            self._delete_hook_links('pre-revprop-change')

    def _validate_bool_options(self, req):
        """Processes the boolean options received in a http request
        by post.
        """
        for option in ('readonly_repository',
                       'email.enabled',
                       'email_from_enabled',
                       'email.attachment',
                       'email_subject_cx',
                       'log_message.required',
                       'commands.enabled',
                       'svn_property',
                       'svnpolicies_enabled',
                       'advanced_precomit_enabled',
                       'advanced_postcomit_enabled'):
            self.log.debug("setting svnpolicies %s=%s", option,
                           req.args.get(option, 'false'))
            if option == 'email.enabled':
                if req.args.get('email.enabled', 'false') != 'false':
                    email_list = req.args.getlist('email.list')
                    if not email_list:
                        self.valid_email_flag = False
                    for email in email_list:
                        if email == '' or not api.validate_email(email):
                            self.valid_email_flag = False
                            break
                    if self.valid_email_flag:
                        self.config.set('svnpolicies', 'email.enabled',
                                        req.args.get('email.enabled',
                                                     'false'))
                        self.config.set('svnpolicies', 'email.list',
                                        req.args.get('email.list', ''))
                    else:
                        self._add_warning(req, "The email list is not valid.")
                else:
                    self.config.set('svnpolicies', 'email.enabled', "false")
                    self.config.set('svnpolicies', 'email.list', '')
            elif option == 'email_from_enabled':
                if req.args.get('email.enabled', 'false') != 'false':
                    email = req.args.get('email_from_address', 'false')
                    email_flag = req.args.get('email_from_enabled', False)

                    if email_flag and self.email_enabled:
                        if email != '' and api.validate_email(email):
                            self.config.set('svnpolicies', option,
                                            req.args.get(option, 'false'))
                            self.config.set('svnpolicies',
                                            'email_from_address', email)
                        else:
                            self._add_warning(req,
                                "The from email address is not valid.")
                    else:
                        self.config.set('svnpolicies', 'email_from_enabled',
                                        'false')
                        self.config.set('svnpolicies', 'email_from_address',
                                        '')

            elif option == 'advanced_postcomit_enabled':
                if not self.email_enabled or \
                        req.args.get(option, 'false') == 'false':
                    self._delete_file(self.advanced_postcommit_file)
                    self.config.set('svnpolicies', 'advanced_postcomit_file',
                                    '')
                    # set to false the value
                    self.config.set('svnpolicies', option, 'false')
                else:
                    self.config.set('svnpolicies', option,
                                    req.args.get(option, 'false'))
                    self.config.set('svnpolicies', 'advanced_postcomit_file',
                                    '')

            elif option == 'advanced_precomit_enabled':
                if not self.log_message_required or \
                                req.args.get(option, 'false') == 'false':
                    # delete the hook file
                    self._delete_file(self.advanced_precommit_file)
                    # delete the config file value
                    self.config.set('svnpolicies', 'advanced_precomit_file',
                                    '')
                    # set to false the value
                    self.config.set('svnpolicies', option, 'false')
                else:
                    self.config.set('svnpolicies', option,
                                    req.args.get(option, "false"))
                    self.config.set('svnpolicies', 'advanced_precomit_file',
                                    '')
            else:
                self.config.set('svnpolicies', option,
                                req.args.get(option, "false"))

    def _create_advanced_hook(self, file_name, file_content):
        """Creates a file in the trac hook directory."""
        # clean file content from windows cr character
        file_content = file_content.replace('\r', '')
        try:
            self._delete_file(file_name)
            with file(file_name, 'w') as fh:
                fh.write(file_content)
            os.chmod(file_name, stat.S_IRWXU)
        except Exception, e:
            self.log.error(e, exc_info=True)
            return False
        return True

    def _delete_file(self, file_name):
        """Deletes a file from the system."""
        try:
            if os.path.isfile(file_name):
                os.unlink(file_name)
                self.log.debug("delete the advanced hook file" + file_name)
                return True
        except Exception, e:
            self.log.error(e, exc_info=True)
            return False
        return False

    def _add_pre_revprop_change_hook(self, req):
        return self._add_hook('pre-revprop-change')

    def _add_pre_commit_hook(self, req):
        return self._add_hook('pre-commit')

    def _add_post_commit_hook(self, req):
        return self._add_hook('post-commit')

    def _get_svn_hooks_path(self):
        """Returns the path on the system where the svn server expects
        the hook file to be present. The trac configuration file
        provides the svn repository information.
        """
        repos = RepositoryManager(self.env).get_all_repositories().get('')
        is_svn = repos['type'] == 'svn' or \
                 not repos['type'] and \
                 self.config.get('trac', 'repository_type') == 'svn'
        if is_svn and os.path.exists(repos['dir']):
            return self._get_path_to_dir(repos['dir'], 'hooks')

    def _add_hook(self, name):
        svn_hooks_path = self._get_svn_hooks_path()
        env_hooks_path = self._get_env_hooks_path()
        if svn_hooks_path and env_hooks_path:
            self._delete_hook_links(name)
            return self._create_hook_links(name, svn_hooks_path,
                                           env_hooks_path)

    def _get_env_hooks_path(self):
        """Returns the path on the system where the svn server expects
        the hook file to be present. The trac configuration file
        provides the svn repository information.
        """
        return self._get_path_to_dir(self.env.path, 'hooks')

    def _get_path_to_dir(self, *dirs):
        path = os.path.join(*dirs)
        return os.path.normcase(os.path.realpath(path))

    def _delete_hook_links(self, link_name):
        """This method removes the symbolic links for `link_name`
        so that the hook is disabled.
        """

        # get the svn path
        svn_repository = self._get_svn_hooks_path()
        if not svn_repository:
            return False
        svn_hook = os.path.join(svn_repository, link_name)

        # get the trac environment path
        hooks_path = self._get_env_hooks_path()
        if not hooks_path:
            return False
        trac_hook = os.path.join(hooks_path, link_name)

        try:
            # test the parameters
            if not os.path.isdir(svn_repository) or \
                    not os.path.isdir(hooks_path):
                self.log.warning("the parameters are not directories")
                raise Exception()

            # Add link from generic post-commit file to trac environment
            if os.path.islink(trac_hook):
                os.unlink(trac_hook)
                self.log.debug("deleted the file: %s", trac_hook)
            # Add link from the trac environment to svn repository
            if os.path.islink(svn_hook):
                os.unlink(svn_hook)
                self.log.debug("deleted the file: %s", svn_hook)
        except Exception, e:
            self.log.error(e, exc_info=True)
            return False
        return True

    def _extract_the_hook_script(self, resource_name):
        """Extracts the required hook file from the zipped egg
        and returns the path to the unzipped file.
        """
        return api.get_hook_path(resource_name)

    def _create_hook_links(self, link_name, svn_hooks_path, env_hooks_path):
        """Create a symbolic links on the system. The method tries to
        create two symbolic links, one in the trac environment hooks
        directory and one in the svn repository hooks directory. The
        first link points to a generic script in the trac plugin and
        the second points to the first link. This mesh of links is
        created so that, at runtime, the trac.ini file can be found.
        """
        try:
            # test the parameters
            if not os.path.isdir(svn_hooks_path) or \
                    not os.path.isdir(env_hooks_path):
                self.log.warning("the parameters are not directories: %s %s",
                                 svn_hooks_path, env_hooks_path)
                raise Exception()
            # create the path to the generic hook file
            generic_script = self._extract_the_hook_script(link_name + '.py')

            if not os.path.isfile(generic_script):
                self.log.warning("the generic script %s isn't on the "
                                 "computed path", generic_script)
                raise Exception()

            # add link from generic post-commit file to trac environment
            env_link_path = os.path.join(env_hooks_path, link_name)
            os.symlink(generic_script, env_link_path)
            self.log.debug("created link %s to the generic script",
                           env_link_path)

            # add link from the trac environment to the svn repository
            svn_link_path = os.path.join(svn_hooks_path, link_name)
            os.symlink(env_link_path, svn_link_path)
            self.log.debug("created link %s to the trac environment link",
                           svn_link_path)
        except Exception, e:
            self.log.error(e, exc_info=True)
            return False
        return True
