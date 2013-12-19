from setuptools import setup

setup(
    name='SimpleMultiProject',
    version='0.0.4',
    packages=['simplemultiproject'],
    package_data={
        'simplemultiproject' : [
            'templates/*.html',
            'htdocs/*.js',
            'htdocs/css/*.css'
        ]
    },
    author = 'Christopher Paredes',
    author_email='jesuchristopher@gmail.com',
    maintainer = "falkb",
    license='GPL',
    url='http://trac-hacks.org/wiki/SimpleMultiProject',
    description='Simple Multi Project',
    long_description='Simple Multi Project',
    keywords='Simple Multi Project',
    entry_points = {'trac.plugins': ['simplemultiproject = simplemultiproject']}
)