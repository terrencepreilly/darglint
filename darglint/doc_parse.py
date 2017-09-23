"""Parses a google-style docstring."""


# Pseudocode
#
# A docstring is expected to be in the following format:
#
#    <docstring > ::= <doc-term><content><doc-term>
#        | <doc-term><explanation><newline>
#              (<explanation-section><newline>)?
#              <arguments-section>?
#              (<return-section>|<yield-section>)?
#          <doc-term>
#    <yield-section> ::= Yields: <explanation>+<newline>
#    <return-section> ::= Returns: <explanation>+<newline>
#    <arguments-section> ::= Args:<newline><argument>+
#    <argument> ::= <name>: <explanation>[<indent><explanation>]*
#    <name> ::= \w[\w\d\_]*
#    <explanation-section> ::= [explanation]+<newline>
#    <explanation> ::= [<content><newline>]+
#    <newline> ::= '\n'
#    <indent> ::= '    '
#    <content> ::= '\w', '\ ', or special characters
#    <doc-term > ::= """
