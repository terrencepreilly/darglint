from setuptools import setup, find_packages

setup(
    name="bnf_to_cnf",
    version="0.0.2",
    author="Terrence Reilly",
    author_email="terrencepreilly@gmail.com",
    description=("A utility for converting bnf to cnf."),
    license="MIT",
    keywords="grammar bnf cnf",
    packages=find_packages(exclude=('tests', 'docs')),
    long_description=(
        'A small utility to convert BNF to CNF for use in '
        'darglint, to ease writing new grammars.'
    ),
    entry_points={
        'console_scripts': [
            'bnf_to_cnf = bnf_to_cnf.driver:main',
        ],
    },
    install_requires=[
        'lark-parser==0.7.8',
    ],
    setup_requires=[],
    tests_require=['pytest'],
    python_requires='>=3.7',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Topic :: Software Development :: Code Generators',
        'Topic :: Software Development :: Compilers',
        'License :: OSI pproved :: MIT License',
        'Programming Language :: Python :: 3.7',
        'Intended Audience :: Developers',
    ],
)
