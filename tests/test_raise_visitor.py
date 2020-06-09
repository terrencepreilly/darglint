import ast
from unittest import TestCase
from darglint.analysis.raise_visitor import RaiseVisitor


class RaiseVisitorTestCase(TestCase):

    def assertFound(self, program, *exceptions):
        function = ast.parse(program).body[0]
        visitor = RaiseVisitor()
        visitor.visit(function)
        for exception in exceptions:
            self.assertTrue(
                exception in visitor.exceptions,
                'Expected to find {} in exceptions, but did not.'.format(
                    exception
                )
            )

    def assertNoneFound(self, program):
        function = ast.parse(program).body[0]
        visitor = RaiseVisitor()
        visitor.visit(function)
        self.assertEqual(
            visitor.exceptions,
            set(),
            'Expected to find no exceptions, but found {}'.format(
                len(visitor.exceptions)
            ),
        )

    def test_identifies_one_exception(self):
        program = '\n'.join([
            'def f():',
            '    raise Exception("Something")',
        ])
        self.assertFound(program, 'Exception')

    def test_ignores_caught_exception(self):
        program = '\n'.join([
            'def f():',
            '    try:',
            '        raise Exception("Something")',
            '    except Exception as e:',
            '        pass',
        ])
        self.assertNoneFound(program)

    def test_ignores_caught_exception_unnamed(self):
        program = '\n'.join([
            'def f():',
            '    try:',
            '        raise Exception("Something")',
            '    except:',
            '        pass',
        ])
        self.assertNoneFound(program)

    def test_identifies_exception_in_catch(self):
        program = '\n'.join([
            'def f():',
            '    try:',
            '        something_dangerous()',
            '    except:',
            '        raise Exception("Something")',
        ])
        self.assertFound(program, 'Exception')

    def test_identifies_uncaught_in_try(self):
        program = '\n'.join([
            'def f():',
            '    try:',
            '        raise SyntaxError("Problematic.")',
            '    except IOException:',
            '        print("Not gonna happen.")',
        ])
        self.assertFound(program, 'SyntaxError')

    def test_caught_in_outer_try(self):
        program = '\n'.join([
            'def f():',
            '    try:',
            '        try:',
            '            raise SyntaxError("Here!")',
            '        except IOException:',
            '            pass',
            '    except SyntaxError as e:',
            '        pass',
        ])
        self.assertNoneFound(program)

    def test_uncaught_in_nested_try(self):
        program = '\n'.join([
            'def f():',
            '    try:',
            '        try:',
            '            raise InterruptedException()',
            '        except MathError:',
            '            pass',
            '    except IOError:',
            '        pass',
        ])
        self.assertFound(program, 'InterruptedException')

    def test_caught_in_inner_catch(self):
        program = '\n'.join([
            'def f():',
            '    try:',
            '        try:',
            '            raise SyntaxError(">")',
            '        except:',
            '            pass',
            '    except IOError:',
            '        pass',
        ])
        self.assertNoneFound(program)

    def test_caught_multiple_exceptions(self):
        program = '\n'.join([
            'def f(x):',
            '    try:',
            '        y = int(x)',
            '        return 2 / y',
            '    except (ValueError, ZeroDivisionError) as vezde:',
            '        pass',
        ])
        self.assertNoneFound(program)

    def test_reraise_one_of_multiple_exceptions(self):
        program = '\n'.join([
            'def f(x):',
            '    try:',
            '        y = int(x)',
            '        return 2 / y',
            '    except (ValueError, ZeroDivisionError) as vezde:',
            '        raise vezde',
        ])
        self.assertFound(
            program,
            'ValueError',
            'ZeroDivisionError',
        )

    def test_bare_reraise_single_exception(self):
        program = '\n'.join([
            'def f(x):',
            '    try:',
            '        return 1 / x',
            '    except ZeroDivisionError:',
            '        raise',
        ])
        self.assertFound(
            program,
            'ZeroDivisionError',
        )

    def test_bare_reraise_one_of_multiple_exceptions(self):
        program = '\n'.join([
            'def f(x):',
            '    try:',
            '        y = int(x)',
            '        return 2 / y',
            '    except (ValueError, ZeroDivisionError):',
            '        raise',
        ])
        self.assertFound(
            program,
            'ValueError',
            'ZeroDivisionError',
        )
