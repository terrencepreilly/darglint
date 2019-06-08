from itertools import chain
import random
from unittest import (
    TestCase,
)

from bnf_to_cnf.parser import (
    Parser,
)
from bnf_to_cnf.node import (
    Node,
    NodeType,
)

MAX_REPS = 5


class ParserTestCase(TestCase):

    def test_parse_simple_rule(self):
        """Make sure a simple, terminal rule works."""
        node = Parser().parse('<args> ::= "Args"')
        self.assertTrue(isinstance(node, Node))
        self.assertEqual(
            str(node),
            '<args> ::= "Args"',
        )

    def test_parse_rule_with_spaces(self):
        """Test conjunction in rules."""
        node = Parser().parse('<heading> ::= <ident> ":"')
        self.assertEqual(
            str(node),
            '<heading> ::= <ident> ":"',
        )

    def test_multiple_sequences(self):
        """Make sure we can have multiple sequences."""
        node = Parser().parse('<heading> ::= "Args" ":" | "Returns" ":"')
        self.assertEqual(
            str(node),
            '<heading> ::= "Args" ":" | "Returns" ":"'
        )

    def test_multiple_rules(self):
        """Make sure we can handle multiple rules in a grammar."""
        node = Parser().parse('''
            <head> ::= <keyword> ":"

            <keyword> ::= "Args" | "Returns"
        ''')
        self.assertEqual(
            str(node),
            '\n'.join([
                '<head> ::= <keyword> ":"',
                '<keyword> ::= "Args" | "Returns"',
            ]),
        )

    def test_mix_terminals_and_nonterminals(self):
        """Make sure we can mix terminals and non-terminals."""
        values = [
            '<S> ::= <A> "a" | <B>',
            '<S> ::= "a" <A> | <B>',
            '<S> ::= "a" | <B>',
        ]
        for value in values:
            node = Parser().parse(value)
            self.assertEqual(
                str(node),
                value
            )

    def test_failing_terminal_parse(self):
        """Make sure this particular instance, which failed, passes."""
        value = (
            '<S> ::= <A> "a" | <B>\n'
            '<A> ::= "b" | <B>\n'
            '<B> ::= <A> | "a"'
        )
        node = Parser().parse(value)
        self.assertEqual(
            value,
            str(node),
        )

    def test_comments_are_ignored(self):
        # Here, terminals are tokens which will be represented in python.
        grammar = [
            '<start> ::= <sentence>',
            '<sentence> ::= <word_run> <period>',
            '<word_run> ::= <word> <word_run> | ε',
            '<period> ::= "IND_TYPE\\.period"',
            '<word> ::= "IND_TYPE\\.word"',
        ]
        comments = [
            '# ----- IMPORTANT SECTION ----',
            '# Author: Thomas Jefferson',
        ]

        # Make sure they zip together well.
        comments += [''] * (len(grammar) - len(comments) + 1)
        without_comments = Parser().parse('\n'.join(grammar))
        for _ in range(MAX_REPS):
            random.shuffle(comments)
            complete = list(chain(*zip(comments, grammar)))
            with_comments = Parser().parse('\n'.join(complete))
            self.assertTrue(without_comments.equals(with_comments))

    def test_with_imports(self):
        grammar = (
            'import base.bnf\n'
            'import utils.bnf\n'
            '\n'
            '<start> ::= <sentence>\n'
            '<setence> ::= <verb> <noun>\n'
            '<verb> ::= "TT\\.VERB"\n'
            '<noun> ::= "TT\\.NOUN"'
        )
        node = Parser().parse(grammar)
        self.assertEqual(
            grammar,
            str(node),
            f'\nExpected:\n{grammar}\n\nBut got:\n{node}'
        )

    def test_with_name(self):
        grammar = '\n'.join([
            'import base.bnf',
            '',
            'Grammar: MySpecialGrammar',
            '',
            '<A> ::= "SPECIAL"'
        ])
        tree = Parser().parse(grammar)
        name = next(tree.filter(Node.is_name))
        self.assertEqual(
            name.value,
            'MySpecialGrammar',
        )
        py_repr = tree.to_python()
        self.assertTrue('class MySpecialGrammar' in py_repr)

    def test_parse_single_annotation(self):
        """Make sure we can annotate a production with an error."""
        grammar = '@SE001\n<sentence> ::= <wordrun> <newline>'
        tree = Parser().parse(grammar)
        production = tree.children[0]
        annotations = production.children[0]
        self.assertEqual(
            annotations.node_type,
            NodeType.ANNOTATIONS,
        )
        self.assertEqual(
            len(annotations.children),
            1,
        )
        annotation = annotations.children[0]
        self.assertEqual(
            annotation.node_type,
            NodeType.ANNOTATION,
        )
        self.assertEqual(
            annotation.value,
            'SE001',
        )

    def test_parse_multiple_annotations(self):
        """Make sure a production can have multiple annotations."""
        grammar = '@VERBLESS\n@PUNCT\n<sentence> ::= <period> <noun>'
        tree = Parser().parse(grammar)
        production = tree.children[0]
        annotations = production.children[0]
        self.assertEqual(
            ['VERBLESS', 'PUNCT'],
            [x.value for x in annotations.children],
        )

    def test_parse_annotation_on_rhs(self):
        """Make sure we can annotate a particular production."""
        grammar = '<A> ::= @Q <B> <C>'
        tree = Parser().parse(grammar)
        production = tree.children[0]
        expression = production.children[1]
        sequence = expression.children[0]
        annotations = sequence.children[0]
        self.assertEqual(
            annotations.node_type,
            NodeType.ANNOTATIONS,
        )
        annotation = annotations.children[0]
        self.assertEqual(
            annotation.value,
            'Q',
        )
