# Description

IncludeSourcePartialPlugin  allows source files to be partially or wholly
included in other wiki content.

# Samples

Include entire file:
> [[IncludeSource(trunk/proj/file.py)]]

Includes line 20-50 inclusive:
> [[IncludeSource(trunk/proj/file.py, start=20, end=50)]]

Includes line where "pattern" is found to first line + 20:
> [[IncludeSource(trunk/proj/file.py, start=pattern, end=20)]]

Includes line where "pattern1" is found to line where pattern2 is found:
> [[IncludeSource(trunk/proj/file.py, start=pattern1, end=pattern2)]]

Includes last 30 lines of file at revision 1200:
> [[IncludeSource(trunk/proj/file.py, start=-30, rev=1200)]]

Include entire file but formatted plain:
> [[IncludeSource(trunk/proj/file.py, mimetype=text/plain)]]

For docs on installation, configuration, and examples, please refer to
https://trac-hacks.org/wiki/IncludeSourcePartialPlugin
