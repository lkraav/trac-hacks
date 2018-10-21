# -*- coding: utf-8 -*-

from trac.admin import IAdminPanelProvider
from trac.core import *
from trac.util.presentation import Paginator
from trac.web.chrome import Chrome, add_link, add_notice

from packagerepository.core import PackageRepositoryModule
from packagerepository.model import PackageRepositoryFile


class PackageRepositoryAdminPanel(Component):
    """Package Repository Admin Panel"""

    implements(IAdminPanelProvider)

    # IAdminPanelProvider methods

    def get_admin_panels(self, req):
        if 'PACKAGE_REPOSITORY_ADMIN' in req.perm:
            yield ('packagerepository', "Package Repository", 'packages', "Packages")

    def render_admin_panel(self, req, category, panel, path_info):
        if panel == 'packages':
            req.perm.require('PACKAGE_REPOSITORY_ADMIN')
            return self.render_packages_panel(req, category, panel, path_info)

    def render_packages_panel(self, req, category, panel, path_info):
        package_repo_mod = PackageRepositoryModule(self.env)
        repositories = package_repo_mod.get_all_repository_types()

        # Detail view?
        if path_info:
            id = path_info
            file = PackageRepositoryFile.select_by_id(self.env, id)
            if not file:
                raise TracError("Package does not exist!")
            if req.method == 'POST':
                if req.args.get('save'):
                    file.repository = req.args.get('repository')
                    file.package = req.args.get('package')
                    file.version = req.args.get('version')
                    file.filename = req.args.get('filename')
                    file.comment = req.args.get('comment')
                    PackageRepositoryFile.update(self.env, file)
                    add_notice(req, 'Your changes have been saved.')
                    req.redirect(req.href.admin(category, panel))
                elif req.args.get('cancel'):
                    req.redirect(req.href.admin(category, panel))

            Chrome(self.env).add_wiki_toolbars(req)
            data = {
                'view': 'detail',
                'file': file,
                'repositories': repositories,
            }
        else:
            if req.method == 'POST':
                if req.args.get('add'):
                    # Add file
                    repotype = req.args.get('repository')
                    filename, fileobj, filesize = req.args.getfile('file')
                    if not filename:
                        raise TracError("No file uploaded")

                    package_repo_mod.save_package(repotype, filename, fileobj)

                    file = PackageRepositoryFile(None, None, None, None, None, None)
                    file.repository = repotype
                    file.package = req.args.get('package')
                    file.version = req.args.get('version')
                    file.filename = filename
                    file.comment = req.args.get('comment')
                    PackageRepositoryFile.add(self.env, file)
                    add_notice(req, 'The file has been added.')
                    req.redirect(req.href.admin(category, panel))
                elif req.args.get('remove'):
                    # Remove files
                    file_ids = req.args.getlist('sel')
                    if not file_ids:
                        raise TracError('No files selected')

                    for id in file_ids:
                        file = PackageRepositoryFile.select_by_id(self.env, id)
                        package_repo_mod.delete_package(file.repository, file.filename)

                    PackageRepositoryFile.delete_by_ids(self.env, file_ids)
                    add_notice(req, 'The files have been removed.')
                    req.redirect(req.href.admin(category, panel))

            # Pagination
            page = int(req.args.get('page', 1))
            max_per_page = int(req.args.get('max', 10))

            files = PackageRepositoryFile.select_paginated(self.env, page, max_per_page)
            total_count = PackageRepositoryFile.total_count(self.env)

            paginator = Paginator(files, page - 1, max_per_page, total_count)
            if paginator.has_next_page:
                next_href = req.href.admin(category, panel, max=max_per_page, page=page + 1)
                add_link(req, 'next', next_href, 'Next Page')
            if paginator.has_previous_page:
                prev_href = req.href.admin(category, panel, max=max_per_page, page=page - 1)
                add_link(req, 'prev', prev_href, 'Previous Page')

            pagedata = []
            shown_pages = paginator.get_shown_pages(21)
            for page in shown_pages:
                pagedata.append([req.href.admin(category, panel, max=max_per_page, page=page), None,
                                str(page), 'Page %d' % (page,)])
            paginator.shown_pages = [dict(zip(['href', 'class', 'string', 'title'], p)) for p in pagedata]
            paginator.current_page = {'href': None, 'class': 'current',
                                    'string': str(paginator.page + 1),
                                    'title':None}

            data = {
                'view': 'list',
                'paginator': paginator,
                'max_per_page': max_per_page,
                'files': files,
                'repositories': repositories,
            }

        return 'packagerepository_admin_files.html', data, None
