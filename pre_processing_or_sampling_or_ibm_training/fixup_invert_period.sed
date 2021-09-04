s/__*[a-zA-Z0-9:-]*//
s/[.]/ period/g
s/,/ comma/g
s/[/]/ slash /g
s/YYYY//g
s/yyyy//g
s/xxx//g
s/xx//g
s/XXXXX//g
s/xxxx//g
s/\(period\) \([[:upper:]]\)/\1\
\2/g
