"""Tests against goldens contained in a custom JSON file.

Goldens can be created using the doc_extract utility in the bin/ folder.
Goldens may not specify all parts of a docstring, but in order for
the integration test to pass, all parts identified in the golden must
be identified using the current implementation.

"""

import json
import sys
from unittest import ( # noqa
    TestCase,
    skip,
)
from darglint.docstring.docstring import (
    Docstring,
)
from darglint.docstring.base import (
    Sections,
)

SECTION_MAP = {
    'args': Sections.ARGUMENTS_SECTION,
    'arguments': Sections.ARGUMENTS_SECTION,
    'arguments-section': Sections.ARGUMENTS_SECTION,
    'except': Sections.RAISES_SECTION,
    'long-description': Sections.LONG_DESCRIPTION,
    'params': Sections.ARGUMENTS_SECTION,
    'raise': Sections.RAISES_SECTION,
    'raises': Sections.RAISES_SECTION,
    'raises-section': Sections.RAISES_SECTION,
    'return': Sections.RETURNS_SECTION,
    'returns': Sections.RETURNS_SECTION,
    'returns-section': Sections.RETURNS_SECTION,
    'short-description': Sections.SHORT_DESCRIPTION,
    'yield': Sections.YIELDS_SECTION,
    'yields': Sections.YIELDS_SECTION,
    'yields-section': Sections.YIELDS_SECTION,
    'param': Sections.ARGUMENTS_SECTION,
}


class Goldens(TestCase):

    def setUp(self):
        with open('integration_tests/goldens.json', 'r') as fin:
            self.goldens = json.load(fin)

    def parse_golden(self, golden):
        if golden['type'] == 'GOOGLE':
            docstring = Docstring.from_google(golden['docstring'])
        elif golden['type'] == 'SPHINX':
            docstring = Docstring.from_sphinx(golden['docstring'])
        else:
            raise Exception('Unsupported docstring type {}'.format(
                golden['type']
            ))
        return docstring, golden['metadata']

    def normalize_section(self, section):
        lowered = section.lower().strip()
        if lowered in SECTION_MAP:
            return SECTION_MAP[lowered]
        else:
            raise Exception('Expected {} to be in section lookup.'.format(
                section,
            ))
        return section

    def assertSectionsMatch(self, docstring, metadata, message=''):
        sections = metadata['sections']
        for section in sections:
            normalized_section = self.normalize_section(section)
            self.assertTrue(
                docstring.get_section(normalized_section),
                'Expected docstring to have '
                '{} but did not:\n\n```\n{}\n```\n\n{}'.format(
                    normalized_section,
                    docstring.root.reconstruct_string(),
                    message,
                )
            )

    def test_golden(self):
        for i, golden in enumerate(self.goldens):
            docstring, metadata = self.parse_golden(golden)
            self.assertSectionsMatch(
                docstring,
                metadata,
                'Index: {}\nTree: {}'.format(i, docstring.root),
            )
            sys.stderr.write('.')
