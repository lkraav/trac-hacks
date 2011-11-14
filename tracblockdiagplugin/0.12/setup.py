"""
Author: IWATA Hidetaka <iwata0303@gmail.com>
"""
from setuptools import setup

NAME = "BlockDiagPlugin"
VERSION = "0.5.1"

setup(
    name = NAME,
    version = VERSION,
    packages = ['blockdiagplugin'],
    author = "IWATA Hidetaka",
    author_email = "iwata0303@gmail.com",
    description = """Provide macros to embed diagram generated by blockdiag family. Based on TracPlantUmlPlugin.""",
    license = "GPL",
    keywords = "trac macro embed include blockdiag",

    entry_points = {
        "trac.plugins": [
            "blockdiagplugin.web_ui = blockdiagplugin.web_ui"
        ]
    }
)
