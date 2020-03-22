import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(name='trac-IncludeSource',
    version='0.5',
    packages=['includesource'],
    author='Chris Heller',
    maintainer='Thomas Tressieres',
    maintainer_email='ttressieres@gmail.com',
    long_description=long_description,
    long_description_content_type="text/markdown",
    description='Include (parts of) a source file into the current wiki page',
    url='http://trac-hacks.org/wiki/IncludeSourcePartialPlugin',
    license='BSD',
    classifiers=[
        "Programming Language :: Python :: 2",
        "Operating System :: OS Independent",
    ],
    install_requires = ['Trac'],
    entry_points = {'trac.plugins': ['includesource.IncludeSource = includesource.IncludeSource']})
