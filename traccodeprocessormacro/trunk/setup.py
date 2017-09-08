from setuptools import setup

PACKAGE = 'TracCodeProcessor'
VERSION = '0.11.0'

setup(
    name = PACKAGE,
    version = VERSION,
    
    author = "Sebastian Krysmanski",
    author_email = None,
    url = "https://svn.mayastudios.de/mtpp/wiki/Plugins/CodeProcessor",
    
    description = "Provides a WikiProcessor for code listing that uses file " \
                  "extensions for language detection rather than mimetypes.",
    keywords = "trac macro code listing",
    
    license = "Modified BSD",
    
    install_requires = [
        'Trac>=0.11',
    ],
    
    packages=['codeprocessor'],
    package_data={'codeprocessor': ['htdocs/*']},
                                     
    entry_points={'trac.plugins': [ '%s = codeprocessor.codeprocessor' ]},
)