
IMPORTS = "from darglint.parse.grammar import BaseGrammar\nfrom darglint.parse.grammar import Production as P\nfrom darglint.token import TokenType\n"


google.py: google2.py
	echo $(IMPORTS) > google.py && cat google2.py >> google.py

google2.py: google.bnf
	bnf_to_cnf -o google2.py google.bnf
