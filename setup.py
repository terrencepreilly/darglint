"""Defines the package, tests, and dependencies."""

import os
from setuptools import setup, find_packages


def read_full_documentation(fname):
    """Get long documentation from the README.md."""
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


requirements = ['redbaron']


setup(
    name="darglint",
    version="0.0.0",
    author="Terrence Reilly",
    author_email="terrencepreilly@gmail.com",
    description=("A utility for ensuring Google-style docstrings"
                 "stay up to date with the source code."),
    license="MIT",
    keywords="documentation linter",
    url="http://github.com/terrencepreilly/darglint",
    packages=find_packages(exclude=('tests', 'docs')),
    long_description=read_full_documentation('README.md'),
    entry_points={
        'console_scripts': [
            'darglint = darglint.driver:main',
        ],
    },
    install_requires=requirements,
    setup_requires=requirements,
    tests_require=['pytest'],
)
