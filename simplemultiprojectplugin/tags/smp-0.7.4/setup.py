from setuptools import setup

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name='TracSimpleMultiProject',
    version='0.7.4',
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
    author='Christopher Paredes, falkb, Cinc-th, Ryan J Ollos',
    author_email='',
    maintainer="Cinc-th",
    license='BSD',
    url='https://trac-hacks.org/wiki/SimpleMultiProjectPlugin',
    description='Simple Multi Project plugin for managing several projects '
                'with one Trac instance.',
    long_description=long_description,
    long_description_content_type='text/markdown',
    keywords='Simple Multi Project',
    classifiers=['Framework :: Trac'],
    entry_points={'trac.plugins': [
        'simplemultiproject.admin_command = simplemultiproject.admin_command',
        'simplemultiproject.admin_filter = simplemultiproject.admin_filter',
        'simplemultiproject.environmentSetup = simplemultiproject.environmentSetup',
        'simplemultiproject.milestone = simplemultiproject.milestone',
        'simplemultiproject.roadmap = simplemultiproject.roadmap',
        'simplemultiproject.ticket = simplemultiproject.ticket',
        'simplemultiproject.timeline = simplemultiproject.timeline',
        'simplemultiproject.permission = simplemultiproject.permission',
        'simplemultiproject.admin_project = simplemultiproject.admin_project',
        'simplemultiproject.version = simplemultiproject.version'
    ]},
    test_suite='simplemultiproject.tests.test_suite'
)
