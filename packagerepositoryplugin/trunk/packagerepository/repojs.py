# -*- coding: utf-8 -*-

import shutil
import os
import re

from trac.core import *
from trac.cache import cached
from trac.util import lazy
from trac.util.presentation import to_json
from trac.web.api import IRequestHandler, HTTPNotFound

from packagerepository.core import IPackageRepositoryProvider
from packagerepository.model import PackageRepositoryFile


class JavascriptPackageRepository(Component):
    """Provides an online repository for Javascript packages.
    Implements the "CommonJS Compliant package registry" API:
    http://wiki.commonjs.org/wiki/Packages/Registry
    Can be used with `npm` via `--registry`.
    """

    implements(IPackageRepositoryProvider, IRequestHandler)

    # IPackageRepositoryProvider methods

    def get_repository_types(self):
        return ['js']

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
        /packages/js
        (?:
          /
          (?:
            ([A-Za-z0-9\-\.\_]+)            # Group 1: namme
            (?:
              /
              (?:
                ([A-Za-z0-9\-\.\_]+)        # Group 2: version
                (?:
                  /
                  (?:
                    ([0-9]+)                # Group 3: id
                    /
                    ([A-Za-z0-9\-\.\_]+)?   # Group 3: filename
                  )?
                )?
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
                req.args['name'] = match.group(1)
            if match.group(2):
                req.args['version'] = match.group(2)
            if match.group(3):
                req.args['id'] = match.group(3)
                req.args['filename'] = match.group(4)
            return True

    def process_request(self, req):
        req.perm.require('PACKAGE_REPOSITORY_VIEW')

        name = req.args.get('name')
        ver = req.args.get('version')
        id = req.args.get('id')
        filename = req.args.get('filename')
        
        if name is None:
            self._send_json(req, self.packages)
        
        package = self.packages[name]
        if package is None:
            raise HTTPNotFound()

        if ver is None:
            self._send_json(req, package)

        version = package['versions'].get(ver)
        if version is None:
            raise HTTPNotFound()

        if filename is None:
            self._send_json(req, version)

        file = PackageRepositoryFile.select_by_id(self.env, id)
        if file is None or file.filename != filename:
            raise HTTPNotFound()
        file_path = os.path.join(self.packages_path, file.filename)
        req.send_header('Content-Disposition', 'attachment')
        req.send_file(file_path, 'application/octet-stream')

    def _send_json(self, req, data):
        req.send(to_json(data), 'application/json')

    @lazy
    def packages_path(self):
        return os.path.join(self.env.files_dir, 'packages', 'js')

    @cached
    def packages(self):
        packages = {}
        files = PackageRepositoryFile.select_by_repository(self.env, 'js')
        for file in files:
            name = file.package
            version = file.version
            id = file.id
            filename = file.filename
            package = packages.setdefault(name, {
                'name': name,
                'versions': {},
            })
            package['versions'][version] = {
                'name': name,
                'version': version,
                'dist': {
                    'tarball': self.env.href('packages', 'js', name, version, id, filename),
                },
            }
        return packages
