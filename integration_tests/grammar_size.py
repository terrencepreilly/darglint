"""A script to check and report the size of the grammars."""

import inspect
import os
import importlib

from darglint.parse.grammar import (
    BaseGrammar,
)


def convert_filename_to_module(filename):
    return filename[:-3].replace('/', '.')


def get_python_modules_in_grammars():
    basepath = os.path.join(
        os.getcwd(), 'darglint/parse/grammars'
    )
    return [
        (
            x,
            convert_filename_to_module(
                os.path.join('darglint/parse/grammars', x)
            )
        )
        for x in os.listdir(basepath)
        if x.endswith('.py')
    ]


def get_grammars(module):
    return [
        cls for (name, cls) in
        inspect.getmembers(module, inspect.isclass)
        if issubclass(cls, BaseGrammar) and cls is not BaseGrammar
    ]


def get_productions_in_grammar(grammar):
    return len(grammar.productions)


if __name__ == '__main__':
    modules = get_python_modules_in_grammars()
    count = {
        'google': 0,
        'sphinx': 0,
    }
    print('BY FILENAME')
    for grammar_type in count:
        for filename, filepath in filter(
            lambda x: x[0].startswith(grammar_type),
            modules
        ):
            mod = importlib.import_module(filepath)
            grammars = get_grammars(mod)
            amount = 0
            for grammar in grammars:
                amount += get_productions_in_grammar(
                    grammar
                )
            count[grammar_type] += amount
            print('{} {}'.format(filename.ljust(50), amount))
    print('\nTOTALS')
    for grammar in count:
        print('{}:\t{}'.format(grammar, count[grammar]))
