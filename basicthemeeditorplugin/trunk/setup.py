from setuptools import setup

PACKAGE = 'BasicThemeEditorPlugin'
VERSION = '0.1'

setup(
    name = PACKAGE,
    version = VERSION,
    
    author = "Sebastian Krysmanski",
    author_email = None,
    url = "http://svn.mayastudios.de/maya/mtpp",
    
    description = "A webadmin panel to change some basic style settings.",
    keywords = "trac plugins",
    
    license = "BSD",
    
    install_requires = [
        'Trac>=0.11',
    ],
    
    zip_safe=True,
    packages=['basicthemeeditor'],
    package_data={'basicthemeeditor': ['templates/*']},
                                     
    entry_points={'trac.plugins': '%s = basicthemeeditor.web_ui' % PACKAGE},
)