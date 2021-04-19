# -*- coding: utf-8 -*-
#
# Copyright (C) 2016 Cinc
# All rights reserved.
#
# This software is licensed as described in the file COPYING.txt, which
# you should have received as part of this distribution.
#
# Author: Cinc
#

from collections import namedtuple
from trac.admin import IAdminPanelProvider
from trac.config import ConfigSection
from trac.core import Component, implements
from trac.mimeview.api import Mimeview
from trac.util.translation import _
from trac.web.chrome import add_link, add_notice, add_script, add_script_data, add_stylesheet, add_warning
from .model import ReviewDataModel, ReviewFileModel
from .repo import insert_project_files, repo_path_exists

__author__ = 'Cinc'
__license__ = "BSD"


def get_prj_file_list(self, prj_name):
    with self.env.db_query as db:
        FileData = namedtuple('FileData', ['file_id', 'path', 'repo', 'hash', 'rev', 'changerev'])
        files = [[FileData(*item), ''] for item in db("""SELECT f.file_id, f.path, 
                                               f.repo, f.hash, f.revision, f.changerevision
                                               FROM peerreviewfile f
                                               WHERE f.project = %s ORDER BY f.path
                                               """, (prj_name,))]
        approved_hashes = [item[0] for item in db("SELECT a.hash FROM peerreviewfile AS a WHERE status = 'approved'")]
        for item in files:
            if item[0].hash in approved_hashes:
                item[1] = 'Approved'
        return files


class PeerReviewFileAdmin(Component):
    """Admin panel to specify files belonging to a project.

    [[BR]]
    You may define a project identifier and a root folder from the repository holding all the files
    of a project using this admin panel. When saving the information all the files in the folder hierarchy are hashed
    and file name, revision, hash and project name are inserted in the database.

    Using the file information it is possible to create reports (see TracReports for more information) like which
    files may need a review and more.
    """
    implements(IAdminPanelProvider)

    external_map_section = ConfigSection('peerreview:externals',
        """It is possible to create a list of project files to check against files approved during a code review.
        A root directory may be selected which contains the source files. While traversing the tree {{{svn:esternal}}} 
        information is taken into account and all linked directories are also traversed.
        
        It is possible to have virtual repositories in Trac pointing to different parts of a bigger Subversion
        repository. To make sure externals are properly mapped path information may be provided in the section 
        {{{[peerreview:externals]}}} of the TracIni. Note that Subversion 1.5 server root relative URLs supported 
        (like {{{/foo/bar/src}}}) but not other relative URLs.
        
        Example:
        {{{
        #!ini
        [peerreview:externals]
        1 = /svn/repos1/src_branch1/foo           /src_branch1/foo  Repo-Src1                  
        2 = /svn/repos1/src_branch2/bar           /src_branch2/bar  Repo-Src2
        3 = /svn/repos1/src_branch3/baz           /src_branch3/baz  Repo-Src3
        4 = http://server/svn/repos1/src_branch3  /src_branch3  Repo-Src3
        }}}
        
        With the above, the
        `/svn/repos1/src_branch1/foo` external will
        be mapped to `/src_branch1/foo` in the repository {{{Repo-Src1}}}. 
        
        You only have to provide the common path prefix here. The remainder of the external path will automatically 
        appended thus {{{/svn/repos1/src_branch1/foo/dir1/dir2/dir3}}} becomes {{{/src_branch1/foo/dir1/dir2/dir3}}}.
        """)

    # IAdminPanelProvider methods

    def __init__(self):
        self._externals_map = {}

    def get_admin_panels(self, req):
        if 'CODE_REVIEW_DEV' in req.perm:
            yield ('codereview', 'Code review', 'projectfiles', 'Project Files')

    def render_admin_panel(self, req, cat, page, path_info):

        def remove_project_info(rem_name):
            # Remove project name info
            rev_data = ReviewDataModel(self.env)
            rev_data.clear_props()
            rev_data['data'] = rem_name
            rev_data['data_key'] = 'name'
            for item in rev_data.list_matching_objects():
                item.delete()
            # Remove info about project like rootfolder, extensions, revision, repo
            rev_data = ReviewDataModel(self.env)
            rev_data.clear_props()
            rev_data['data_key'] = rem_name
            for item in rev_data.list_matching_objects():
                item.delete()
            ReviewFileModel.delete_files_by_project_name(self.env, rem_name)

        def add_project_info():
            def _insert_project_info(type_, key_, val):
                rev_data = ReviewDataModel(self.env)
                rev_data['type'] = type_
                rev_data['data_key'] = key_
                rev_data['data'] = val
                rev_data.insert()
            _insert_project_info('fileproject', 'name', name)
            _insert_project_info('rootfolder', name, rootfolder)
            _insert_project_info('excludeext', name, exts)
            _insert_project_info('excludepath', name, exclpath)
            _insert_project_info('includeext', name, incl)
            _insert_project_info('repo', name, reponame)
            _insert_project_info('revision', name, rev)
            _insert_project_info('follow_externals', name, follow_externals)
            # Create option for DynamicVariables plugin
            # Note: we need to get the updated project data here
            prj_lst = sorted([key for key in ReviewDataModel.all_file_project_data(self.env)])
            if prj_lst:
                self.config.set('dynvars', 'project_files.options', '|'.join(prj_lst))
                self.config.save()

        def create_ext_list(ext_str):
            """Create a list of extensions from a string.

            Double ',', trailing ',' and empty extensions are filtered out. Extensions not starting with '.'
            are ignored.

            @return: unfiltered extension list, filtered extension list
            """
            if not ext_str:
                return [], []
            # filter trailing ',', double ','and empty exts
            ext_list = [ext.strip() for ext in ext_str.split(',') if ext.strip()]
            return ext_list, [ext.lower() for ext in ext_list if ext[0] == '.']

        def create_path_list(path_str):
            """Create a list of paths from a string.

            Double ',', trailing ',' and empty extensions are filtered out. Paths not starting with '/'
            are ignored.

            @return: unfiltered list, filtered list
            """
            if not path_str:
                return [], []
            # filter trailing ',', double ','and empty exts
            ext_list = [ext.strip() for ext in path_str.split(',') if ext.strip()]
            return ext_list, [ext for ext in ext_list if ext[0] == '/']

        req.perm.require('CODE_REVIEW_DEV')

        name = req.args.get('projectname') or path_info
        rootfolder = req.args.get('rootfolder')
        reponame = req.args.get('reponame', '')
        rev = req.args.get('rev', None)
        exts = req.args.get('excludeext', '')
        incl = req.args.get('includeext', '')
        exclpath = req.args.get('excludepath', '')
        follow_externals = req.args.get('follow_ext', False)
        sel = req.args.get('sel', [])  # For removal
        if type(sel) is not list:
            sel = [sel]

        all_proj = ReviewDataModel.all_file_project_data(self.env)

        if req.method=='POST':
            def _do_redirect(action):
                parms = {'projectname': name,
                         'rootfolder': rootfolder,
                         'excludeext': exts,
                         'includeext': incl,
                         'excludepath': exclpath,
                         'repo': reponame,
                         'rev': rev,
                         'error': 1
                         }
                if action == 'add':
                    req.redirect(req.href.admin(cat, page, parms))
                elif action == 'save':
                    req.redirect(req.href.admin(cat, page, path_info, parms))

            def check_parameters(action):
                if not repo_path_exists(self.env, rootfolder, reponame):
                    add_warning(req, _("The given root folder %s can't be found in the repository or it is a file."),
                                       rootfolder)
                    _do_redirect(action)
                if len(ext_list) != len(ext_filtered):
                    add_warning(req, _("Some extensions in exclude list are not valid: %s"), exts)
                    _do_redirect(action)
                if len(incl_list) != len(incl_filtered):
                    add_warning(req, _("Some extensions in include list are not valid: %s"), incl)
                    _do_redirect(action)
                if len(path_lst) != len(path_lst_filtered):
                    add_warning(req, _("Some entries in the exclude path list are not valid."))
                    _do_redirect(action)

            ext_list, ext_filtered = create_ext_list(exts)
            incl_list, incl_filtered = create_ext_list(incl)
            path_lst, path_lst_filtered = create_path_list(exclpath)

            if req.args.get('add'):
                action = 'add'
                if not name:
                    add_warning(req, _("You need to specify a project name."))
                    _do_redirect(action)
                if name in all_proj:
                    add_warning(req, _("The project identifier already exists."))
                    _do_redirect(action)
                check_parameters(action)  # This redirects to the page on parameter error
                add_project_info()
                errors, num_files = insert_project_files(self, rootfolder, name, ext_filtered, incl_filtered,
                                                         path_lst_filtered,
                                                         follow_externals, rev=rev, repo_name=reponame)
                add_notice(req, _("The project has been added. %s files belonging to the project %s have been added "
                                  "to the database"), num_files, name)
                for err in errors:
                    add_warning(req, err)
            elif req.args.get('save'):
                action = 'save'
                if not req.args.get('projectname'):
                    add_warning(req, _("No project name given. The old name was inserted again."))
                    add_warning(req, _("No changes have been saved."))
                    _do_redirect(action)
                if name != path_info:
                    if name in all_proj:
                        add_warning(req, _("The project identifier already exists."))
                        _do_redirect(action)
                check_parameters(action)  # This redirects to the page on parameter error

                # Handle change. We remove all data for old name and recreate it using the new one
                remove_project_info(path_info)
                add_project_info()
                errors, num_files = insert_project_files(self, rootfolder, name, ext_filtered, incl_filtered,
                                                         path_lst_filtered,
                                                         follow_externals, rev=rev, repo_name=reponame)
                add_notice(req, _("Your changes have been saved. %s files belonging to the project %s have been added "
                                  "to the database"), num_files, name)
                for err in errors:
                    add_warning(req, err)
            elif req.args.get('remove'):
                for rem_name in sel:
                    remove_project_info(rem_name)

            req.redirect(req.href.admin(cat, page))

        all_proj_lst = [[key, value] for key, value in all_proj.items()]
        data = {'view': 'detail' if path_info else 'list',
                'projects': sorted(all_proj_lst, key=lambda item: item[0]),
                'projectname': name,
        }
        if(path_info):
            # Details page or file list
            data['view_project'] = path_info
            view_proj = all_proj[path_info]
            # With V3.1 the following was added to the saved information for multi repo support.
            # It isn't available for old projects.
            view_proj.setdefault('repo', '')
            view_proj.setdefault('revision', '')
            # With V3.2 includeext and excludepath were added.
            # These aren't available for old projects.
            view_proj.setdefault('includeext', '')
            view_proj.setdefault('excludepath', '')
            # Legacy support. The name changed in V3.2
            try:
                excl_ext = view_proj['excludeext']
            except KeyError:
                excl_ext = view_proj['extensions']
            view_proj.setdefault('follow_externals', False)
            data.update({
                'rootfolder': rootfolder or view_proj['rootfolder'],
                'excludeext': exts or excl_ext,
                'excludepath': exclpath or view_proj['excludepath'],  #exclpath or excl_path,
                'includeext': incl or view_proj['includeext'],  #incl or incl_ext,
                'reponame': reponame or view_proj['repo'],
                'revision': rev or view_proj['revision'],
                'follow_externals': follow_externals or view_proj['follow_externals']
            })
            if req.args.get('filelist'):
                data['view'] = 'filelist'
                data['files'] = get_prj_file_list(self, path_info)

                # For downloading in docx format
                conversions = Mimeview(self.env).get_supported_conversions('text/x-trac-reviewfilelist')
                for key, name, ext, mime_in, mime_out, q, c in conversions:
                    conversion_href = req.href("peerreview", format=key, filelist=path_info)
                    add_link(req, 'alternate', conversion_href, name, mime_out)

        else:
            data.update({
                'rootfolder': rootfolder,
                'excludeext': exts,
                'excludepath': exclpath,
                'includeext': incl,
                'reponame': reponame,
                'revision': rev
            })

        add_stylesheet(req, 'common/css/browser.css')
        add_stylesheet(req, 'hw/css/admin_file.css')
        add_script_data(req, {'repo_browser': req.href.adminrepobrowser(data['rootfolder'],
                                                                        repo=data['reponame'],
                                                                        rev=data['revision']),
                              'show_repo_idx': path_info == None if 'error' not in req.args else False}
                        )
        add_script(req, 'hw/js/admin_files.js')
        return 'admin_files.html', data