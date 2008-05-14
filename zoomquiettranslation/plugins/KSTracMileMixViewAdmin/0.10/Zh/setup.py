from setuptools import find_packages, setup

setup(
    name = 'TracMileMixViewAdmin',
    version = '0.2',
    packages = ['rtadmin'],
    package_data = { 'rtadmin': [ '*.txt', 'templates/*.*', 'htdocs/*.*', 'tests/*.*' ] },

    author = "Richard Liao",
    author_email = 'richard.liao.i@gmail.com',
    maintainer = 'Richard Liao',
    maintainer_email = "richard.liao.i@gmail.com",
    description = "MileMixView Admin plugin for Trac.",
    license = "BSD",
    keywords = "trac rela ticket admin",
    url = "http://trac-hacks.org/wiki/MileMixViewAdmin",
    classifiers = [
        'Framework :: Trac',
    ],
    
    install_requires = ['TracWebAdmin'],
    entry_points = {'trac.plugins': ['rtadmin = rtadmin.relaticketadmin']},
)
