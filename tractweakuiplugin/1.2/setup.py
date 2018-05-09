from setuptools import find_packages, setup

setup(
    name='TracTweakUI',
    version='1.2',
    packages=['tractweakui'],
    package_data={'tractweakui': [
        '*.txt', 'templates/*.*', 'htdocs/*.*', 'tests/*.*']},
    include_package_data=True,
    author="Richard Liao",
    author_email='richard.liao.i@gmail.com',
    maintainer='Richard Liao',
    maintainer_email="richard.liao.i@gmail.com",
    description="Trac Tweak UI plugin for Trac.",
    license="BSD",
    keywords="trac tweak ui",
    url="https://trac-hacks.org/wiki/TracTweakUiPlugin",
    classifiers=[
        'Framework :: Trac',
    ],
    install_requires=['Trac'],
    entry_points={'trac.plugins': ['tractweakui = tractweakui.web_ui']},
)
