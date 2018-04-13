TracGoogleSearch
================

TracGoogleSearch_ is a trac_ plugin which enables your trac_ environment to
use Google_'s Adsense_ For Search on the mini search box displayed on top.

**Note:** Regular trac_ search won't be disabled, the users must click the
*"Search"* button to access it, and will only show up and work if user has
``SEARCH_VIEW`` permissions, unlike this plugin, which does not
require any special permissions since it's querying Google_ not trac_.

Installation
------------
Installing the plugin is as easy as::

  sudo easy_install TracGoogleSearch

And then enabling it:

.. sourcecode:: ini

  [components]
  tracext.google.search.* = enabled

And that's it!

Configuration
-------------
In order to use this plugin you must first create a custom search engine on
your Adsense_ account, configure it like you want it and choose to display
the results on a page on your own website.

If you wish Google_ to show results relative to the domain of your trac_
environment, on your Adsense_ account, edit your search engine settings, choose
*"view more advanced features"*, select *"Search the entire web but emphasize
included sites"* and then under *"Sites"* add your trac_ environment domain.

From the resulting code that Google_ provides we'll need the values from the
hidden fields named, **cx** and **cof**, ie, your client id and search id
strings.

Consider the following example code:

.. sourcecode:: html

  <form action="http://domain.tld/gsearch" id="cse-search-box">
    <div>
      <input type="hidden" name="cx" value="partner-pub-0000000000000000:0aaaa0aaa00a" />
      <input type="hidden" name="cof" value="FORID:1" />
      <input type="hidden" name="ie" value="UTF-8" />
      <input type="text" name="q" size="31" />
      <input type="submit" name="sa" value="Search" />
    </div>
  </form>
  <script type="text/javascript"
          src="http://www.google.com/coop/cse/brand?form=cse-search-box&lang=en"></script>


The values you'll need to remember would be
**partner-pub-0000000000000000:0aaaa0aaa00a** and **FORID:1**, the rest of the
code will be provided by the plugin.

The plugin can then be configured on trac_'s administration panel, under the
section **Google** and then **Search**.

Bugs and/or New Features
------------------------

Please submit bugs of new features to::

  http://google.ufsoft.org/


Source Code
-----------

If you wish to be on the bleeding edge and get the latest available code:

.. sourcecode:: sh

  hg clone http://google.ufsoft.org/hg/search/ TracGoogleSearch


**Note**: For up-to-date documentation please visit TracGoogleSearch_'s site.


.. _trac: http://trac.edgewall.org
.. _TracGoogleSearch: http://google.ufsoft.org/wiki/TracGoogleSearch
.. _Google: http://www.google.com
.. _Adsense: https://www.google.com/adsense/
