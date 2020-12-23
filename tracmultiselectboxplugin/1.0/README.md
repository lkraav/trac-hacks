Notes
=====

[TracMultiSelectBoxPlugin](https://trac-hacks.org/wiki/TracMultiSelectBoxPlugin "TracMultiSelectBoxPlugin")
treats pseudo multipul select values with the ticket custom field.

Note: TracMultiSelectBoxPlugin requires Trac 1.0 or higher since it uses
the **list** format of text type. ([TracTicketsCustomFields](http://trac.edgewall.org/wiki/TracTicketsCustomFields "TracTicketsCustomFields"))


Features
--------

* Provide simple multiple select values field

As compared to other alternatives,
this plugin is intended to be simple and light weight, easy to use.


Configuration
=============

To use multiple select values like this:

    [components]
    multiselectbox.filter.multiselectbox = enabled

    [ticket-custom]
    multiselectfield = text
    multiselectfield.format = list
    multiselectfield.label = my custom field
    multiselectfield.multiple = true
    multiselectfield.options = foo bar baz  ; each value is delimited with space
    multiselectfield.size = 4               ; size attribute passed to select tag
    multiselectfield.value = bar            ; default value when new ticket is created


Operation Tips
==============

revert function
---------------

To revert multiple select values during you are editing.
Unfortunately, Trac don't care about it. (confirmed 1.0.2) 
To use Trac's revert function,
you must apply a patch included in the source distribution.

    $ cd path/to/trac
    $ patch -p0 < patch/support-multipleselct-for-reverthandler-trac10.patch
    $ restart Trac


Acknowledgment
==============

This plugin was inspired by [MultiSelectFieldPlugin](http://trac-hacks.org/wiki/MultiSelectFieldPlugin "MultiSelectFieldPlugin").
MultiSelectFieldPlugin is good choice if you're finding more rich selectbox.
