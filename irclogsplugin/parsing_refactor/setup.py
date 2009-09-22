from setuptools import setup

PACKAGE = 'irclogs'
VERSION = '0.3'

setup(
    name=PACKAGE,
    version=VERSION,
    description='Display Supybot IRC Logs',
    author='Armin Ronacher, pacopablo, doki_pen',
    author_email='doki_pen@doki-pen.org',
    url='http://trac-hacks.org/wiki/IrcLogsPlugin',
    license='BSD',
    test_suite= 'irclogs.tests.suite',
    packages=['irclogs', 'irclogs.provider'],
    classifiers=[
        'Framework :: Trac',
        'License :: OSI Approved :: BSD License',
    ],
    package_data={
        'irclogs' : ['templates/*.html', 'htdocs/css/*.css', 
                     'htdocs/js/*.js', 'htdocs/images/*.png']
    },
    entry_points = {
        'trac.plugins': [
            'irclogs = irclogs',
            'irclogs.provider = irclogs.provider',
        ],
        'console_scripts': ['update-irc-search = irclogs.console:update_irc_search',],
    },
    install_requires = ['pytz>=2005m'],
    # optional pyndexter
)
