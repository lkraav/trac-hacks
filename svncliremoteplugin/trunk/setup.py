from setuptools import setup

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name='TracSvnCliRemote',
    version='0.1.0',
    packages=['subversioncli'],
    package_data={
        'subversioncli': [
        ]
    },
    install_requires=['Trac'],
    author='Cinc-th',
    author_email='',
    maintainer="Cinc-th",
    license='BSD',
    url='https://trac-hacks.org/wiki/SvnCliRemotePlugin',
    description='Subversion connector for remote and local repositories using the svn command line client',
    long_description=long_description,
    keywords='Subversion',
    classifiers=['Framework :: Trac'],
    entry_points={'trac.plugins': [
        'subversioncli.svn_cli = subversioncli.svn_cli',
    ]},
    test_suite='tests'
)
