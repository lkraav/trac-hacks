from setuptools import find_packages, setup

setup(
    name='SVN_MULTI_URLs',
    version='0.3',
    author='Andreas Podskalsky',
    author_email='andreas.podskalsky@siemens.com',
    url='http://trac-hacks.org/wiki/SvnMultiUrlsPlugin',
    description='Provide links to the actual URLs of svn versioned resources',
    license='GPL',
    keywords='trac plugin multi svn',
    packages=find_packages(exclude=['*.tests*']),
    package_data={'svnmultiurls': ['templates/*.html']},
    install_requires=["Genshi>=0.6"],
    dependency_links=['http://svn.edgewall.org/repos/genshi/trunk#egg=Genshi-0.6'],
    entry_points = """
    [trac.plugins]
    svnmultiurls = svnmultiurls
    """,
    )
