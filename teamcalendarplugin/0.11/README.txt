====================
Team Calendar Plugin
====================

This plugin adds a new tab, Team Calendar, to users with the TEAMCALENDAR_VIEW
permission. This shows a simple tables with dates running down the rows
and team members across the columns. Users with TEAMCALENDAR_UPDATE_OWN
permissions can change the state of the tick boxes under their own name,
and save the results. Users with TEAMCALENDAR_UPDATE_OTHERS permission can
update everyone's.

The plugin requires a table `team_availability` that needs to be created manually and goes into the same database that Trac is using.

For MySQL, the table can be created as follows:

    CREATE TABLE `team_availability` (
      `username` VARCHAR(255) NOT NULL DEFAULT '',
      `ondate` DATE NOT NULL DEFAULT '0000-00-00',
      `availability` FLOAT UNSIGNED DEFAULT NULL,
      PRIMARY KEY (`username`, `ondate`)
    );

For PostgreSQL, the table can be created as follows:

    CREATE TABLE team_availability (
       username VARCHAR(255) NOT NULL DEFAULT '',
       ondate DATE NOT NULL,
       availability FLOAT DEFAULT NULL,
       PRIMARY KEY (username, ondate)
    );

For Sqlite3, the database and table can be created as follows:

    $ sqlite3 trac.db

    CREATE TABLE team_availability (
       username TEXT NOT NULL DEFAULT '', 
       ondate DATE NOT NULL DEFAULT (DATETIME('now')), 
       availability FLOAT DEFAULT NULL, 
       PRIMARY KEY (username, ondate)
    );

The 'availability' column will contain 0 or 1 if populated through the GUI.
It is left as a float to make it possible to store more granular availability,
e.g. half-day, but there is no UI for this at present.

The calendar does not do anything more by itself. However, the 
team_availability table can be used in reports.

Installation
------------

Install using 'setup.py install' or easy_install as normal, and then
enable in trac.ini with:

    [components]
    teamcalendar.* = enabled

If you want to use a different table name than 'team_availability', add::

    [team-calendar]
    table_name = some_name

If you want to display more or fewer weeks before or after the current week
by default, add::

    [team-calendar]
    weeks_prior = 2
    weeks_after = 3
