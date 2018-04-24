# Based on code from : http://trac-hacks.org/wiki/VotePlugin
from setuptools import setup

setup(
    name='FiveStarVote',
    version='0.2.0',
    packages=['fivestarvote'],
    author='Dav Glass',
    author_email='dav.glass@yahoo.com',
    maintainer='Ryan J Ollos',
    maintainer_email='ryan.j.ollos@gmail.com',
    license='BSD',
    url='https://trac-hacks.org/wiki/FiveStarVotePlugin',
    description='A plugin for 5-star voting on Trac resources.',
    entry_points={
        'trac.plugins': [
            'fivestarvote = fivestarvote'
        ]
    },
    install_requires=['Trac'],
    package_data={'fivestarvote': [
        'htdocs/js/*.js',
        'htdocs/css/*.css', 'htdocs/css/*.png'
    ]},
)
