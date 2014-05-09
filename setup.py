#!/usr/bin/env python
from inspect import cleandoc
from setuptools import setup

__version__ = "0.1"

setup(
    name="txspinneret",
    version=__version__,
    packages=["txspinneret", "txspinneret.test"],
    description=cleandoc("""
        Spinneret is a collection of higher-level utility classes and functions
        for Twisted Web.
        """),
    long_description=cleandoc("""
        Spinneret is a collection of higher-level utility classes and functions
        to make writing complex Twisted Web applications far simpler, it is
        designed to easily integrate with existing Twisted Web projects for
        things like the improved ``IResource`` implementations.
        """),
    url="https://github.com/jonathanj/txspinneret",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: POSIX",

        # General classifiers to indicate "this project supports Python 2" and
        # "this project supports Python 3".
        "Programming Language :: Python :: 2",

        # More specific classifiers to indicate more precisely which versions
        # of those languages the project supports.
        "Programming Language :: Python :: 2.7",

        "Programming Language :: Python :: Implementation :: CPython",
        "Programming Language :: Python :: Implementation :: PyPy",

        "Topic :: Software Development :: Libraries :: Python Modules",
        ],
    install_requires=["zope.interface>=3.6.0", "twisted>=8.0"],
    test_suite="txspinneret",
    )
