from setuptools import setup

setup(name='TracPoll',
      version='0.4.0',
      packages=['tracpoll'],
      entry_points = {'trac.plugins': ['tracpoll = tracpoll']},
      author='Alec Thomas',
      maintainer = 'Ryan J Ollos',
      maintainer_email = 'ryan.j.ollos@gmail.com',
      url='https://trac-hacks.org/wiki/PollMacro',
      license='BSD',
      package_data={'tracpoll': ['htdocs/css/*.css']},
      install_requires=['Trac'],
      )
