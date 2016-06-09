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

from trac.admin import IAdminPanelProvider
from trac.core import Component, implements
from trac.util.text import _
from trac.web.chrome import add_notice, add_script, add_script_data, add_stylesheet, add_warning
from .model import ReviewDataModel, ReviewFileModel
from .repo import insert_project_files, repo_path_exists

__author__ = 'Cinc'
__license__ = "BSD"

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

    # IAdminPanelProvider methods

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
            _insert_project_info('extensions', name, exts)
            _insert_project_info('repo', name, reponame)
            _insert_project_info('revision', name, rev)

        def create_ext_list(ext_str):
            """Create a list of extensions from a string.

            Double ',', trailing ',' and empty extensions are filtered out. Extensions not starting with '.'
            are ignored.

            @return: unfiltered extension list, filtered extension list
            """
            if not ext_str:
                return [], []
            ext_list = [ext.strip() for ext in ext_str.split(',') if ext.strip()]  # filter trailing ',', double ','and empty exts
            return [ext for ext in ext_str.split(',') if ext], [ext.lower() for ext in ext_list if ext[0] == '.']

        req.perm.require('CODE_REVIEW_DEV')

        name = req.args.get('projectname') or path_info
        rootfolder = req.args.get('rootfolder')
        reponame = req.args.get('reponame', '')
        rev = req.args.get('rev', None)
        exts = req.args.get('extensions', '')
        ext_list, ext_filtered = create_ext_list(exts)
        sel = req.args.get('sel', [])  # For removal
        if type(sel) is not list:
            sel = [sel]

        all_proj = ReviewDataModel.all_file_project_data(self.env)

        if req.method=='POST':
            if req.args.get('add'):
                def do_redirect():
                    req.redirect(req.href.admin(cat, page, projectname=name,
                                                rootfolder=rootfolder,
                                                extensions=exts,
                                                repo=reponame,
                                                rev=rev,
                                                error=1))
                if not name:
                    add_warning(req, _("You need to specify a project name."))
                    do_redirect()
                if name in all_proj:
                    add_warning(req, _("The project identifier already exists."))
                    do_redirect()
                if not repo_path_exists(self.env, rootfolder, reponame):
                    add_warning(req, _("The given root folder can't be found in the repository or it is a file."))
                    do_redirect()
                if len(ext_list) != len(ext_filtered):
                    add_warning(req, _("Some extensions are not valid."))
                    do_redirect()
                add_project_info()
                insert_project_files(self.env, rootfolder, name, ext_filtered, rev=rev, reponame=reponame)
                add_notice(req, _("The project has been added. All files belonging to the project have been added "
                                  "to the database"))
            elif req.args.get('save'):
                def do_redirect_save():
                    req.redirect(req.href.admin(cat, page, path_info,
                                                projectname=name,
                                                rootfolder=rootfolder,
                                                extensions=exts,
                                                repo=reponame,
                                                rev=rev,
                                                error=1))

                if not req.args.get('projectname'):
                    add_warning(req, _("No project name given. The old name was inserted again."))
                    add_warning(req, _("No changes have been saved."))
                    do_redirect_save()
                if name != path_info:
                    if name in all_proj:
                        add_warning(req, _("The project identifier already exists."))
                        do_redirect_save()
                if not repo_path_exists(self.env, rootfolder, ''):
                    add_warning(req, _("The given root folder can't be found in the repository or it is a file."))
                    do_redirect_save()
                if len(ext_list) != len(ext_filtered):
                    add_warning(req, _("Some extensions are not valid. %s"), exts)
                    do_redirect_save()
                # Handle change. We remove all data for old name and recreate it using the new one
                remove_project_info(path_info)
                add_project_info()
                insert_project_files(self.env, rootfolder, name, ext_filtered, rev=rev, reponame=reponame)
                add_notice(req, _("Your changes have been changed. All files belonging to the project have been added "
                                  "to the database"))
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
            data['view_project'] = path_info
            view_proj = all_proj[path_info]
            # With V3.1 the following was added to the saved information for multi repo support.
            # It isn't available for old projects.
            if 'repo' not in view_proj:
                view_proj['repo'] = ''
            if 'revision' not in view_proj:
                view_proj['revision'] = ''
            data.update({
                'rootfolder': rootfolder or view_proj['rootfolder'],
                'extensions': exts or view_proj['extensions'],
                'reponame': reponame or view_proj['repo'],
                'revision': rev or view_proj['revision'],
            })
        else:
            data.update({
                'rootfolder': rootfolder,
                'extensions': exts,
                'reponame': reponame,
                'revision': rev
            })
        add_stylesheet(req, 'common/css/browser.css')
        add_stylesheet(req, 'hw/css/admin_file.css')
        add_script_data(req, {'repo_browser': self.env.href.adminrepobrowser(data['rootfolder'],
                                                                             repo=data['reponame'],
                                                                             rev=data['revision']),
                              'show_repo_idx': path_info == None if 'error' not in req.args else False}
                        )
        add_script(req, 'hw/js/admin_files.js')
        return 'admin_files.html', data