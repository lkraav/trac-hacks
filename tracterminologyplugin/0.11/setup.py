from setuptools import find_packages, setup

print find_packages(exclude=['*.tests*'])
setup(
    name='TracTerminologyPlugin', version='0.1',
    author='KAWACHI Takashi', author_email='kawachi@sra.co.jp',
    url="http://example.com/this_is_dummy",
    packages=find_packages(exclude=['*.tests*']),
    entry_points={
        'trac.plugins': [
            'terminology = terminology'
        ]
    },
    licence="BSD",
)
