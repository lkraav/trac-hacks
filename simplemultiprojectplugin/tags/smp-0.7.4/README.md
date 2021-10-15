# Simple Multi Project Plugin

[SimpleMultiProjectPlugin](https://trac-hacks.org/wiki/SimpleMultiProjectPlugin) lets you easily manage multiple user projects with one Trac instance. This is not a meta project in front of several other Trac projects. It implements the idea of a SingleEnvironment. 

## Key features
* Milestones, versions and components can be assigned to all or certain projects 
* Milestones and versions are displayed on the _Roadmap_ page and can be grouped by project
* On the roadmap page and timeline page it is possible to apply filters to show only projects that meet certain criteria.
* _New Ticket_ will just offer the associated milestones, versions and components of the chosen project. This requires a new custom-ticket field _project_.
* Restrict access to certain milestones, versions and tickets by defining members or non-members of a project. 

## Integration with other plugins
[MultiProjectBacklogPlugin](https://trac-hacks.org/wiki/MultiProjectBacklogPlugin) integrates with this plugin allowing you to maintain project specific backlogs in your agile process.

## Source
You can check out [SimpleMultiProjectPlugin](https://trac-hacks.org/wiki/SimpleMultiProjectPlugin) from [here](https://trac-hacks.org/svn/simplemultiprojectplugin) using Subversion, or [browse the source](https://trac-hacks.org/browser/simplemultiprojectplugin) with Trac.

Download the zipped source from the [Homepage](https://trac-hacks.org/wiki/SimpleMultiProjectPlugin) or [Pypi](https://pypi.python.org/pypi/TracSimpleMultiProject).

## Installation
**Note:** The plugin doesn't use Genshi for Trac 1.4+.

* Add a custom ticket field 'project' to your trac.ini file to give tickets the information to which project they belong. Milestones selection depends on that as well.
  ```
  [ticket-custom]
  project = select
  project.label = Project
  project.value =
  ```

* Give permissions to certain users. Available permissions are:
  * ```PROJECT_SETTINGS_VIEW``` - you can see the list of projects with their description and their component mapping on the admin panel
  * ```PROJECT_ADMIN``` - full admin access, you can also create and delete projects, and map to milestones, versions and components

* Add the new policy ```SmpPermissionPolicy``` to the front of your permission policy provider list to enable project permission checks for users.
  ```
  [trac]
  permission_policies = SmpPermissionPolicy, ... any other ...
  ```

## Configuration
The plugin comes with sane default values, but if you have specific requirements you may change some configuration options using the Trac admin web interface.

## Set project permissions for users
A new permission system is implemented by a new permission policy ```SmpPermissionPolicy``` and additional request filtering. The latter is necessary because [TracFineGrainedPermissions](https://trac.edgewall.org/wiki/TracFineGrainedPermissions) are limited to some resources, notably excluding versions and components.

For permission checking and proper filtering the permission policy plugin must be activated and configured in trac.ini:
```
[trac]
permission_policies = SmpPermissionPolicy, ... any other ...
```
Make sure the new policy is the first in the list of available policies.

You may mark a project as restricted on the project admin page which has the following effects.

* Tickets linked with a restricted project can't be accessed by users without permissions. 
  
  This works for individual ticket pages, ticket queries, the timeline page and everywhere else a ticket is shown.

*  Milestones belonging to restricted projects can't be accessed without permissions. 

   This affects ticket queries, the roadmap and timeline pages and individual ticket pages.

* Components and versions of restricted projects are not available for queries or when creating/modifying ticket pages.

Projects without restrictions and their linked resources can be accessed by any user. Normal Trac permission settings apply.

Project permissions are assigned using the Trac permission admin panel. Each project has a unique ID which is not changing over the lifetime of a project, even if you change the project name.
To give a user access to a project you have to give the permission ```PROJECT_<id>_MEMBER``` where ```<id>``` is the unique project id. For finer control over individual resources the normal Trac permissions are available.

This means a project permission is a coarse filter to only prevent global project resources access. You can't have individual fine grained resource access for different projects (like ```TICKET_VIEW```) because normal Trac permissions are defined for all projects. Use TracFineGrainedPermissions if you need such control.

## Authors
Christopher Paredes, falkb, Cinc-th, Ryan J Ollos
