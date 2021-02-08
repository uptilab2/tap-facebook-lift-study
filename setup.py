#!/usr/bin/env python
from setuptools import setup

setup(
    name="tap-facebook-lift-study",
    version="0.1.0",
    description="Singer.io tap for extracting data",
    author="emile.caron@uptilab.com",
    url="http://singer.io",
    classifiers=["Programming Language :: Python :: 3 :: Only"],
    py_modules=["tap_facebook_lift_study"],
    install_requires=[
        # NB: Pin these to a more specific version for tap reliability
        "singer-python",
        "facebook-business==9.0.2",
    ],
    entry_points="""
    [console_scripts]
    tap-facebook-lift-study=tap_facebook_lift_study:main
    """,
    package_data = {
        "schemas": ["schemas/*.json"]
    },
    include_package_data=True,
)
