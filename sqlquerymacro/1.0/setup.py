#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup

setup(
    name = "TracSqlQueryMacro",
    version = "0.3",
    packages = ["sqlquery"],
    package_data = {"sqlquery": []},

    author = "James Mills",
    author_email = "James dot Mills at au dot pwc dot com",
    description = "A macro to execute sql queries against a database",
    license = "BSD",
    keywords = "trac macro sql query",
    url = "https://trac-hacks.org/wiki/SqlQueryMacro",

    entry_points = {
        "trac.plugins": [
            "sqlquery.macro = sqlquery.macro"
        ]
    },
)
