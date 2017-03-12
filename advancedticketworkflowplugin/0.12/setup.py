#!/usr/bin/env python

from setuptools import setup, find_packages

extra = {}
try:
    import babel
    del babel
    extra['message_extractors'] = {
        'advancedworkflow': [
            ('**.py', 'python', None),
            ('**.html', 'genshi', None),
        ],
    }
    from trac.util.dist import get_l10n_cmdclass
    extra['cmdclass'] = get_l10n_cmdclass()
except ImportError:
    pass

setup(
    name='AdvancedTicketWorkflowPlugin',
    version='0.12.0',
    author='Eli Carter',
    author_email='elicarter@retracile.net',
    license='BSD',
    description='Advanced workflow operations Trac plugin',
    long_description='Provides more advanced workflow operations for Trac 0.12',
    url='https://trac-hacks.org/wiki/AdvancedTicketWorkflowPlugin',

    packages=find_packages(exclude=['*.tests*']),
    package_data={
        'advancedworkflow': [
            'locale/*/LC_MESSAGES/*.mo',
        ],
    },
    test_suite='advancedworkflow.tests.test_suite',
    entry_points={
        'trac.plugins': [
            'advancedworkflow.controller = advancedworkflow.controller',
        ],
    },
    install_requires=[],
    #zip_safe=False,
    **extra)
