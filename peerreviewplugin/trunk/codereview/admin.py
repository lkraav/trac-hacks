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
from trac.web.main import add_notice, add_warning
from .model import ReviewDataModel, ReviewFileModel
from .repo import insert_project_files, repo_path_exists

__author__ = 'Cinc'
__license__ = "BSD"

class PeerReviewFileAdmin(Component):
    implements(IAdminPanelProvider)

    # IAdminPanelProvider methods

    def get_admin_panels(self, req):
        if 'CODE_REVIEW_DEV' in req.perm:
            yield ('codereview', 'Code review', 'projectfiles', 'Project Files')

    def render_admin_panel(self, req, cat, page, path_info):
        def _insert_project_info(type_, key_, val):
            rev_data = ReviewDataModel(self.env)
            rev_data['type'] = type_
            rev_data['data_key'] = key_
            rev_data['data'] = val
            rev_data.insert()
        def remove_project_info(rem_name):
            # Remove project name info
            rev_data = ReviewDataModel(self.env)
            rev_data.clear_props()
            rev_data['data'] = rem_name
            rev_data['data_key'] = 'name'
            for item in rev_data.list_matching_objects():
                item.delete()
            # Remove info about project like rootfolder, extensions
            rev_data = ReviewDataModel(self.env)
            rev_data.clear_props()
            rev_data['data_key'] = rem_name
            for item in rev_data.list_matching_objects():
                item.delete()
            ReviewFileModel.delete_files_by_project_name(self.env, rem_name)

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

        exts = req.args.get('extensions', '')
        ext_list, ext_filtered = create_ext_list(exts)
        sel = req.args.get('sel', [])  # For removal
        if type(sel) is not list:
            sel = [sel]

        all_proj = ReviewDataModel.all_file_project_data(self.env)

        if req.method=='POST':
            if req.args.get('add'):
                if name in all_proj:
                    add_warning(req, _("The project identifier already exists."))
                    req.redirect(req.href.admin(cat, page, projectname=name,
                                                rootfolder=rootfolder,
                                                extensions=exts))
                if not repo_path_exists(self.env, rootfolder, ''):
                    add_warning(req, _("The given root folder can't be found in the repository or it is a file."))
                    req.redirect(req.href.admin(cat, page, projectname=name,
                                                rootfolder=rootfolder,
                                                extensions=exts))
                if len(ext_list) != len(ext_filtered):
                    add_warning(req, _("Some extensions are not valid."))
                    req.redirect(req.href.admin(cat, page, projectname=name,
                                                rootfolder=rootfolder,
                                                extensions=exts))
                _insert_project_info('fileproject', 'name', name)
                _insert_project_info('rootfolder', name, rootfolder)
                _insert_project_info('extensions', name, exts)
                insert_project_files(self.env, rootfolder, name, ext_filtered)
                add_notice(req, _("The project has been added. All files belonging to the project have been added "
                                  "to the database"))
            elif req.args.get('save'):
                if name != path_info:
                    if name in all_proj:
                        add_warning(req, _("The project identifier already exists."))
                        req.redirect(req.href.admin(cat, page, path_info, projectname=name,
                                                    rootfolder=rootfolder,
                                                    extensions=exts))
                if not repo_path_exists(self.env, rootfolder, ''):
                    add_warning(req, _("The given root folder can't be found in the repository or it is a file."))
                    req.redirect(req.href.admin(cat, page, path_info, projectname=name,
                                                rootfolder=rootfolder,
                                                extensions=exts))
                if len(ext_list) != len(ext_filtered):
                    add_warning(req, _("Some extensions are not valid. %s"), exts)
                    req.redirect(req.href.admin(cat, page, path_info, projectname=name,
                                                rootfolder=rootfolder,
                                                extensions=exts))
                # Handle change. We remove all data for old name and recreate it using the new one
                remove_project_info(path_info)
                _insert_project_info('fileproject', 'name', name)
                _insert_project_info('rootfolder', name, rootfolder)
                _insert_project_info('extensions', name, exts)
                insert_project_files(self.env, rootfolder, name, ext_filtered)
                add_notice(req, _("Your changes have been changed. All files belonging to the project have been added "
                                  "to the database"))
            elif req.args.get('remove'):
                for rem_name in sel:
                    remove_project_info(rem_name)

            req.redirect(req.href.admin(cat, page))
        all_proj_lst = [[key, value] for key, value in all_proj.items()]
        data = {'view': 'detail' if path_info else 'list',
                'projects': sorted(all_proj_lst, key=lambda item: item[0]),
        }
        if(path_info):
            data['view_project'] = path_info
            view_proj = all_proj[path_info]
            data.update({
                'projectname': name,
                'rootfolder': rootfolder or view_proj['rootfolder'],
                'extensions': exts or view_proj['extensions']
            })
        else:
            data.update({
                'projectname': name,
                'rootfolder': rootfolder,
                'extensions': exts
            })

        return 'admin_files.html', data