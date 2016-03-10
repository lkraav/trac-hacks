MultiProjectBacklog
===================

This plugin is derived from TracBacklog plugin:

    https://trac-hacks.org/wiki/TracBacklogPlugin

with last commit

    https://github.com/jszakmeister/trac-backlog/commit/6e76f506351847189dcbfb26bfcad7889aa76f24

from 2013-10-15. The code from the pull request

    https://github.com/jszakmeister/trac-backlog/pull/12

which adds support for ticket custom fields is included. Some interface
improvements and bug fixes went into the code. The codebase was
updated to support modern Trac concepts introduced with V0.12 and V1.0.

It supports multiple projects when using SimpleMultiProjectPlugin. Note that
you may also use this plugin without multiple projects. That means you don't need
to have SimpleMultiProjectPlugin installed.

This plugin is meant to help you with your agile process using Trac.  One of
the key practices of agile development, is prioritizing the backlog.  That
can be difficult to do in Trac, as it doesn't have any way of doing
fine-grained ranking of tickets.  This plugin helps resolve that
short-coming.

MultiProjectBacklog adds a new navigational element to your navigation bar.
Clicking on it will take you to the unscheduled backlog (all active tickets
of a project that aren't currently assigned to a milestone).  On the right hand side,
is a listing of open milestones.  The idea is that you drag-n-drop tickets
within the list itself to change their rank.  Once you're happy with the
ranking (i.e., you've worked with your customer to prioritize the outstanding
tickets), you drag-n-drop tickets onto a milestone to assign it into the
milestone.  This effectively treats milestones as sprints.

The unscheduled backlog is created from tickets that are not assigned
to any milestone.  You can also view each milestone and see and individual
backlog for it, but all tickets are ranked absolutely (they maintain their
absolute ranking when you drag them in and out of a milestone).  Furthermore,
if you are trying this on an existing project, the initial rank for each
ticket will be it's ticket id.  You'll want to spend some time sorting your
tickets, and you may want to consider pulling them all into the unscheduled
backlog when you do that (so that you can order the all the tickets against
each other).

By using the project drop down list on the top right you may switch your
project. Only tickets and milestones assigned to that project are shown.

Dependencies
------------

It requires Trac 1.0 or better.


Installation
------------

Follow the standard Trac ​plugin installation instructions:

    https://trac.edgewall.org/wiki/TracPlugins

Enable the plugin in trac.ini:

    [components]
    multiprojectbacklog.* = enabled

You need to run {{{trac-admin <path/to/env> upgrade}}} on your database, since the
plugin needs to create a table and some default values for your ticket ordering.

Configuration
-------------

Users can customize the columns they see in the Backlog preference pane. On the
backlog page the user may individually select more columns to be shown or hidden. The
preferences affect the initial page state.

Bugs/Feature Requests
---------------------

Please use issue list at

    https://trac-hacks.org/wiki/MultiProjectBacklogPlugin

to file any bugs and feature requests.

Source
------

The plugin is maintained on

    https://trac-hacks.org/wiki/MultiProjectBacklogPlugin


Other Solutions
---------------

See also:

TracBacklog: https://github.com/jszakmeister/trac-backlog
TracKanbanBoard: https://pypi.python.org/pypi/TracKanbanBoard/0.2
BacklogPlugin: https://trac-hacks.org/wiki/BacklogPlugin
AgiloForTracPlugin: https://trac-hacks.org/wiki/AgiloForTracPlugin
IttecoTracPlugin: https://trac-hacks.org/wiki/IttecoTracPlugin
