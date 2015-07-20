from setuptools import setup

PACKAGE = 'hipchatrelay'

setup(name=PACKAGE,
        version='0.0.1',
        packages=[PACKAGE],
        url='http://www.devis.com',
        license='http://www.opensource.org/licenses/mit-license.php',
        author='Nicholas Wheeler',
        author_email='nwheeler@devis.com',
        long_description="""
        Relay all changes to the appropriate hipchat room
        """,
        entry_points={'trac.plugins': [ '%s = %s' % (PACKAGE, PACKAGE) ]},
        package_data={'hipchatrelay' : ['templates/*.html', ]}
)
      
      
