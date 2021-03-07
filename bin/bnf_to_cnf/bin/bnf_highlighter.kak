# A highlighter for the BNF syntax used here. This could probably be improved by
# doing something like adding a specific highlighter for assignment vs.
# references. But it's good enough for now.

provide-module bnf-highlighter %&
    add-highlighter shared/bnf regions
    add-highlighter shared/bnf/ region '#' '\n' fill comment
    add-highlighter shared/bnf/ region '"' '"' fill string

    add-highlighter shared/bnf/other default-region group
    add-highlighter shared/bnf/other/ regex [a-zA-Z_][a-zA-Z_0-9]+ 0:module
    add-highlighter shared/bnf/other/ regex <[a-zA-Z_][a-zA-Z\-_0-9]*> 0:variable
    add-highlighter shared/bnf/other/ regex @[a-zA-Z_][a-zA-Z_0-9]* 0:meta
    add-highlighter shared/bnf/other/ regex \b(from|import|grammar|start)\b 0:keyword
    add-highlighter shared/bnf/other/ regex \B(::=|\||:|,)\B 0:operator
    add-highlighter shared/bnf/other/ regex \b[0-9]+\b 0:value
    add-highlighter shared/bnf/other/ regex "ε" 0:value
&

hook global WinSetOption filetype=bnf %{
    require-module bnf-highlighter
    add-highlighter window/bnf ref bnf
    hook -once -always window WinSetOption filetype=.* %{
        remove-highlighter window/bnf
    }
}

hook global BufCreate .+\.bnf %{
    set-option buffer filetype bnf
}
