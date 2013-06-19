# -*- coding: utf-8 -*-

# http://docs.python.org/distutils/apiref.html
from setuptools import find_packages, setup

##
# Add L10N support for newer trac distributions
# see http://trac.edgewall.org/wiki/CookBook/PluginL10N
##
setup_l10n = {}
try:
  from trac.util.dist import get_l10n_cmdclass
  cmdclass = get_l10n_cmdclass()
  if cmdclass:
    setup_l10n = {
      'cmdclass': cmdclass,
      'message_extractors': { 'projectplan': [
        ('**.py',                'python', None), # generic python extractor
        ('**/templates/**.html', 'genshi', None), # genshi (x)html Template extractor
        ('**/templates/**.txt',  'genshi', {      # genshi Text Template extractor
          'template_class': 'genshi.template:TextTemplate'
        }),
      ]}
    }
except ImportError:
  pass

##
# create setup instance
##
setup(
  name = u'ProjectPlan',
  ###
  #  * setuptools/distutils versioning: https://pythonhosted.org/setuptools/setuptools.html#specifying-your-project-s-version
  #  * semantic versioning, c.f. http://semver.org/
  #  FIXME: on Reintegration, fix the version numbering according to semver (next major increase)
  #  currently i'm using <last trunk merged ver>-dev.tira<nrchanges> which allows
  #  setuptools parse_version to compare the version (<ver> predecessor < <ver>-dev.tiraN < <ver>)
  ###
  version = u'2.1.3-dev.tira1',
  description = u'ProjectPlanPlugin for Trac',
  long_description = u"""
    ProjectPlan Plugin basicaly adds the possibility for fast and
    easy integration of different project mananagement visualizations
    (those working on the tickets and generating output like reports, charts and so on).
    The output generation does work in three steps:
      1. collect the tickets needed for the output: can be controlled by user arguments if its allowed by the output/plugin
      2. calculate (controlled by output), some calculations can be enabled/disabled with user arguments, depending on the output
      3. render (generate the output), controlled by user arguments, additional arguments are output dependend
    Additional information can be found at the Trac-Hacks project page for this plugin.
  """,
  author = u'anbo & makadev',
  author_email = u' anbo@informatik-tipps.net',
  url = u'http://trac-hacks.org/wiki/ProjectPlanPlugin',
  download_url = u'http://trac-hacks.org/svn/projectplanplugin',
  packages = find_packages(),
  license = u'GPL2',
  keywords = u'project plan visualization',
  package_data = { 'projectplan': [
    u'templates/*.html',
    u'htdocs/css/*.*',
    u'htdocs/images/*.*',
    u'htdocs/images/*/*.*',
    u'htdocs/images/*/*/*.*',
    u'htdocs/images/*/*/*/*.*',
    u'htdocs/js/*.*',
    u'htdocs/js/*/*.*',
    u'htdocs/js/*/*/*.*',
    u'locale/*/LC_MESSAGES/*.mo'
  ] },
  install_requires = ( u'Trac >=0.12, <1.1' ),
  entry_points = { u'trac.plugins': u'projectplan = projectplan.projectplan' },
  **setup_l10n
)
