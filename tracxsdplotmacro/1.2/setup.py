from setuptools import find_packages, setup

setup(
    name='TracXsdPlot', 
    version='1.2',
    author = 'Theodor Norup',
    author_email = 'theodor.norup@gmail.com',
    url = 'https://trac-hacks.org/wiki/TracXsdPlotMacro',
    license = '3-clause BSD',
    packages=find_packages(exclude=['*.tests*']),
    entry_points = """
        [trac.plugins]
        tracxsdplot = tracxsdplot
    """,
    install_requires = [ 'Trac >= 1.0.6' ]
)
