
IMPORTS = "from darglint.parse.grammar import BaseGrammar\nfrom darglint.parse.grammar import Production as P\nfrom darglint.token import TokenType\n"

sections = google_raises_section.py \
		   google_arguments_section.py \
		   google_yields_section.py \
		   google_returns_section.py \
		   google_short_description.py \
		   google_types.py \
		   google_long_description.py

all: $(sections)

%.py: %.bnf
	bnf_to_cnf -o _$@ $< && \
		echo $(IMPORTS) > $@ && \
		cat _$@ >> $@ && \
		rm _$@

clean:
	rm $(sections)
