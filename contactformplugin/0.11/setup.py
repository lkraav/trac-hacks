from setuptools import setup

PACKAGE = 'ContactFormPlugin'
VERSION = '0.1'

setup(
    name = PACKAGE,
    version = VERSION,
    
    author = "Sebastian Krysmanski",
    author_email = None,
    url = "https://svn.mayastudios.de/mtpp/wiki/Plugins/ContactFormPlugin",
    
    description = "A contact form to allow users to contact the project team members.",
    keywords = "trac plugins email",
    
    license = "Modified BSD",
    
    install_requires = [
        'Trac>=0.11',
    ],
    
    zip_safe=True,
    packages=['contactform'],
    package_data={'contactform': ['templates/*']},
                                     
    entry_points={'trac.plugins': '%s = contactform.web_ui' % PACKAGE},
)