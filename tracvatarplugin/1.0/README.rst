==========
tracvatar
==========

Adds avatar icons provided by either `Gravatar <http://www.gravatar.com/>`_  or
`Libravatar <http://libravatar.org>`_ to Trac.

Credit goes to the `HackergotchiPlugin <http://trac-hacks.org/wiki/HackergotchiPlugin>`_ for
some general ideas.

Ideally, Trac itself would just include support for author avatars
as a built in, since this is an extremely common and desirable feature.

For now, the approach of the plugin is to filter specific Trac views,
gather all the authors found in the "data" hash being passed to
Genshi, then using Genshi filters to insert additional avatar nodes.

Currently supported views are:

* Timeline
* Issue display
* Issue change display (i.e. comments, attachments)
* Source browser listing (tested for svn and hg so far)
* Individual changeset page (tested for svn and hg so far)
* User prefs page (includes link to "change your avatar" at
  gravatar.com/libravatar.org)

Installation
============

To install, just use ``python setup.py bdist_egg`` to create an egg file which
then goes into the Trac ``plugins/`` folder, or just ``python setup.py install``
to plug it in entirely.

Configuration
=============

To enable the plugin in trac.ini::

    [components]
    tracvatar.* = enabled

There are then available optional "size" settings for each view, shown
below are defaults::

    [tracvatar]
    ticket_reporter_size = 60
    ticket_comment_size = = 40
    timeline_size = 30
    browser_lineitem_size = 20
    browser_changeset_size = 40
    prefs_form_size = 40
    avatar_default = default
    backend = gravatar
    metanav_size = 30



