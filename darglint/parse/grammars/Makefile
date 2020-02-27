
sections = google_arguments_section.py \
		   google_long_description.py \
		   google_raises_section.py \
		   google_returns_section.py \
		   google_returns_section_without_type.py \
		   google_short_description.py \
		   google_yields_section.py \
		   google_yields_section_without_type.py \
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
		   sphinx_yields_section.py \
		   sphinx_yield_type_section.py \
		   numpy_arguments_section.py \
		   numpy_long_description.py \
		   numpy_other_arguments_section.py \
		   numpy_raises_section.py \
		   numpy_receives_section.py \
		   numpy_returns_section.py \
		   numpy_short_description.py \
		   numpy_warns_section.py \
		   numpy_yields_section.py

all: $(sections)

%.py: %.bnf
	bnf_to_cnf -o $@ $<

clean:
	rm $(sections)
