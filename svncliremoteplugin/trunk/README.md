# Subversion connector for remote and local repositories using the svn command line client
## Description
This plugin allows you to connect to remote and/or local subversion repositories.
It uses the subversion command line client svn so no subversion-python bindings
need to be installed which sometimes can be a daunting task.

This is a direct connector without any caching so initial viewing of large trees
is slow especially for remote Http:/Https: repositories like https://trac-hacks.org/svn.
Nevertheless working with subtrees like https://trac-hacks.org/svn/peerreviewplugin is
 going well.

## Status
Note that this plugin is in early development so many bugs exists and features are
still missing.
* No support for properties
* No preview for certain files containing unicode characters
* Context navigation for Next Revision doesn't work
* Navigation over svn-copied files is flaky
* No caching 

## Configuration
Use the Trac repository admin page to configure a repository.

There are two connector types available:
* `svn-cli-direct` for local repositories
* `svn-cli-remote` for remote repositories like _http:_ or _https:_

### Local repository
For local repositories you have to provide an _absolute path_ to the repository
directory.

Choose `svn-cli-direct` as connector.

### Remote repository
There is no native support for remote subversion repositories in Trac. The admin
page checks if an entered path is a local one, more specifically if it's an
absolute one. The path doesn't have to exist, though.

We have to trick Trac into accepting a Url by prepending it with a slash `/` (or
`x:\ ` when running Trac on Windows) like this:

    /https://trac-hacks.org/svn

or

    x:\https://trac-hacks.org/svn

Choose `svn-cli-remote` as connector.
