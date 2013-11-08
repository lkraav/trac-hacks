# About
This Trac plugin allows you to specify additional JS or CSS files that
should be included via the `trac.ini`

e.g.

    [inherit]
    htdocs_dir = /path/to/chrome/shared

    [static_resources]
    ticket = jquery.autolink.js, our-styles.css
    wiki = our-styles.css

Will add to urls with `ticket` in them the js and css file and to
`wiki` the css file. These files should be on the filesystem in the
directory specified by `htdocs_dir` (standard trac config element).



# Origin

This is a fork of http://www.trac-hacks.org/wiki/AddStaticResourcesPlugin
rewritten for trac 1.0 (needs to do less).

# License

The MIT License (MIT)

Copyright (c) 2013 Nathan Bird, Russ Tyndall, Accelerated Data Works dba Acceleration.net

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
