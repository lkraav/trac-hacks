TracWikiPrintPlugin
===================
This plugin allows you to export to PDF (book or article format) or printable HTML format (page contents without Trac headers/footers) allowing easy printing. PDF export is based on [wkhtmltopdf](https://wkhtmltopdf.org/).

Older versions up to V3.0.0 used [xhtml2pdf](http://www.xhtml2pdf.com/) for generating PDF files. While having the advantage of being a pure Python solution it was abandoned because the output quality of [wkhtmltopdf](https://wkhtmltopdf.org/) is way better. For these unsupported older releases see [WikiPrintXhtml2pdf](https://trac-hacks.org/wiki/TracWikiPrintPlugin/WikiPrintXhtml2pdf).

Key features:

* Administration page for default settings.
* Customizable footers for PDF.
* Customizable front page for PDF book format.
* Automatic creation of Table of Contents for PDF books.
* The style of the resulting PDF or HTML can be fully customized using CSS.
* Different page sizes.
* PDF "print dialog" for altering settings prior to PDF file creation.
* Makro to specify contents and format of PDF Books with export feature.

The plugin is seamlessly integrated in the Trac user interface by adding items to the `Download in other formats` section of each wiki page.

The full documentation can be found on the homepage: [TracWikiPrintPlugin](https://trac-hacks.org/wiki/TracWikiPrintPlugin) (https://trac-hacks.org/wiki/TracWikiPrintPlugin)

### Supported Trac releases

Trac 1.4 and 1.6 are fully supported.

For older releases use TracWikiPrintPlugin V3.x.x or older.

License
-------

Releases up to V3.x.x were licensed as GPL.

With V4.0.0 the plugin was rewritten from scratch and is now BSD licensed.

Download
--------
Download the zipped source from [here](https://trac-hacks.org/browser/tracwikiprintplugin?format=zip).

Source
------
You can check out [TracWikiPrintPlugin](https://trac-hacks.org/wiki/TracWikiPrintPlugin) from [here](https://trac-hacks.org/svn/tracwikiprintplugin) using Subversion, or [browse the source](https://trac-hacks.org/browser/tracwikiprintplugin) with Trac.

Installation
------------
To install the plugin from trunk:

    $ pip install https://trac-hacks.org/svn/tracwikiprintplugin/trunk

To install the older `V3.0.0` release:

    $ pip install https://trac-hacks.org/svn/tracwikiprintplugin/tags/V3.0.0

Install [wkhtmltopdf](https://wkhtmltopdf.org/). 

*Note:* [wkhtmltopdf](https://wkhtmltopdf.org/) must be in your path or more precisely in the path used by Trac.

Enable the plugin using Tracs plugin administration page or by adding `wikiprint.* = enabled` in the components section of your `trac.ini` file:

```
[components]
...
wikiprint.* = enabled
```

Usage
-----

After the plugin is enabled, a new administration panel will be available under the `Wikiprint` section, and 4 new download formats will be available in the `Download in other formats` section at the end of each wiki page:

* Printable HTML
* PDF Page
* PDF Page (custom settings)
* PDF Book

A new makro `PdfBook` can be used to create PDF books from any number of wiki pages.

### Administration page

The default configuration for page exports may be provided using the `Wikiprint` administration page. These settings apply when not overriden by the user while exporting a PDF. While most settings are related to PDF files the style page specified here also applies when generating the `Printable HTML` page.

### Printable HTML

The wiki page is stripped from Tracs footer, header and navigation. The resulting page only contains the wiki content.

Styling of the page is according to the style page selected using the administration panel.

### PDF Page

`PDF Page` creates a PDF file out of the wiki page, with no cover page. Styles will be used from the style page defined in the global configuration set with the administration panel.

Table of contents macros in the wiki page like `[[PageOutline()]]` or others are not stripped from the page.

### PDF Page (custom settings)

The wiki page is exported as a PDF file. This is like normal `PDF Page` export but it is possible to override the global configuration while generating the PDF file. A settings page similar to a "print dialog" is presented to the user before the actual export happens.

### PDF Book

This will create a book-like PDF document. While exporting the user is presented with a settings page to specify a cover page and whether a table of contents should be added. Styling may be changed by selecting one of the available style page. The cover page used for the book may be any wiki page.

Common table of contents macros in the wiki page like `[[PageOutline()]]` or `[[TracGuideToc()]]` are removed from each wiki page.

### PdfBook makro

Using the makro it is possible to define PDF books with any number of wiki pages a cover page and table of contents. The configuration specified in the makro may always be overriden by the user while creating the book. This way one may for example change the predefined cover page or omitt the table of contents. Note that you can't add or remove pages while creating the book.

The configuration from the makro is rendered to the user and a button added to create the PDF book. Note that only one PdfBook makro on a wiki page is supported.

The makro must be specified in WikiProcessors syntax:

```
{{{#!PdfBook
...
}}}
```

The contents must be formatted like an INI file. The following sections are defined:

* `[parameters]`: specify cover page and table of contents
* `[pages]`: list of wiki pages to add to the book.

```
{{{#!PdfBook
[parameters]
# Name of a wiki page to be used as the cover page
cover = CoverPage
# Set to 1 for a table of contents, else set to 0
toc = 1

[pages]
# Names of wiki pages to be added to the PDF book.
WikiStart
WikiFormatting
}}}
```
