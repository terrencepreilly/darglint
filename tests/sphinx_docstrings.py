"""A collection of sphinx docstrings from the wild."""
import ast


def publish_msgstr(app, source, source_path, source_line, config, settings):
    # From https://github.com/sphinx-doc/sphinx
    # File: sphinx/transforms/il8n.py
    """Publish msgstr (single line) into docutils document

    :param sphinx.application.Sphinx app: sphinx application
    :param unicode source: source text
    :param unicode source_path: source path for warning indication
    :param source_line: source line for warning indication
    :param sphinx.config.Config config: sphinx config
    :param docutils.frontend.Values settings: docutils settings
    :return: document
    :rtype: docutils.nodes.document
    """
    ...
    # Expected item head to end with TokenType.COLON but was TokenType.WORD 'app' # noqa


def _strip_basic_auth(url):
    # From https://github.com/sphinx-doc/sphinx
    # File: sphinx/ext/intersphinx.py
    """Returns *url* with basic auth credentials removed. Also returns the
    basic auth username and password if they're present in *url*.

    E.g.: https://user:pass@example.com => https://example.com

    *url* need not include basic auth credentials.

    :param url: url which may or may not contain basic auth credentials
    :type url: ``str``

    :return: *url* with any basic auth creds removed
    :rtype: ``str``
    """
    ...


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


def copytree(self, destination, symlinks=False):
    # File: sphinx/testing/path.py
    """
    Recursively copy a directory to the given `destination`. If the given
    `destination` does not exist it will be created.

    :param symlinks:
        If ``True`` symbolic links in the source tree result in symbolic
        links in the destination tree otherwise the contents of the files
        pointed to by the symbolic links are copied.
    """
    # Expected item to start with TokenType.COLON but was TokenType.INDENT


def rmtree(self, ignore_errors=False, onerror=None):
    # File: sphinx/testing/path.py
    """
    Removes the file or directory and any files or directories it may
    contain.

    :param ignore_errors:
        If ``True`` errors are silently ignored, otherwise an exception
        is raised in case an error occurs.

    :param onerror:
        A callback which gets called with the arguments `func`, `path` and
        `exc_info`. `func` is one of :func:`os.listdir`, :func:`os.remove`
        or :func:`os.rmdir`. `path` is the argument to the function which
        caused it to fail and `exc_info` is a tuple as returned by
        :func:`sys.exc_info`.
    """
    # Expected item to start with TokenType.COLON but was TokenType.INDENT


def test_params(request):
    # File: sphinx/testing/fixtures.py
    """
    test parameters that is specified by 'pytest.mark.test_params'

    :param Union[str] shared_result:
       If the value is provided, app._status and app._warning objects will be
       shared in the parametrized test functions and/or test functions that
       have same 'shared_result' value.
       **NOTE**: You can not specify shared_result and srcdir in same time.
    """
    # Expected item head to end with TokenType.COLON but was TokenType.WORD 'shared_result'


def add_uids(doctree, condition):
    # File: sphinx/versioning.py
    """Add a unique id to every node in the `doctree` which matches the
    condition and yield the nodes.

    :param doctree:
        A :class:`docutils.nodes.document` instance.

    :param condition:
        A callable which returns either ``True`` or ``False`` for a given node.
    """
    # Expected item to start with TokenType.COLON but was TokenType.INDENT


def merge_doctrees(old, new, condition):
    # File: sphinx/versioning.py
    """Merge the `old` doctree with the `new` one while looking at nodes
    matching the `condition`.

    Each node which replaces another one or has been added to the `new` doctree
    will be yielded.

    :param condition:
        A callable which returns either ``True`` or ``False`` for a given node.
    """
    # Expected item to start with TokenType.COLON but was TokenType.INDENT


def _read_from_url(url, config=None):
    # File: sphinx/ext/intersphinx.py
    """Reads data from *url* with an HTTP *GET*.

    This function supports fetching from resources which use basic HTTP auth as
    laid out by RFC1738 § 3.1. See § 5 for grammar definitions for URLs.

    .. seealso:

       https://www.ietf.org/rfc/rfc1738.txt

    :param url: URL of an HTTP resource
    :type url: ``str``

    :return: data read from resource described by *url*
    :rtype: ``file``-like object
    """
    # Expected item to start with TokenType.COLON but was TokenType.NEWLINE


def _get_safe_url(url):
    # File: sphinx/ext/intersphinx.py
    """Gets version of *url* with basic auth passwords obscured. This function
    returns results suitable for printing and logging.

    E.g.: https://user:12345@example.com => https://user@example.com

    :param url: a url
    :type url: ``str``

    :return: *url* with password removed
    :rtype: ``str``
    """
    # Expected item to start with TokenType.COLON but was TokenType.NEWLINE


def find_catalog_source_files(*args):
    # File: sphinx/util/i18n.py
    """
    :param list locale_dirs:
       list of path as `['locale_dir1', 'locale_dir2', ...]` to find
       translation catalogs. Each path contains a structure such as
       `<locale>/LC_MESSAGES/domain.po`.
    :param str locale: a language as `'en'`
    :param list domains: list of domain names to get. If empty list or None
       is specified, get all domain names. default is None.
    :param boolean gettext_compact:
       * False: keep domains directory structure (default).
       * True: domains in the sub directory will be merged into 1 file.
    :param boolean force_all:
       Set True if you want to get all catalogs rather than updated catalogs.
       default is False.
    :return: [CatalogInfo(), ...]
    """
    # Expected item head to end with TokenType.COLON but was TokenType.WORD 'locale'


def get_full_module_name(node):
    # File: sphinx/util/nodes.py
    """
    return full module dotted path like: 'docutils.nodes.paragraph'

    :param nodes.Node node: target node
    :return: full module dotted path
    """
    # Expected item head to end with TokenType.COLON but was TokenType.WORD 'node'


def set_application(self, app):
    # File: sphinx/parsers.py
    """set_application will be called from Sphinx to set app and other instance variables

    :param sphinx.application.Sphinx app: Sphinx application object
    """
    # Expected item head to end with TokenType.COLON but was TokenType.WORD 'app'


def write_bytes(sef, bytes, append=False):
    # File: sphinx/testing/path.py
    """
    Writes the given `bytes` to the file.

    :param append:
        If ``True`` given `bytes` are added at the end of the file.
    """
    # Expected item to start with TokenType.COLON but was TokenType.INDENT


def repr_domxml(node, length=80):
    # File: sphinx/util/nodes.py
    """
    return DOM XML representation of the specified node like:
    '<paragraph translatable="False"><inline classes="versionmodified">New in version...'

    :param nodes.Node node: target node
    :param int length:
       length of return value to be striped. if false-value is specified, repr_domxml
       returns full of DOM XML representation.
    :return: DOM XML representation
    """
    # Expected item head to end with TokenType.COLON but was TokenType.WORD 'node'


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
