# Subversion connector for remote and local repositories using the svn command line client
## Description
This plugin allows you to connect to remote and/or local subversion repositories. It uses the subversion command line client {{{svn}}} so no subversion-python bindings need to be installed which sometimes can be a daunting task.

The plugin provides a connector with caching and a direct connector without.

The latter is useful if you want to quickly or maybe just temporarily provide access to a (remote) repository.
Initial viewing of large trees with the direct connector is slow especially for remote http:/https: repositories like https://trac-hacks.org/svn. Same for very large changesets.
Nevertheless working with subtrees (like https://trac-hacks.org/svn/peerreviewplugin) is going well.

## Status
The following bugs are known:
* Context navigation for *Next Revision* doesn't work
* No caching for subtree repositories (local mirrors of subtrees do work, though)

The plugin was tested with *Subversion 1.10.3*.

## Installation
Enable the plugin from the Trac plugin admin page or by adding the following to your
 `trac.ini` file:

    [components]
    subversioncli.svn_cli.* = enabled

The subversion client `svn` must be in your path.

## Configuration
Use the Trac repository admin page to configure a repository.

There are two connector types available:
* `svn-cli` caching connector for local and remote repositories
* `svn-cli-direct` direct connector for local and remote repositories

### Local repository
For local repositories you have to provide an ''absolute path'' to the repository directory.

    /path/to/local/repo

or when using Windows

    x:/path/to/local/repo

For local repositories you have to provide an _absolute path_ to the repository
directory.
### Remote repository
There is no native support for remote subversion repositories in Trac. The admin
page checks if an entered path is a local one, more specifically if it's an
absolute one. The path doesn't have to exist, though.

We have to trick Trac into accepting a Url by prepending it with a slash `/` (or
`x:/` when running Trac on Windows) like this:

    /https://trac-hacks.org/svn
or

    x:/https://trac-hacks.org/svn

### Subtree as repository
You may create a repository for a subtree of some larger repository. This may be useful if a repository contains a lot of independent projects like for example here at https://trac-hacks.org.

As an example use this directory path to create a repository for the project PeerReviewPlugin:

    /https://trac-hacks.org/svn/peereviewplugin

Chose `svn-cli-direct` as connector.

There is currently no caching available for remote subtree repositories.
 You have to mirror a subtree to your local system using `svnsync` if you need caching. See here: https://trac.edgewall.org/wiki/TracMigrate#SubversionReplication  

### Hints
Set the following in your *trac.ini*:

    [timeline]
    changeset_show_files = 0

This speeds up the display of the timeline because less information must be queried.
