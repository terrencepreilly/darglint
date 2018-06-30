"""A collection of sphinx docstrings from the wild."""
import ast


# def publish_msgstr(app, source, source_path, source_line, config, settings):
#     # From https://github.com/sphinx-doc/sphinx
#     # File: sphinx/transforms/il8n.py
#     """Publish msgstr (single line) into docutils document
#
#     :param sphinx.application.Sphinx app: sphinx application
#     :param unicode source: source text
#     :param unicode source_path: source path for warning indication
#     :param source_line: source line for warning indication
#     :param sphinx.config.Config config: sphinx config
#     :param docutils.frontend.Values settings: docutils settings
#     :return: document
#     :rtype: docutils.nodes.document
#     """
#     ...


# def _strip_basic_auth(url):
#     # From https://github.com/sphinx-doc/sphinx
#     # File: sphinx/ext/intersphinx.py
#     """Returns *url* with basic auth credentials removed. Also returns the
#     basic auth username and password if they're present in *url*.
#
#     E.g.: https://user:pass@example.com => https://example.com
#
#     *url* need not include basic auth credentials.
#
#     :param url: url which may or may not contain basic auth credentials
#     :type url: ``str``
#
#     :return: *url* with any basic auth creds removed
#     :rtype: ``str``
#     """
#     ...


def extract_original_messages(self):
    # From https://github.com/sphinx-doc/sphinx
    # File: sphinx/addnodes.py
    """Extract translation messages.

    :returns: list of extracted messages or messages generator
    """
    ...


def read_requirements(fh, resolve=False):
    # From https://github.com/pypa/pipenv
    # File: pipenv/patched/safety/util.py
    """
    Reads requirements from a file like object and (optionally) from referenced files.
    :param fh: file like object to read from
    :param resolve: boolean. resolves referenced files.
    :return: generator
    """  # noqa
    ...


def docstrings():
    """Get all of the docstrings in this file (including this one.)

    :return: The docstrings in this file.
    :rtype: List[str]

    """
    with open(__file__, 'r') as fin:
        data = fin.read()
    this_script = ast.parse(data)
    functions = [x for x in this_script.body
                 if isinstance(x, ast.FunctionDef)]
    return list(map(ast.get_docstring, functions))
