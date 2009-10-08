# -*- coding: utf-8 -*-

import re
import datetime
import os

from trac.core import *
from trac.config import *
from trac.wiki.api import parse_args
from ppcache import ppFSFileCache

import trac.ticket.model

class PPConstant():
  dynamic_content_suffix = 'projectplan_dynamic'
  cache_content_suffix = 'pp_cached'
  definisection_name = 'pp_options'

class PPOption():
  '''
    Base Class for (Change/Save/Load/Show)-able Options
  '''
  def __init__( self, key, defval, section, catid, groupid, doc ):
    '''
      Initialize the base Option with some basic Values:
        * key - for reading and writing this Options
        * defval - the default value if non-existent or invalid
        * section - the config section where (key,value) are written to
        * catid - the category page for AdminPanel
        * groupid - the group id for grouped values
        * doc - Documentation for the Option Value/Key shown in AdminPanel
    '''
    if key:
      self.key = key
    else:
      raise Exception('empty key not allowed')
    self.defval = defval
    self.section = section
    self.catid = catid
    self.groupid = groupid
    self.doc = doc

  def get( self ):
    '''
      getter for Optionvalue
    '''
    raise NotImplementedError()

  def set( self, value ):
    '''
      setter for Optionvalue
    '''
    raise NotImplementedError()

class PPSingleValOption( PPOption ):
  '''
    Basic Single Value Option
  '''
  def __init__( self, env, key, defval, section=PPConstant.definisection_name, catid=None, groupid=None, doc="Not Documented" ):
    '''
      Initialize Base Option and add the env for setting/getting Options
    '''
    PPOption.__init__( self, key, defval, section, catid, groupid, doc )
    self.env = env

  def get( self ):
    '''
      std getter using env.config.get
    '''
    return self.env.config.get( self.section, self.key, self.defval )

  def set( self, value ):
    '''
      std setter using env.config.set
    '''
    self.env.config.set( self.section, self.key, value )

class PPSingleSelOption( PPSingleValOption ):
  '''
    Basic Single Value Selection Option
  '''
  def inselectable( self, value ):
    '''
      Check wether a value is in the Selectables
    '''
    return ( value in self.selectable() )

  def selectable( self ):
    '''
      Return a list or dict of Selectables
    '''
    raise NotImplementedError()

class PPSingleConOption( PPSingleValOption ):
  '''
    Basic Single Value Constrained Option
  '''

  def get( self ):
    '''
      get the verified value or the defaultvalue
    '''
    val = PPSingleValOption.get( self )
    if self.verifyvalue( val ):
      return val
    else:
      return self.defval

  def set( self, value ):
    '''
      set the verified value or the defaultvalue
    '''
    if self.verifyvalue( value ):
      PPSingleValOption.set( self, value )
    else:
      PPSingleValOption.set( self, self.defval )

  def verifyvalue( self, value ):
    '''
      verify the value
    '''
    raise NotImplementedError()

class PPListOfOptions( PPOption ):
  '''
    Basic List of Options
  '''

  def keys( self ):
    '''
      Return a list of Keys for the list of Options
    '''
    raise NotImplementedError()

  def get_val_for( self, subkey ):
    '''
      getter for a single option value in the list of options
    '''
    raise NotImplementedError()

  def set_val_for( self, subkey, value ):
    '''
      setter for a single option value in the list of options
    '''
    raise NotImplementedError()

  def get( self ):
    '''
      getter for a list of keys and values for the list of options
    '''
    retdict = {}
    for k in self.keys():
      retdict[ k ] = self.get_val_for( k )
    return retdict

  def set( self, indict ):
    '''
      setter for a list of keys and values for the list of options
    '''
    for k in self.keys():
      if k in indict:
        self.set_val_for( indict[ k ] )

class PPListOfSelOptions( PPListOfOptions ):
  '''
    Base Class for a List of Selection Options
  '''

  def inselectable( self, value ):
    '''
      Check wether calue is in the Selectables
    '''
    return ( value in self.selectable() )

  def selectable( self ):
    '''
      Return a list or dict of Selectables
    '''
    raise NotImplementedError()

class PPHTDPathSelOption( PPSingleSelOption ):
  '''
    HTDocs Path Selection Option Class
  '''
  RelDocPath = ''

  def __init__( self, env, key, defval, section=PPConstant.definisection_name, catid=None, groupid=None, doc="Not Documented" ):
    '''
      Initialize the Base Singel Selection Option
    '''
    PPSingleSelOption.__init__( self, env, key, defval, section, catid, groupid, doc )
    self.selectablekw = None

  @classmethod
  def absbasepath( cls ):
    '''
      Return the Absolute Basepath for the Path Selectables
    '''
    dp = os.path.normpath( cls.RelDocPath )
    from pkg_resources import resource_filename
    htdp = os.path.abspath(os.path.normpath(resource_filename(__name__, 'htdocs')))
    return os.path.join( htdp, dp )

  def selectable( self ):
    '''
      Return a dict of Selectables (and absolute filenames as values)
    '''
    if self.selectablekw == None:
      self.selectablekw = dict()
      p = self.absbasepath()
      try:
        if os.path.isdir( p ):
          dirlist = os.listdir( p )
        else:
          dirlist = []
        for f in dirlist:
          self.selectablekw[ f ] = os.path.join( p, f )
      finally:
        pass
      if self.defval not in self.selectablekw:
        self.selectablekw[ self.defval ] = ''
    return self.selectablekw

class PPListOfHTDPathSelOptions( PPListOfSelOptions ):
  '''
    List of HTDoc Path Selection Options
  '''

  def selector( self ):
    '''
      Return a Selector (PPHTDPathSelOption) which is used for
      accessing the RelDocPath and selectable() attributes
    '''
    raise NotImplementedError()

  def selectable( self ):
    '''
      Return the Selectables for the Selector
    '''
    return self.selector().selectable()

class PPImageSelOption(PPHTDPathSelOption):
  '''
    HTDoc Image Path Selection Option
  '''
  RelDocPath = 'images'
  ImagePattern = re.compile( '.*(\.(png|gif|jpg|jpeg))', re.IGNORECASE )

  def selectable( self ):
    '''
      Return a dict of Selectable Images (ending with png/gif/jpg/jpeg) and
      the Default Value if not existend in the Selectables
    '''
    if self.selectablekw == None:
      seldict = PPHTDPathSelOption.selectable( self )
      for ( e, f ) in seldict.items():
        if ( not os.path.isfile( f ) ) or ( not re.match( self.ImagePattern, e ) ):
          if e != self.defval:
            del seldict[ e ]
    return PPHTDPathSelOption.selectable( self )

class PPListOfImageSelOptions( PPListOfHTDPathSelOptions ):
  '''
    List of HTDoc Image Path Selection Options
    (for Image dependend checks in AdminPanel)
  '''
  pass

class PPDateFormatOption(PPSingleSelOption):
  '''
    Selectable DateFormat Option
  '''
  def selectable( self ):
    '''
      Check wether the value is in the List of possible Values
    '''
    return [ 'DD/MM/YYYY', 'MM/DD/YYYY', 'DD.MM.YYYY' ]

class PPHTMLColorOption(PPSingleConOption):
  '''
    HTML Color Option
  '''
  def verifyvalue( self, value ):
    '''
      Check wether the value has the Format #<6 hex digits>
    '''
    return ( re.match( '#[0-9A-Fa-f]{6}', value )!=None )

class PPIntegerOption(PPSingleConOption):
  '''
    Integer Option
  '''
  def verifyvalue( self, value ):
    '''
      Check wether the value is an Integer value
    '''
    res = True
    try:
      int(value)
    except TypeError:
      res = False
    return res

class PerTracModelEnumColor( PPListOfOptions ):
  '''
    Base Class for List of HTML Color Options for a
    trac.ticket.model.AbstractEnum descendant
  '''

  enumerator_cls = trac.ticket.model.AbstractEnum

  def __init__( self, env, key, defval, section=PPConstant.definisection_name, catid=None, groupid=None, doc='"%s" Not Documented' ):
    '''
      Initialize Single Option which holds the Color Option Key:Value pairs
    '''
    PPListOfOptions.__init__( self, key, defval, section, catid, groupid, doc )
    self._internalOption = PPSingleValOption( env, self.key, '' )

  def keys( self ):
    '''
      Return possible Keys Enumeration Keys, currently set in Trac.
      Like Priority, Severity, and so on.
    '''
    return [ e.name for e in self.enumerator_cls.select( self._internalOption.env ) ]

  def get( self ):
    '''
      Get a Key:Value Dict for Key:HTML Code pairs
    '''
    retdict = {}
    for k in self.keys():
      retdict[ k ] = self.defval
    opts = self._internalOption.get()
    udict = {}
    if opts:
      for entry in opts.split(','):
        (k,v) = entry.strip('"').split( '=', 1 )
        udict[ k ] = v
    retdict.update( udict )
    return retdict

  def set( self, indict ):
    '''
      Set a Key:Value Dict for Key:HTML Code pairs.
      Keys not in current Enumeration will be dropped, Keys not set but in current enumeration
      will be set to defval.
    '''
    wdict = {}
    for k in self.keys():
      if ( k in indict ) and indict[ k ] and ( indict[ k ] != self.defval ):
        wdict[ k ] = indict[ k ]
    if len(wdict) > 0:
      setstr = '"'+ reduce( lambda x, y: x+'","'+y, map( lambda k: k+"="+wdict[ k ], wdict.keys() ) ) +'"'
    else:
      setstr = ''
    self._internalOption.set( setstr )

  def get_val_for( self, subkey ):
    '''
      Return a single HTML Code for a given Enumeration Key
    '''
    gdict = self.get()
    if subkey in gdict:
      return gdict[ subkey ]
    else:
      return self.defval

  def set_val_for( self, subkey, value ):
    '''
      Set a single HTML Code for a given Enumeration Key. Same behavior as for set
    '''
    gdict = self.get()
    if re.match( '#[0-9A-Fa-f]{6}', value ):
      gdict[ subkey ] = value
    else:
      gdict[ subkey ] = self.defval
    self.set( gdict )

class PerTracModelEnumImage( PPListOfImageSelOptions ):
  '''
    Base Class for List of selectable Image Options for a
    trac.ticket.model.AbstractEnum descendant
  '''

  enumerator_cls = trac.ticket.model.AbstractEnum

  def __init__( self, env, key, defval, section=PPConstant.definisection_name, catid=None, groupid=None, doc='"%s" Not Documented' ):
    '''
      Initialize Internal vars for Key:Value Storage
    '''
    PPListOfSelOptions.__init__( self, key, defval, section, catid, groupid, doc )
    self._internalOption = PPImageSelOption( env, key, defval )
    self._internalKeys = None
    self.env = env

  def selector( self ):
    '''
      Return the Internal Single Selector Option used for Selection
      of Option Values
    '''
    return self._internalOption

  def keys( self ):
    '''
      Return a Dict with Enumeration Keys for this Option
    '''
    if self._internalKeys is not None:
      return self._internalKeys
    else:
      self._internalKeys = [ e.name for e in self.enumerator_cls.select( self.env ) ]
      return self._internalKeys

  def get_val_for( self, subkey ):
    '''
      Return the Selected Value (Image) for a given Enumeration Key
    '''
    if subkey in self.keys():
      res = self.env.config.get( self.section, self.key+subkey, self.defval )
      if not self.inselectable( res ):
        res = self.defval
    else:
      res = self.defval
    return res

  def set_val_for( self, subkey, value ):
    '''
      Set the Value for a given Enumeration Key, if it is selectable, else default to defval
    '''
    if subkey in self.keys():
      if not self.inselectable( value ):
        value = self.defval
      self.env.config.set( self.section, self.key+subkey, value )

class PPStatusColorOption( PerTracModelEnumColor ):
  '''
    Per Status Color Option
  '''
  enumerator_cls = trac.ticket.model.Status

class PPPriorityColorOption( PerTracModelEnumColor ):
  '''
    Per Priority Color Option
  '''
  enumerator_cls = trac.ticket.model.Priority

class PPStatusImageOption( PerTracModelEnumImage ):
  '''
    Per Status Image Option
  '''
  enumerator_cls = trac.ticket.model.Status

class PPPriorityImageOption( PerTracModelEnumImage ):
  '''
    Per Priority Image Option
  '''
  enumerator_cls = trac.ticket.model.Priority

class PPConfiguration():
  '''
    ProjectPlan Configuration which Loads/Saves/Manages the Options and
    List of Options.
    Single Value Options are placed in self.flatconf and
    List of Options in self.listconf, both are free for access but
    PPConfiguration wraps some checks around so try to use the PPConfiguration
    methods instead of accessing the Options objects directly.
  '''

  def __init__( self, env ):
    '''
      Initialize the Option (flatconf) and List of Option (listconf) mappings.
      Load the Values.
    '''
    self.env = env
    # <attr>: ( <section>, <key>, <default value> )
    self.flatconf = {}
    # <attr>: ( <section suffix>, <key_list function>, <default value>, <default for non exisiting value> )
    self.listconf = {}
    self.load()

  # non-list attribute getter/setter
  def get( self, n ):
    '''
      Single Option Value Getter: get value for Key n
    '''
    if n in self.flatconf:
      return self.flatconf[ n ].get()
    else:
      raise Exception( "Option %s not found" % n )

  def set( self, n, v ):
    '''
      Single Option Value Setter: set value v for Key n
    '''
    if n in self.flatconf:
      self.flatconf[ n ].set( v )
    else:
      raise Exception( "Option %s not found" % n )

  # list attribute dict getter/setter
  def get_map( self, n ):
    '''
      List of Options Value Getter: get a dict of values and option keys for (list) Key n
    '''
    if n in self.listconf:
      return self.listconf[ n ].get()
    else:
      raise Exception( "List of Options for %s not found" % n )

  def get_map_val( self, n, k ):
    '''
      Single Option Value Getter: get value for Key k in List n
    '''
    if n in self.listconf:
      return self.listconf[ n ].get_val_for( k )
    else:
      raise Exception( "List of Options for %s not found" % n )

  def set_map( self, n, v ):
    '''
      List of Options Value Setter: set a dict of option keys and values for (list) Key n
    '''
    if n in self.listconf:
      self.listconf[ n ].set( v )
    else:
      raise Exception( "List of Options for %s not found" % n )

  def set_map_val( self, n, k, v ):
    '''
      Single Option Value Setter: set value v for Key k in List n
    '''
    if n in self.listconf:
      self.listconf[ n ].set_val_for( k, v )
    else:
      raise Exception( "List of Options for %s not found" % n )

  def load( self ):
    '''
      Initialize the Options and List of Options and load the Values (or Defaults)
    '''
    # Ticket-Custom Field Mappings (no catid/grpid -> not for panel)
    self.flatconf[ 'custom_dependency_field' ] = PPSingleValOption(
      self.env, 'custom_dependency_field', u'dependencies' )

    self.flatconf[ 'custom_due_assign_field' ] = PPSingleValOption(
      self.env, 'custom_due_assign_field', u'due_assign' )

    self.flatconf[ 'custom_due_close_field' ] = PPSingleValOption(
      self.env, 'custom_due_close_field', u'due_close' )

    # Basic Options
    self.flatconf[ 'cachepath' ] = PPSingleValOption(
      self.env, 'cachepath', u'/tmp/ppcache', catid='General', groupid='Cache', doc="""
      Path for File based Caching (mainly used for Image/HTML Rendering speedup).\n
      \n
      ! the cache root directory must be a real directory, not a link\n
      ! after changing this option you need to manualy delete the old cache
      """ )

    self.flatconf[ 'cachedirsize' ] = PPIntegerOption(
      self.env, 'cachedirsize', u'1', catid='General', groupid='Cache', doc="""
      Cache lookup Directory Size\n
      Caching can produce an enormous amount of Files which puts some pressure on
      the underlying Filesystem. Directory lookup and File lookup/creation may be speed up
      with multiple smaller Directory nodes.\n
      (depends on the Filesystem and amount of Files created)\n
      0 = off, all Files will be placed into the cache path\n
      1 - digest length for used hash = use max. 16^(cachedirsize) prefix directories\n
      \n
      ! after changing this option you need to manualy delete the old cache
      """ )

    self.flatconf[ 'dotpath' ] = PPSingleValOption(
      self.env, 'dot_executable', u'/usr/bin/dot', catid='General', groupid='Renderer', doc="""
      Executable Path for the Graphiz dot Program
      """ )

    # Ticket Custom Options
    self.flatconf[ 'ticketassignedf' ] = PPDateFormatOption(
      self.env, '%s.value' % self.get( 'custom_due_assign_field' ),
      u'DD/MM/YYYY', section='ticket-custom', catid='General', groupid='Tickets', doc="""
      DateTime Format which will be used for Calculating the Assign Date
      """ )
    self.flatconf[ 'ticketclosedf' ] = PPDateFormatOption(
      self.env, '%s.value' % self.get( 'custom_due_close_field' ),
      u'DD/MM/YYYY', section='ticket-custom', catid='General', groupid='Tickets', doc="""
      DateTime Format which will be used for Calculating the Closing Date
      """ )

    # Color/Image Options
    self.flatconf[ 'version_fillcolor' ] = PPHTMLColorOption(
      self.env, 'version_fillcolor', u'#FFFFE0', catid='Color', groupid='Non Ticket Elements', doc="""
      Version Cluster Fillcolor
      """ )

    self.flatconf[ 'version_fontcolor' ] = PPHTMLColorOption(
      self.env, 'version_fontcolor', u'#0000FF', catid='Color', groupid='Non Ticket Elements', doc="""
      Version Cluster Font Color
      """ )

    self.flatconf[ 'version_color' ] = PPHTMLColorOption(
      self.env, 'version_color', u'#0000FF', catid='Color', groupid='Non Ticket Elements', doc="""
      Version Cluster Frame Color
      """ )

    self.flatconf[ 'milestone_fillcolor' ] = PPHTMLColorOption(
      self.env, 'milestone_fillcolor', u'#F5F5F5', catid='Color', groupid='Non Ticket Elements', doc="""
      Milestone Cluster Fillcolor
      """ )

    self.flatconf[ 'milestone_fontcolor' ] = PPHTMLColorOption(
      self.env, 'milestone_fontcolor', u'#0000FF', catid='Color', groupid='Non Ticket Elements', doc="""
      Milestone Cluster Font Color
      """ )

    self.flatconf[ 'milestone_color' ] = PPHTMLColorOption(
      self.env, 'milestone_color', u'#0000FF', catid='Color', groupid='Non Ticket Elements', doc="""
      Milestone Cluster Frame Color
      """ )

    self.flatconf[ 'ticket_ontime_color' ] = PPHTMLColorOption(
      self.env, 'ticket_ontime_color', u'#FFFF00', catid='Color', groupid='Tickets', doc="""
        Color for: Ticket is on Time
      """ )

    self.flatconf[ 'ticket_overdue_color' ] = PPHTMLColorOption(
      self.env, 'ticket_overdue_color', u'#FF0000', catid='Color', groupid='Tickets', doc="""
        Color for: Ticket is Over Due
      """ )

    self.flatconf[ 'ticket_notowned_color' ] = PPHTMLColorOption(
      self.env, 'ticket_notowned_color', u'#6666FF', catid='Color', groupid='Tickets', doc="""
        Color for: Ticket is not Owned by current User
      """ )

    self.flatconf[ 'ticket_owned_color' ] = PPHTMLColorOption(
      self.env, 'ticket_owned_color', u'#FF0000', catid='Color', groupid='Tickets', doc="""
        Color for: Ticket is Owned by current User
      """ )

    self.flatconf[ 'ticket_ontime_image' ] = PPImageSelOption(
      self.env, 'ticket_ontime_image', u'none', catid='Image', groupid='Tickets', doc="""
        Symbol for: Ticket is on Time
      """ )

    self.flatconf[ 'ticket_overdue_image' ] = PPImageSelOption(
      self.env, 'ticket_overdue_image', u'none', catid='Image', groupid='Tickets', doc="""
        Symbol for: Ticket is Over Due
      """ )

    self.flatconf[ 'ticket_notowned_image' ] = PPImageSelOption(
      self.env, 'ticket_notowned_image', u'none', catid='Image', groupid='Tickets', doc="""
        Symbol for: Ticket is not Owned by current User
      """ )

    self.flatconf[ 'ticket_owned_image' ] = PPImageSelOption(
      self.env, 'ticket_owned_image', u'none', catid='Image', groupid='Tickets', doc="""
        Symbol for: Ticket is Owned by current User
      """ )

    self.flatconf[ 'ColorForStatusNE' ] = PPHTMLColorOption(
      self.env, 'color_for_ne_status', u'#C0C0C0', catid='Color', groupid='Status', doc="""
      Color for Non-Existing/New Status
      """ )

    self.flatconf[ 'ColorForPriorityNE' ] = PPHTMLColorOption(
      self.env, 'color_for_ne_priority', u'#C0C0C0', catid='Color', groupid='Priority', doc="""
      Color for Non-Existing/New Priority
      """ )

    self.listconf[ 'ColorForStatus' ] = PPStatusColorOption(
      self.env, 'colorforstatus', self.get( 'ColorForStatusNE' ), catid='Color', groupid='Status', doc="""
      HTML Color for rendering Status "%s"
      """ )

    self.listconf[ 'ColorForPriority' ] = PPPriorityColorOption(
      self.env, 'colorforpriority', self.get( 'ColorForPriorityNE' ), catid='Color', groupid='Priority', doc="""
      HTML Color for rendering Priority "%s"
      """ )

    self.listconf[ 'ImageForStatus' ] = PPStatusImageOption(
      self.env, 'image_for_status_', u'none', catid='Image', groupid='Status', doc="""
      Image for Status "%s"
      """ )

    self.listconf[ 'ImageForPriority' ] = PPPriorityImageOption(
      self.env, 'image_for_priority_', u'none', catid='Image', groupid='Priority', doc="""
      Image for Priority "%s"
      """ )

  def save( self ):
    '''
      Save all Changes to the Options and List of Options
    '''
    self.env.config.save()

class PPEnv():
  '''
    Project Plan Environment
    containing references and so on, for most used objects and values like
    macro arguments, trac environment and request...
  '''
  def __init__( self, env, req, content ):
    '''
      Initialize the Envoironment
    '''
    # parse passed macro arguments
    args, kw = parse_args( content )
    self.macroid = str( kw.get('macroid') ) or '1';
    self.macroargs = args
    self.macrokw = kw
    # set constants
    self.const = PPConstant
    # set trac environment, request
    self.tracenv = env
    self.tracreq = req
    # load configuration items
    self.conf = PPConfiguration(env)
    # create cache
    self.cache = ppFSFileCache( self.conf.get( 'cachepath' ),
                                datetime.date.today().isoformat(),
                                int(self.conf.get( 'cachedirsize' )) )
    # initialize the cache hash value with environment settings
    self.mhash = self.cache.newHashObject()
    self.mhash.update( content )
    self.mhash.update( self.macroid )
    self.mhash.update( self.tracreq.authname )
    self.mhash.update( str( datetime.date.today() ) )
