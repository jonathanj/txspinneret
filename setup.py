#!/usr/bin/env python
import os
from inspect import cleandoc
from setuptools import setup


def get_version():
    """
    Get the version from version module without importing more than
    necessary.
    """
    version_module_path = os.path.join(
        os.path.dirname(__file__), "txspinneret", "_version.py")
    # The version module contains a variable called __version__
    with open(version_module_path) as version_module:
        exec(version_module.read())
    return locals()["__version__"]


def read(path):
    """
    Read the contents of a file.
    """
    with open(path) as f:
        return f.read()


setup(
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: POSIX",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: Implementation :: CPython",
        "Programming Language :: Python :: Implementation :: PyPy",
        "Topic :: Software Development :: Libraries :: Python Modules"],
    name="txspinneret",
    version=get_version(),
    description=cleandoc("""
        Spinneret is a collection of higher-level utility classes and functions for Twisted Web.
        """),
    install_requires=["zope.interface>=3.6.0", "twisted>=13.2.0"],
    keywords="twisted web routing",
    license="MIT",
    packages=["txspinneret", "txspinneret.test"],
    url="https://github.com/jonathanj/txspinneret",
    maintainer="Jonathan Jacobs",
    long_description=read('README.rst'),
    test_suite="txspinneret",
    extras_require={
        "doc": ["Sphinx==1.2",
                "sphinx-rtd-theme==0.1.6",
                "sphinxcontrib-zopeext"],
        "dev": ["testtools==0.9.35"],
    })
