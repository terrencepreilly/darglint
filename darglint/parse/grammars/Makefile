
IMPORTS = "from darglint.parse.grammar import BaseGrammar\nfrom darglint.parse.grammar import Production as P\nfrom darglint.token import TokenType\nfrom darglint.parse.identifiers import (\n    ArgumentIdentifier,\n    ArgumentTypeIdentifier,\n    ExceptionIdentifier,\n    NoqaIdentifier,\n    ArgumentItemIdentifier,\n    ExceptionItemIdentifier,\n)\n\n"

sections = google_arguments_section.py \
		   google_long_description.py \
		   google_raises_section.py \
		   google_returns_section.py \
		   google_returns_section_without_type.py \
		   google_short_description.py \
		   google_types.py \
		   google_yields_section.py \
		   sphinx_argument_type_section.py \
		   sphinx_arguments_section.py \
		   sphinx_base.py \
		   sphinx_long_description.py \
		   sphinx_raises_section.py \
		   sphinx_returns_section.py \
		   sphinx_return_type_section.py \
		   sphinx_short_description.py \
		   sphinx_variable_type_section.py \
		   sphinx_variables_section.py \
		   sphinx_yields_section.py

all: $(sections)

%.py: %.bnf
	bnf_to_cnf -o _$@ $< && \
		echo $(IMPORTS) > $@ && \
		cat _$@ >> $@ && \
		rm _$@

clean:
	rm $(sections)
