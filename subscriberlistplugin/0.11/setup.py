from setuptools import setup

PACKAGE = 'SubscriberListPlugin'
VERSION = '0.1'

setup(
    name = PACKAGE,
    version = VERSION,
    
    author = "Sebastian Krysmanski",
    author_email = None,
    url = "https://svn.mayastudios.de/mtpp/wiki/Plugins/SubscriberListPlugin",
    
    description = "Displays a list of all users that will be notified about ticket " \
                  "changes of a certain ticket and informs the user about the current" \
                  "notification settings of Trac.",
    keywords = "trac plugins",
    
    license = "Modified BSD",
    
    install_requires = [
        'Trac>=0.11',
    ],
    
    zip_safe=True,
    packages=['subscriberlist'],
    package_data={'subscriberlist': ['htdocs/*']},
                                     
    entry_points={'trac.plugins': '%s = subscriberlist.web_ui' % PACKAGE},
)