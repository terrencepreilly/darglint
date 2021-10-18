import ast
from unittest import TestCase
from darglint.analysis.raise_visitor import RaiseVisitor
from unittest.mock import (
    patch,
    Mock,
)


class RaiseVisitorTestCase(TestCase):

    def assertFound(self, program, *exceptions):
        """Assert that the given exceptions were detected.

        Args:
            program: The program to run the analysis on.
            exceptions: The exceptions which should have been
                detected as being raised.

        """
        function = ast.parse(program).body[0]
        visitor = RaiseVisitor()
        visitor.visit(function)
        for exception in exceptions:
            self.assertTrue(
                exception in visitor.exceptions,
                'Expected to find {} in exceptions {}, but did not.'.format(
                    exception,
                    repr(visitor.exceptions),
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

    def test_bare_reraise_with_as(self):
        program = '\n'.join([
            'def f(x):',
            '    try:',
            '        return 1 / x',
            '    except ZeroDivisionError as zde:',
            '        raise',
        ])
        self.assertFound(
            program,
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

    def test_capture_tuple(self):
        program = '\n'.join([
            'def f(x):',
            '    try:',
            '        risky()',
            '    except (a.AError, b.BError):',
            '        raise',
        ])
        self.assertFound(
            program,
            'a.AError',
            'b.BError',
        )

    def test_bare_reraise_in_multiple_handlers(self):
        program = '\n'.join([
            'def f(x):',
            '    try:',
            '        risky.attempt(x)',
            '    except risky.Failed:',
            '        raise',
            '    except Exception:',
            '        logger.log("Something else went wrong!")',
            '',
        ])
        self.assertFound(program, 'risky.Failed')

    def test_reraise_any_exception_in_bare_handler(self):
        program = '\n'.join([
            'def f(x):',
            '    try:',
            '        if x == "Racoon":',
            '            raise Rabies()',
            '        elif x == "Bird":',
            '            raise H1N1()',
            '    except:',
            '        raise',
        ])
        self.assertFound(program, 'Rabies', 'H1N1')

    def test_reraise_any_exception_in_bare_handler(self):
        program = '\n'.join([
            'def f(x):',
            '    try:',
            '        if x == "Racoon":',
            '            raise Rabies()',
            '        elif x == "Bird":',
            '            raise H1N1()',
            '    except Rabies:',
            '        raise',
            '    except H1N1:',
            '        raise Unexpected()',
        ])
        self.assertFound(program, 'Rabies', 'Unexpected')

    def test_visits_finally_block(self):
        program = '\n'.join([
            'def f():',
            '    try:',
            '        dangerous_operation()',
            '    finally:',
            '        raise AnException()',
            '',
        ])
        self.assertFound(program, 'AnException')

    def test_visits_or_else_block(self):
        program = '\n'.join([
            'def f():',
            '    try:',
            '        pass',
            '    except Exception:',
            '        pass',
            '    else:',
            '        raise MyException()',
        ])
        self.assertFound(program, 'MyException')

    @patch('darglint.analysis.raise_visitor.logger')
    def test_visits_dynamic_exceptions_with_no_error_logs(self, mock_logger):
        mock_logger.error = Mock()
        program = '\n'.join([
            'def g():',
            '    try:',
            '        f("a")',
            '    except self.PropertyDynamicException:',
            '        pass',
            '    except MethodDynamicException().__class__:',
            '        raise Exception("Reraise.")',
        ])
        self.assertFound(program, 'Exception')
        self.assertFalse(
            mock_logger.error.called,
            'Unexpected error log.  Dynamic exception types from '
            'members of a class or calls to a function shouldn\'t '
            'result in error logs, but only info logs.  We should '
            'effictively ignore them.'
        )
