from setuptools import find_packages, setup

setup(
    name='detailedView', version='1.1',
    packages=find_packages(exclude=['*.tests*']),
    entry_points = """
        [trac.plugins]
        detailedView = detailedView
    """,
    package_data={'detailedView': ['templates/*.html']},
)
