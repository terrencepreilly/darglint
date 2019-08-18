from setuptools import setup, find_packages

setup(
    name="doc_extract",
    version="0.0.1",
    author="Terrence Reilly",
    author_email="terrencepreilly@gmail.com",
    description=("A utility for extracting docstrings from git projects."),
    license="MIT",
    keywords="utils documentation",
    packages=find_packages(exclude=('tests', 'docs')),
    long_description=(
        'A small utility for extracting docstrings from a python project '
        'hosted on a git server, for use in analysis and testing.'
    ),
    entry_points={
        'console_scripts': [
            'doc_extract = doc_extract.driver:main',
        ],
    },
    install_requires=[],
    setup_requires=[],
    tests_require=[],
    python_requires='>=3.7',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'License :: OSI pproved :: MIT License',
        'Programming Language :: Python :: 3.7',
        'Intended Audience :: Developers',
    ],
)
