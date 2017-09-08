from setuptools import setup

PACKAGE = 'SecurePluginPanel'
VERSION = '0.11.5'

setup(
    name = PACKAGE,
    version = VERSION,
    
    author = "Sebastian Krysmanski",
    author_email = None,
    url = "https://svn.mayastudios.de/mtpp/wiki/Plugins/SecurePluginPanel",
    
    description = "A slightly modified plugin panel for the admin section. " \
                  "Plugin installation and uninstallation have been disabled. " \
                  "Moreover components can be set as \"readonly\". This way they" \
                  " can't be enabled or disabled by the admin.",
    keywords = "trac plugins admin",
    
    license = "Modified BSD (Trac License)",
    
    install_requires = [
        'Trac>=0.11',
    ],
    
    zip_safe=True,
    packages=['securepluginpanel'],
    package_data={'securepluginpanel': ['templates/*.html',
                                     'htdocs/*']},
                                     
    entry_points={'trac.plugins': '%s = securepluginpanel.web_ui' % PACKAGE},
)