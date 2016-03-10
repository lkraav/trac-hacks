from setuptools import setup
import multiprojectbacklog

PACKAGE = 'MultiProjectBacklog'

with open('README.txt') as file:
    long_description = file.read()

setup(
    name = PACKAGE,
    version = multiprojectbacklog.get_version(),
    packages = ['multiprojectbacklog'],
    package_data = {
        'multiprojectbacklog': [
            'htdocs/css/*.css',
            'htdocs/js/*.js',
            'templates/*.html',
      ]},
    entry_points = {
        'trac.plugins': [
            'multiprojectbacklog = multiprojectbacklog.web_ui',
            'backlog_prefs = multiprojectbacklog.prefs',
        ]
    },
    install_requires = [
        'Trac>=0.12'
    ],
    author = "John Szakmeister, Cinc",
    author_email = "",
    description = "Enables Trac to be used for managing your ticket backlog. Works with SimpleMultiProject plugin.",
    long_description = long_description,
    url = "https://trac-hacks.org/wiki/MultiProjectBacklogPlugin",
    license = "BSD",
    classifiers = [
        'Development Status :: 4 - Beta',
        'Environment :: Plugins',
        'Environment :: Web Environment',
        'Framework :: Trac',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2 :: Only',
    ],
)
