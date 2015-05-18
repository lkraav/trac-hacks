SVN MULTI URLs
==============

= show SVN MULTI URL links in /browser =

This Plugin was created with input from the SVNURLs Plugin created by kOs
http://trac-hacks.org/wiki/SvnUrlsPlugin
k0s stopped maintaining his plugin, so I,ve created this plugin.

== Description ==

The SvnMultiUrlsPlugin provides links to the url of repository files as
viewable at /browser  This enables easy reference to the
actual svn entities for svn operations To make this work, you will
have to add a section in the trac.ini for your project.
Using the new multiple subversion repisitories from Trac.0.12.x .

{{{
[components]
svnmultiurls.* = enabled
}}}


{{{
[svnmultiurl]
repository_root_url = /svn
}}}
or
{{{
[svnmultiurl]
repository_root_url = http://host/svn
}}}

The name of the repositories must be exactly the same like the directory name of
the repository directory !

Delete also the deprecated pramater "repository_dir" from trac.ini !

Optionally, you may also add an entry to this section controlling what
text
is displayed:

{{{
[svnmultiurl]
link_text = [svn]
}}}


== Bugs/Feature Requests == 

Existing bugs and feature requests for SvnMultiUrlsPlugin are
[query:status!=closed&component=SvnMultiUrlsPlugin&order=priority here].

If you have any issues, create a 
[/newticket?component=SvnMultiUrlsPlugin&owner=podskalsky new ticket].

== Download and Source ==

Download the [download:svnmultiurlsplugin zipped source], check out
[/svn/svnmultiurlsplugin using Subversion], or [source:svnmultiurlsplugin browse
the source] with Trac.

== Example ==

See http://trac.openplans.org/openplans/browser . The {{{[svn]}}}
links in the image below point to the http svn location of the
relevant resources:

[[Image(svnurls.png)]]

== How SVN MULTI URLs Works ==

svnmultiurls filters the outgoing stream using ITemplateStreamFilter.  This
requires the latest version of genshi.  Running {{{python setup.py
[develop|install]}}} should pull down the correct version 
