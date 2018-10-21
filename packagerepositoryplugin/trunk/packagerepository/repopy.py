# -*- coding: utf-8 -*-

import shutil
import os
import re

from trac.core import *
from trac.cache import cached
from trac.util import lazy
from trac.web.api import IRequestHandler, HTTPNotFound

from packagerepository.core import IPackageRepositoryProvider
from packagerepository.model import PackageRepositoryFile


def normalize(name):
    """https://www.python.org/dev/peps/pep-0503/#normalized-names"""
    return re.sub(r"[-_.]+", "-", name).lower()


class PythonPackageRepository(Component):
    """Provides an online repository for Python packages.
    Implements the "Simple Repository API":
    https://www.python.org/dev/peps/pep-0503/
    Can be used with `pip` via `--index-url`.
    """

    implements(IPackageRepositoryProvider, IRequestHandler)

    # IPackageRepositoryProvider methods

    def get_repository_types(self):
        return ['py']

    def save_package(self, repository_type, filename, fileobj):
        file_path = os.path.join(self.packages_path, filename)
        if not os.access(self.packages_path, os.F_OK):
            os.makedirs(self.packages_path)
        with open(file_path, 'wb') as targetobj:
            shutil.copyfileobj(fileobj, targetobj)
        del self.packages

    def delete_package(self, repository_type, filename):
        file_path = os.path.join(self.packages_path, filename)
        os.remove(file_path)
        del self.packages

    # IRequestHandler methods

    MATCH_REQUEST_RE = re.compile(r"""
        ^
        /packages/py
        (?:
          /
          (?:
            ([a-z0-9\-]+)               # Group 1: project
            (?:
              /
              (?:
                ([0-9]+)                # Group 2: id
                /
                ([A-Za-z0-9\-\.\_]+)    # Group 3: filename
              )?
            )?
          )?
        )?
        $
        """, re.VERBOSE)

    def match_request(self, req):
        match = self.MATCH_REQUEST_RE.match(req.path_info)
        if match:
            if match.group(1):
                req.args['project'] = match.group(1)
            if match.group(2):
                req.args['id'] = match.group(2)
                req.args['filename'] = match.group(3)
            return True

    def process_request(self, req):
        req.perm.require('PACKAGE_REPOSITORY_VIEW')

        project = req.args.get('project')
        id = req.args.get('id')
        filename = req.args.get('filename')
        
        if project is None:
            return self._render_index(req)
        
        if id is None:
            return self._render_project(req, project)

        file = PackageRepositoryFile.select_by_id(self.env, id)
        if file is None or file.filename != filename:
            raise HTTPNotFound()
        file_path = os.path.join(self.packages_path, file.filename)
        req.send_header('Content-Disposition', 'attachment')
        req.send_file(file_path, 'application/octet-stream')

    def _render_index(self, req):
        data = {
            'projects': self.projects.values(),
        }
        return 'packagerepository_py_index.html', data, None

    def _render_project(self, req, project):
        if project not in self.projects:
            raise HTTPNotFound()
        data = {
            'packages': self.projects[project]['packages'],
        }
        return 'packagerepository_py_project.html', data, None

    @lazy
    def packages_path(self):
        return os.path.join(self.env.files_dir, 'packages', 'py')

    @cached
    def projects(self):
        projects = {}
        files = PackageRepositoryFile.select_by_repository(self.env, 'py')
        for file in files:
            name = normalize(file.package)
            id = file.id
            filename = file.filename
            project = projects.setdefault(name, {
                'href': self.env.href('packages', 'py', name) + '/',
                'name': name,
                'packages': [],
            })
            project['packages'].append({
                'href': self.env.href('packages', 'py', name, id, filename),
                'filename': filename,
            })
        return projects
