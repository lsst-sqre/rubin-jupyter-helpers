"""Setup module for Rubin JupyterHub Helper functions and classes.
"""
import codecs
import io
import os
import setuptools


def get_version(file, name="__version__"):
    """Get the version of the package from the given file by
    executing it and extracting the given `name`.
    """
    path = os.path.realpath(file)
    version_ns = {}
    with io.open(path, encoding="utf8") as f:
        exec(f.read(), {}, version_ns)
    return version_ns[name]


def local_read(filename):
    """Convenience function for includes.
    """
    full_filename = os.path.join(
        os.path.abspath(os.path.dirname(__file__)), filename
    )
    return codecs.open(full_filename, "r", "utf-8").read()


NAME = "rubin_jupyter_utils.helpers"
_path = NAME.replace(".", "/")
DESCRIPTION = (
    "Rubin helper classes and functions for "
    + "Jupyter Hub server environment"
)
LONG_DESCRIPTION = local_read("README.md")
VERSION = get_version("%s/_version.py" % _path)
AUTHOR = "Adam Thornton"
AUTHOR_EMAIL = "athornton@lsst.org"
URL = "https://github.com/lsst-sqre/rubin-jupyter-helpers"
LICENSE = "MIT"

setuptools.setup(
    name=NAME,
    version=VERSION,
    long_description=LONG_DESCRIPTION,
    packages=setuptools.find_namespace_packages(
        include=["rubin_jupyter_utils.*"]
    ),
    url=URL,
    author=AUTHOR,
    author_email=AUTHOR_EMAIL,
    license=LICENSE,
    classifiers=[
        "Development Status :: 4 - Beta",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.5",
        "License :: OSI Approved :: MIT License",
    ],
    keywords="lsst",
    install_requires=["eliot",
                      "kubernetes",
                      "requests>=2,<3"],
)
