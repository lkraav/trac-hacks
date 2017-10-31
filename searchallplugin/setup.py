from setuptools import setup

setup(
    name='TracSearchAll',
    version='0.9',
    packages=['tracsearchall'],
    author='Alvaro J. Iradier',
    author_email="alvaro.iradier@polartech.es",
    description="Search in all projects in the same parent folder",
    long_description="",
    license='GPL',
    url="https://www.trac-hacks.org/wiki/SearchAllPlugin",
    entry_points={
        'trac.plugins': [
            'tracsearchall = tracsearchall.searchall'
        ]
    }
)
