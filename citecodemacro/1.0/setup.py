from setuptools import find_packages, setup

setup(
    name = 'TracCiteCode',
    version = '0.1.0',
    packages = find_packages(exclude=['*.tests*']),
    entry_points = {
        'trac.plugins': [
            'traccitecode = traccitecode',
        ],
    },
)
