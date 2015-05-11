# -*- coding: utf-8 -*-

import os
import urllib

from trac.admin.api import IAdminPanelProvider
from trac.config import BoolOption
from trac.core import Component, implements
from trac.perm import PermissionSystem
from trac.util.translation import _
from trac.versioncontrol import RepositoryManager
from trac.web.chrome import ITemplateProvider, add_notice, add_warning

from io import AuthzFile
from model import Group, Path, PathAcl, User


class SvnAuthzAdminPage(Component):

    implements(IAdminPanelProvider, ITemplateProvider)

    show_all_repos = BoolOption('svnauthzadmin',
        'show_all_repos', False,
        """Enabling this option will allow the Trac project to view
        the entire contents of the SVN trac|authz_file.""")

    read_only_display = BoolOption('svnauthzadmin',
        'read_only_display', False,
        """Enabling this option will prevent the Trac project from
        changing the contents of the SVN trac|authz_file.""")

    def __init__(self):
        # Retrieve info for all repositories associated with this project
        self.authz_file = self.config.getpath('trac', 'authz_file')
        rm = RepositoryManager(self.env)
        self.project_repos = []
        for reponame in rm.get_all_repositories().iterkeys():
            self.project_repos.append(reponame)
        self.authz = None

    # ITemplateProvider methods

    def get_htdocs_dirs(self):
        return []

    def get_templates_dirs(self):
        from pkg_resources import resource_filename
        return [resource_filename('svnauthz', 'templates')]

    # IAdminPanelProvider methods

    def get_admin_panels(self, req):
        if 'TRAC_ADMIN' in req.perm:
            yield ('versioncontrol', 'Version Control',
                   'svnauthz', 'Subversion Access')

    def render_admin_panel(self, req, cat, page, path_info):
        data = {}

        self.authz = self._get_authz(req)
        if not self.authz:
            return 'admin_authz.html', data

        if req.method == 'POST':
            if 'addgroup' in req.args:
                data.update(self._add_group(req))
            elif 'addpath' in req.args:
                data.update(self._add_path(req))
            elif 'addgroupmember' in req.args:
                data.update(self._add_group_member(req))
            elif 'removegroupmembers' in req.args:
                data.update(self._del_group_member(req))
            elif 'removegroups' in req.args:
                data.update(self._del_groups(req))
            elif 'removepaths' in req.args:
                data.update(self._del_paths(req))
            elif 'addpathmember' in req.args:
                data.update(self._add_path_member(req))
            elif 'changepathmembers' in req.args:
                data.update(self._change_path_members(req))
            if not any(key.endswith('_error') for key in data.keys()):
                add_notice(req, _("Your changes have been saved."))

        # Handle group and path edit mode handling
        editgroup = None
        editpath = None
        if path_info and path_info.startswith('editgroup/'):
            editgroup, d = self._edit_group(path_info)
            data.update(d)
        elif path_info and path_info.startswith('editpath/'):
            editpath, d = self._edit_path(path_info)
            data.update(d)

        paths_disp = []
        for repository, path in [(p.get_repo(), p.get_path())
                                 for p in self.authz.get_paths()]:
            if not self.show_all_repos and \
                    repository not in self.project_repos:
                # We eliminate repos associated with other Trac projects
                # unless show_all_repos is true
                continue
            path_disp = self._get_disp_path_name(repository, path)
            path_disp_url = urllib.pathname2url(path_disp)
            if editpath and editpath == path_disp_url:
                path_disp_href = req.href.admin('versioncontrol', 'svnauthz')
            else:
                path_disp_href = req.href.admin('versioncontrol', 'svnauthz',
                                                'editpath')
                path_disp_href += '/' + path_disp_url
            paths_disp.append({
                'name': path_disp,
                'url': path_disp_url,
                'href': path_disp_href
            })
        data['paths'] = sorted(paths_disp, key=lambda p: p['href'].lower())
        self.log.debug("SvnAuthzAdminPlugin: paths: '%s'", data['paths'])

        groups_disp = []
        for group_disp in sorted(g.get_name() for g in self.authz.get_groups()):
            group_disp_url = urllib.pathname2url(group_disp)
            if editgroup and editgroup == group_disp_url:
                group_disp_href = req.href.admin('versioncontrol', 'svnauthz')
            else:
                group_disp_href = req.href.admin('versioncontrol', 'svnauthz',
                                                 'editgroup', group_disp_url)

            groups_disp.append({
                'name': group_disp,
                'url': group_disp_url,
                'href': group_disp_href
            })
        data['groups'] = sorted(groups_disp, key=lambda p: p['href'].lower())
        self.log.debug("SvnAuthzAdminPlugin: groups: '%s'", data['groups'])

        data['read_only_display'] = self.read_only_display

        AuthzFile(self.authz_file).write(self.authz)

        return 'admin_authz.html', data

    def _add_group(self, req):
        groupname = req.args.get('groupname')
        if not groupname:
            return {'addgroup_error': _("Group not specified")}
        try:
            group = Group(groupname, [])
        except Exception, e:
            return {'addgroup_error': e}
        self.authz.add_group(group)
        return {}

    def _del_groups(self, req):
        groups_to_del = req.args.getlist('selgroup')
        if not groups_to_del:
            return {'delgroup_error': _("No groups selected.")}
        try:
            for group in groups_to_del:
                self.authz.del_group(urllib.url2pathname(group))
        except Exception, e:
            return {'delgroup_error': e}
        return {}

    def _add_path(self, req):
        pathname = req.args.get('path')
        if ':' in pathname:
            repository, pathname = pathname.split(':')
            repository = repository.strip()
        else:
            repository = self.project_repos[0]
        pathname = pathname.strip()
        if not pathname:
            return {'addpath_error': _("Path not specified")}
        try:
            path = Path(pathname, [], repository)
        except Exception, e:
            return {'addpath_error': e}
        self.authz.add_path(path)
        return {}

    def _del_paths(self, req):
        paths_to_del = req.args.getlist('selpath')
        if not paths_to_del:
            return {'delpath_error': _("No paths selected.")}
        paths = [(p.get_repo(), p.get_path()) for p in self.authz.get_paths()]
        try:
            for urlpath in paths_to_del:
                validpath = \
                    self._get_valid_path(paths, urllib.url2pathname(urlpath))
                if validpath:
                    self.authz.del_path(validpath[1], validpath[0])
        except Exception, e:
            return {'delpath_error': e}
        return {}

    def _add_group_member(self, req):
        editgroup = urllib.url2pathname(req.args.get('editgroup'))
        subject = req.args.get('subject')
        if subject == '':
            subject = req.args.get('subject2')
        if subject == '':
            return {'addgroupmember_error': _("No member specified")}
        group = self.authz.find_group(editgroup)
        if group is None:
            return {
                'addgroupmember_error': "Group %s does not exist" % editgroup
            }
        try:
            member = self._get_member(subject)
            assert member is not None
            group.append(member)
        except Exception, e:
            return {'addgroupmember_error': e}
        return {}

    def _del_group_member(self, req):
        editgroup = urllib.url2pathname(req.args.get('editgroup'))
        group = self.authz.find_group(editgroup)
        if not group:
            return {
                'delgroupmember_error': _("Group %(group)s does not exist",
                                          group=editgroup)
            }
        try:
            for member in req.args.getlist('selgroupmember'):
                group.remove(self._get_member(member))
        except Exception, e:
            return {'delgroupmember_error': e}

        return {}

    def _add_path_member(self, req):
        editpath = urllib.url2pathname(req.args.get('editpath'))
        subject = req.args.get('subject')
        if subject == '':
            subject = req.args.get('subject2')
        if subject == '':
            return {'addpathmember_error': _("No member specified")}
        acls = req.args.getlist('addpathmember_acl')
        paths = [(p.get_repo(), p.get_path()) for p in self.authz.get_paths()]
        validpath = self._get_valid_path(paths, editpath)
        if not validpath:
            return {
                'changepathmember_error':
                    _("Not a valid path: %(path)s", path=editpath)
            }
        path = validpath[1]
        repo = validpath[0]
        path_members = self.authz.find_path(path, repo)

        read = False
        write = False
        for i in acls:
            if i == 'R':
                read = True
            elif i == 'W':
                write = True

        try:
            s = self._get_member(subject)
            assert s is not None
            path_members.append(PathAcl(s, read, write))
        except Exception, e:
            return {'addpathmember_error': e}
        return {}

    def _change_path_members(self, req):
        editpath = urllib.url2pathname(req.args.get('editpath'))
        paths = [(p.get_repo(), p.get_path()) for p in self.authz.get_paths()]
        validpath = self._get_valid_path(paths, editpath)
        if not validpath:
            return {
                'changepathmember_error':
                    _("Not a valid path: %(path)s", path=editpath)
            }
        path = validpath[1]
        repo = validpath[0]
        members_to_del = req.args.getlist('selpathmember')
        member_acls = req.args.getlist('selpathmember_acl')
        path_members = self.authz.find_path(path, repo)

        if len(path_members) == 0:
            # Nothing to do
            return {}

        try:
            if members_to_del:
                if not members_to_del:
                    return {
                        'changepathmember_error':
                            _("Wrong type of member selection")
                    }
                for member in members_to_del:
                    m = self._get_member(member)
                    to_remove = path_members.find_path_member(m)
                    path_members.remove(to_remove)
        except Exception, e:
            return {'changepathmember_error': e}

        try:
            for member in path_members:
                read = False
                write = False
                if '%s_R' % member.get_member() in member_acls:
                    read = True
                if '%s_W' % member.get_member() in member_acls:
                    write = True
                if (read, write) != (member.is_read(), member.is_write()):
                    member.set_read(read)
                    member.set_write(write)
        except Exception, e:
            return {'changepathmember_error': e}

        return {}

    def _edit_group(self, path_info):
        """Populates the editgroup.* parts of the hdf

        @return the value of editgroup.url or None
        """
        data = {}
        index = path_info.index('/')+1
        edit_group = urllib.url2pathname(path_info[index:len(path_info)])
        group = self.authz.find_group(edit_group)
        if group is not None:
            data['editgroup_name'] = edit_group
            data['editgroup_url'] = urllib.pathname2url(edit_group)
            data['editgroup_members'] = \
                sorted((str(m) for m in group),
                       key=lambda member: member.lower())

            # Populate member candidates
            not_in_list = [str(m) for m in group]
            not_in_list.append('@%s' % edit_group)
            candidates = self._get_candidate_subjects(not_in_list)
            if candidates:
                data['editgroup_candidates'] = candidates
            return data['editgroup_url'], data
        self.log.debug("SvnAuthzAdminPlugin: Group %s not found.", edit_group)
        return None, {}

    def _get_all_users(self):
        """Fetches all users/groups from PermissionSystem."""
        perm = PermissionSystem(self.env)
        users = ['*']
        data = perm.get_all_permissions()
        if not data:
            return []  # we abort here

        for subject, action in data:
            if subject not in users and \
                    subject not in ('anonymous', 'authenticated'):
                users.append(subject)
        return users

    def _get_authz(self, req):
        if self.authz_file and os.path.exists(self.authz_file):
            return AuthzFile(self.authz_file).read()
        elif self.authz_file:
            add_warning(req, _("Authz file not found at %(file)s",
                               file=self.authz_file))
        else:
            add_warning(req, _("Path to authz file not defined in trac.ini."))

        return None

    def _get_candidate_subjects(self, not_in_list=None):
        candidates = ['']
        users = [user for user in self._get_all_users()
                 if user not in not_in_list]
        candidates += sorted(users)
        candidates += sorted(group.__str__()
                             for group in self.authz.get_groups()
                             if group.__str__() not in not_in_list or [])
        return candidates

    def _edit_path(self, path_info):
        """Populates the editpath.* parts of the hdf

        @return the value of editgroup.url or None
        """
        data = {}
        index = path_info.index('/') + 1
        edit_path = urllib.url2pathname(path_info[index:len(path_info)])
        paths = [(p.get_repo(), p.get_path()) for p in self.authz.get_paths()]
        valid_path = self._get_valid_path(paths, edit_path)
        if valid_path:
            data['editpath_name'] = edit_path
            data['editpath_url'] = urllib.pathname2url(edit_path)
            path_members = self.authz.find_path(valid_path[1], valid_path[0])
            edit_path_members = []
            for member in path_members:
                read = write = ''
                if member.is_read():
                    read = 'checked'
                if member.is_write():
                    write = 'checked'

                edit_path_members.append({
                    'subject': str(member.get_member()),
                    'read': read,
                    'write': write
                })
            data['editpath_members'] = \
                sorted(edit_path_members, key=lambda m: m['subject'].lower())

            # Populate member candidates
            not_in_list = [str(m.get_member()) for m in path_members]
            candidates = self._get_candidate_subjects(not_in_list)
            if candidates:
                data['editpath_candidates'] = candidates
            return data['editpath_url'], data
        return None, {}

    def _get_valid_path(self, pathlist, path):
        for repository, pathname in pathlist:
            if self._get_disp_path_name(repository, pathname) == path:
                return repository, pathname
        return None, path

    @staticmethod
    def _get_disp_path_name(repository, path):
        if repository is None:
            return '*:%s' % path
        else:
            return '%s:%s' % (repository, path)

    def _get_member(self, id_, create_group=False):
        if id_.startswith('@'):
            g = self.authz.find_group(id_.lstrip('@'))
            if not g and create_group:
                return Group(id_.lstrip('@'), [])
            else:
                return g
        else:
            return User(id_)
