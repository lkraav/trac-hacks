# Copyright 2010-2011, 2014 Stefan Goebel - <tracsecdl -at- subtype -dot- de>
#
# This file is part of TracSecDl.
#
# TracSecDl is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.
#
# TracSecDl is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# TracSecDl. If not, see <http://www.gnu.org/licenses/>.

from setuptools import setup

setup (

    name         = 'TracSecDl',
    version      = '0.1.2',
    description  = "File download plugin for Trac.",
    keywords     = 'trac lighttpd mod_secdownload files upload download',
    author       = 'Stefan Göbel',
    author_email = 'tracsecdl@subtype.de',
    url          = 'https://gitlab.com/goeb/tracsecdl/',
    license      = 'GPLv3',
    zip_safe     = True,
    classifiers  = ['Framework :: Trac'],

    packages     = [
            'tracsecdl',
            'tracsecdl.database',
            'tracsecdl.model',
            'tracsecdl.model.enum',
        ],

    package_data = {
            'tracsecdl': [
                    'templates/*.html', 'htdocs/css/*.css', 'htdocs/js/*.js'
                ]
        },

    entry_points = {
            'trac.plugins': [
                    'TracSecDl.AdminUI   = tracsecdl.admin_ui',
                    'TracSecDl.Config    = tracsecdl.config',
                    'TracSecDl.Env       = tracsecdl.env',
                    'TracSecDl.Extension = tracsecdl.extension',
                    'TracSecDl.Perm      = tracsecdl.perm',
                    'TracSecDl.Redirect  = tracsecdl.redirect',
                    'TracSecDl.Timeline  = tracsecdl.timeline',
                    'TracSecDl.Upload    = tracsecdl.upload',
                    'TracSecDl.WebUI     = tracsecdl.web_ui',
                    'TracSecDl.Wiki      = tracsecdl.wiki',
                ]
        },

)

# :indentSize=4:tabSize=4:noTabs=true:mode=python:maxLineLen=79: