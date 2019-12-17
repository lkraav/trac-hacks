from setuptools import setup

setup(
    name='ResourceReservation',
    version='1.0.4',
    packages=['resreservation'],
    package_data={'resreservation' : ['*.txt', 'templates/*.html', 'htdocs/js/*.js', 'htdocs/css/*.css', 'htdocs/images/*.*']},
    author = 'Roberto Longobardi',
    author_email='seccanj@gmail.com',
    license='BSD. See the file LICENSE.txt contained in the package.',
    url='http://trac-hacks.org/wiki/ResourceReservationPlugin',
    download_url='http://sourceforge.net/projects/resreserv4trac',
    description='Resource Reservation plugin for Trac',
    long_description='A Trac plugin and macro to allow for visually planning and reserving the use of resources in your environment, e.g. test machines, consumable test data, etc..., with just one click. Currently tested on Trac 0.11, 0.12 and Python 2.5 and 2.6.',
    keywords='trac plugin project resource management planning schedule',
    classifiers=['Framework :: Trac'],
    entry_points={'trac.plugins': ['resreservation = resreservation']},
    dependency_links=['http://svn.edgewall.org/repos/genshi/trunk#egg=Genshi-dev'],
    install_requires=['Genshi >= 0.5'],
    )
