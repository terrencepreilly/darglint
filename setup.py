"""Defines the package, tests, and dependencies."""

import os
from setuptools import setup, find_packages, Command
import subprocess


def read_full_documentation(fname):
    """Get long documentation from the README.rst.

    Args:
        fname: The filename for the documentation.

    Returns:
        The documentation, as a string.

    """
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


requirements = []


class PreBuildCommand(Command):
    """Converts README file."""

    description = 'Converts README.md to README.rst using pandoc.'
    user_options = []

    def initialize_options(self):
        self.cwd = None

    def finalize_options(self):
        self.cwd = os.getcwd()

    def run(self):
        assert os.getcwd() == self.cwd, 'We must be in the package root.'
        try:
            subprocess.run(['pandoc', 'README.md', '-o', 'README.rst'])
        except Exception:
            print('Pandoc must be installed to convert README.')


class CleanCommand(Command):
    """Cleans the project.

    - Remove the dist directory.
    - Remove the build directory.

    """

    description = 'Clean the directory of build artifacts'
    user_options = []

    def initialize_options(self):
        self.cwd = None

    def finalize_options(self):
        self.cwd = os.getcwd()

    def run(self):
        assert os.getcwd() == self.cwd, 'We must be in the package root.'
        subprocess.run(['rm', '-rf', './dist'])
        subprocess.run(['rm', '-rf', './build'])


setup(
    name="darglint",
    version="0.3.4",
    author="Terrence Reilly",
    author_email="terrencepreilly@gmail.com",
    description=("A utility for ensuring Google-style docstrings"
                 "stay up to date with the source code."),
    license="MIT",
    keywords="documentation linter development",
    url="http://github.com/terrencepreilly/darglint",
    packages=find_packages(exclude=('tests', 'docs')),
    long_description=read_full_documentation('README.rst'),
    entry_points={
        'console_scripts': [
            'darglint = darglint.driver:main',
        ],
    },
    install_requires=requirements,
    setup_requires=requirements,
    tests_require=['pytest', 'tox'] + requirements,
    python_requires='>=3.5',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Documentation',
        'Topic :: Software Development :: Quality Assurance',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.5',
    ],
    cmdclass={
        'prebuild': PreBuildCommand,
        'clean': CleanCommand,
    },
)
