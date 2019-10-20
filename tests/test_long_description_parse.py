from unittest import TestCase

from darglint.lex import (
    lex,
    condense,
)
from darglint.parse.long_description import (
    parse,
)
from darglint.parse.identifiers import (
    NoqaIdentifier,
)
from darglint.parse.grammars.google_long_description import (
    LongDescriptionGrammar,
)
from darglint.parse.cyk import (
    parse as cyk_parse,
)
from darglint.utils import (
    CykNodeUtils,
)


class LongDescriptionParserTestCase(TestCase):

    def parse_string(self, value):
        tokens = lex(value)
        condensed_tokens = condense(tokens)
        return parse(condensed_tokens)

    def get_identifiers(self, node, identifier):
        for child in node.walk():
            if identifier in child.annotations:
                yield child

    def get_identifier(self, node, identifier):
        return next(self.get_identifiers(node, identifier))

    def assertContains(self, node, identifier, msg=''):
        found = self.get_identifier
        if found:
            return found
        self.fail(
            'Expected node to contain identifier '
            '{}, but it did not.\n{}'.format(
                identifier,
                msg,
            )
        )

    def assertTokensEqual(self, token1, token2, msg=''):
        if token1 is None and token2 is None:
            return
        elif token1 is None or token2 is None:
            self.fail('{} != {}: {}'.format(
                token1, token2, msg
            ))
        self.assertEqual(
            token1.token_type, token2.token_type,
            msg,
        )
        self.assertEqual(
            token1.value, token2.value,
            msg,
        )

    def assertNodesEqual(self, node1, node2, msg=''):
        if node1 is None and node2 is None:
            return
        elif node1 is None or node2 is None:
            self.fail(
                '{} != {}: {}'.format(
                    node1, node2, msg,
                )
            )
        self.assertTokensEqual(
            node1.value, node2.value, msg
        )
        # We don't care about the symbols, since they are prone to change,
        # and the complexity there is handled by the identifier classes.
        self.assertNodesEqual(node1.lchild, node2.lchild, msg)
        self.assertNodesEqual(node1.rchild, node2.rchild, msg)

    def test_parse_single_word(self):
        node = self.parse_string('parseme!')
        self.assertEqual(
            node.symbol,
            'long-description',
        )

    def test_parse_multiple_words(self):
        node = self.parse_string('parse me!')
        self.assertEqual(
            node.symbol,
            'long-description',
        )

    def test_parse_with_other_symbols(self):
        for symbol in [
            'Returns', 'Yields', 'Args', '(', ')'
        ]:
            raw = 'normal words {} normal'.format(symbol)
            node = self.parse_string(raw)
            self.assertEqual(
                node.reconstruct_string(),
                raw,
            )

        # Colons are slightly different.  Probably this
        # will break once we handle whitespace correctly.
        node = self.parse_string('normal: words')
        self.assertEqual(
            node.reconstruct_string(),
            'normal: words',
        )

    def test_parse_endline_bare_noqa(self):
        raw = 'Something something # noqa'
        node = self.parse_string(raw)
        self.assertContains(node, NoqaIdentifier, str(node))

    def test_parse_newline_bare_noqa(self):
        raw = 'something # noqa\n'
        node = self.parse_string(raw)
        self.assertContains(node, NoqaIdentifier, str(node))

    def test_parse_just_noqa(self):
        raw = '# noqa'
        node = self.parse_string(raw)
        self.assertContains(node, NoqaIdentifier, str(node))

    def test_parse_initial_bare_noqa(self):
        raw = '# noqa\nSomething something'
        node = self.parse_string(raw)
        self.assertContains(node, NoqaIdentifier, str(node))

    def test_parse_noqa_with_targets(self):
        raw = '# noqa: I301'
        node = self.parse_string(raw)
        self.assertContains(node, NoqaIdentifier, str(node))

    def test_parse_noqa_with_multiple_targets(self):
        raw = '# noqa: I301 E302 *\nSomething something'
        node = self.parse_string(raw)
        self.assertContains(node, NoqaIdentifier, str(node))

    def test_cyk_noqa_matches(self):
        for raw in [
            '# noqa',
            '# noqa: I102',
            '# noqa: I301 E102 I320',
            'random words # noqa',
            'random words # noqa: I102',
            'random words # noqa: I301 E102 I320',

            # FIXME: These should parse with Cyk...
            # '# noqa\n',
            # '# noqa: I102\n',
            # '# noqa: I301 E102 I320\n',
        ]:
            recursive_node = self.parse_string(raw)
            recursive_noqa = self.get_identifier(
                recursive_node,
                NoqaIdentifier
            )
            self.assertTrue(recursive_noqa)

            cyk_node = cyk_parse(LongDescriptionGrammar, condense(lex(raw)))
            cyk_noqa = self.get_identifier(cyk_node, NoqaIdentifier)
            self.assertTrue(cyk_noqa)

            self.assertNodesEqual(
                cyk_noqa, recursive_noqa, repr(raw)
            )

    def test_noqa_always_on_left(self):
        raw = '\n'.join([
            '# noqa',
            'b',
        ])
        node = self.parse_string(raw)
        for noqa in self.get_identifiers(node, NoqaIdentifier):
            self.assertFalse(
                CykNodeUtils.contains(noqa, 'long-description'),
                'The noqa should be on its own, but was not:\n{}'.format(
                    noqa
                )
            )

    def test_noqa_identifiers_correct(self):
        raw = '\n'.join([
            'Noqa-full.',
            '',
            '# noqa',
            '# noqa: I325',
            '',
            'Raises:',
            '    MyException: Sometimes.  # noqa: I932',
            '',
        ])
        node = self.parse_string(raw)
        noqas = list(self.get_identifiers(node, NoqaIdentifier))
        self.assertEqual(
            len(noqas),
            3,
        )

        individuals = [
            '# noqa',
            '# noqa: I325',
            '# noqa: I932',
        ]
        for individual, noqa in zip(individuals, noqas):
            individual_node = self.parse_string(individual)
            self.assertNodesEqual(
                noqa,
                individual_node,
            )
