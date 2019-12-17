Resource Reservation plugin for Trac

  Copyright 2010 Roberto Longobardi

  Project web page on TracHacks: http://trac-hacks.org/wiki/ResourceReservationPlugin
  
  Project web page on SourceForge.net: http://sourceforge.net/projects/resreserv4trac/
  
  Project web page on Pypi: http://pypi.python.org/pypi/ResourceReservation

  
A Trac plugin and macro to allow for visually planning and reserving the use of resources in your environment, e.g. test machines, consumable test data, etc..., with just one click.

=================================================================================================  
Change History:

Release 1.0.4 (2011-04-30):
  o Fixed bug #8746 Unicode trouble. 
                    Actually this bug could have also been named "It simpy doesn't work".
                    I mistakenly removed a single token from the database creation code, just ruining it.
                    Thanks Thorsen for reporting it.
  o Fixed bug #8464 Project environment upgrade fails with database error

Release 1.0.3 (2011-04-14):
  o Implemented security permissions RES_RESERVE_VIEW and RES_RESERVE_MODIFY
  o Added date and time tooltip on each table cell, to easy the reading of large time sheets

Release 1.0.1 (2010-08-12):
  o Fixed bug #7480 Does not work on IE
  o Begin externalizing strings into catalog
  o Fixed some problems with concurrent reservation of same resource in same day by different users

Release 1.0 (2010-08-10):
  o First release publicly available
  
  
