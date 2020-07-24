from setuptools import setup

setup(
    name='TracSimpleMultiProject',
    version='0.7.1',
    packages=['simplemultiproject'],
    package_data={
        'simplemultiproject': [
            'templates/*.html',
            'htdocs/*.js',
            'htdocs/js/*.js',
            'htdocs/css/*.css'
        ]
    },
    install_requires=['Trac'],
    author='Christopher Paredes',
    author_email='jesuchristopher@gmail.com',
    maintainer="falkb",
    license='GPL',
    url='https://trac-hacks.org/wiki/SimpleMultiProjectPlugin',
    description='Simple Multi Project plugin for managing several projects '
                'with one Trac instance.',
    long_description='Simple Multi Project',
    keywords='Simple Multi Project',
    classifiers=['Framework :: Trac'],
    entry_points={'trac.plugins': [
        'simplemultiproject.admin = simplemultiproject.admin',
        'simplemultiproject.admin_command = simplemultiproject.admin_command',
        'simplemultiproject.admin_filter = simplemultiproject.admin_filter',
        'simplemultiproject.environmentSetup = simplemultiproject.environmentSetup',
        'simplemultiproject.milestone = simplemultiproject.milestone',
        'simplemultiproject.model = simplemultiproject.model',
        'simplemultiproject.roadmap = simplemultiproject.roadmap',
        'simplemultiproject.ticket = simplemultiproject.ticket',
        'simplemultiproject.timeline = simplemultiproject.timeline',
        'simplemultiproject.version = simplemultiproject.version',
        'simplemultiproject.permission = simplemultiproject.permission',
    ]},
    test_suite='simplemultiproject.tests.test_suite'
)
