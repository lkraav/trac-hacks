from setuptools import find_packages, setup

setup(
    name='TracJupyterNotebook', version='1.0',
    packages=find_packages(exclude=['*.tests*']),
    entry_points = {
        'trac.plugins': [
            'TracJupyterNotebook = tracjupyternotebook.renderer',
        ],
    },
    install_requires = [
        'ipython',
        'nbformat',
        'nbconvert',
    ],
)

