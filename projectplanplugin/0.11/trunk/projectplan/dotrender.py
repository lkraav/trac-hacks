# -*- coding: iso-8859-15 -*-

import os
import time
import subprocess

import ppenv

class GVCMapXGen():
  '''
    Write a DOT file and generate a working set that can be used for Rendering:
       - a Dot File that will be used by Graphviz to generate
       - Image for the Background
       - Client-Side Map for Image Overlay Elements
       - a log File that keeps the GV error output

    GVCMapXGen uses the pp Filesystem Cache for caching. Check obj.cached before
    trying to write the DOT file. A cached working set still provides file and
    linknames, but theres no fileobj and no filegeneration generation.
  '''
  def __init__( self, env, hashobject ):
    '''
      Initialize the local pathes/filenames and the resulting Image Link either
      for the cache entry on hit, or for generating those files.
      If self.cached then cache entries must be used and None will be set for
      the DOT file input. Check self.cached before writing.
    '''

    self.env = env
    self.config = env.conf
    if not hashobject.Finalized:
      hashobject.finalize()
    self.centry = env.cache.lookupEntry( hashobject, False )

    self.cached = False

    if self.centry.Exists:
      if not ( self.centry.entryExists( '.dot' ) and
               self.centry.entryExists( '.map' ) and
               self.centry.entryExists( '.png' ) and
               self.centry.entryExists( '.log' ) ):
        # possible collision, wipe and hope it wont mess everything up :/
        self.centry.wipe()
      else:
        self.cached = True

    # build absolute filenames, no cache entries written at the moment!
    self.dotfile = self.centry.getFileName( '.dot' )
    self.cmapxfile = self.centry.getFileName( '.map' )
    self.imgfile = self.centry.getFileName( '.png' )
    self.genoefile = self.centry.getFileName( '.log' )

    # build the image link
    self.imglink = env.tracreq.href( ppenv.PPConstant.cache_content_suffix,
                                     env.cache.urlCacheFile( self.imgfile ) )

    # create cache entries
    if not self.cached:
      # the dotfile will be constructed, so we need a file object
      self.__iobj = self.centry.getFile( '.dot', False )
      # map/png/log are generated by graphviz, but we need at least the entries
      self.centry.getFile( '.map', True )
      self.centry.getFile( '.png', True )
      self.centry.getFile( '.log', True )
      # self._iobj.write( codecs.BOM_UTF8 )
      # graphviz currently doesnt like the UTF8 BOM -> [syntax error]
    else:
      self.__iobj = None

  def iputstring( self, instr ):
    '''
      write a string into the dot file
    '''
    self.__iobj.write( instr.encode( 'utf-8' ) )

  def __iadd__( self, instr ):
    '''
      overriden operator "+=": GVMapGen x String -> GVMapGen
    '''
    self.iputstring( instr )
    return self

  def generate( self ):
    '''
      if not cached, close the dot file, produce the map/img/log file and
      write the cache entries (if theres no exception/error from dot/os).
      if cached, do nothing
    '''
    if not self.cached:
      # close file
      self.__iobj.close()
      try:
        logfobj = open( self.genoefile, 'w' )
        # execute: dot -v -Tcmapx -o fn.map -Tpng -o fn.png fn.dot >fn.log 2>&1
        dotexec = self.config.get( 'dotpath' )
        if os.path.isabs( dotexec ) and ( not os.path.isfile( dotexec ) ):
          raise Exception( "DOT Executable not found: "+dotexec );
        gvctx = subprocess.Popen(
                  executable = dotexec,
                  args = [
                          "-v",
                          "-Kdot", # mandatory at least since graphviz 2.26.3
                          "-Tcmapx",
                          "-o" + self.cmapxfile,
                          "-Tpng", "-o" + self.imgfile,
                          self.dotfile ],
                  shell = False,
                  stdout = logfobj,
                  stderr = subprocess.STDOUT )
        exitstatus = gvctx.wait()
        time.sleep(10) # just to be sure, wait 3 sec, ticket #6541
        #pid, exitstatus = os.waitpid( gvctx.pid, 0 )
        if exitstatus != 0:
          # simply raise an exception with link to the logfile
          # the logfile may be still accessible as long as the cache entry is
          # not rewritten
          raise Exception( '''dot execution failed,
            logfile _may_ be still accessible at %s ''' %
            self.env.cache.urlCacheFile( self.genoefile ) )
      except Exception:
        # just in case.. close logfile
        logfobj.close()
        # pass exception for caller
        raise
      else:
        # write the cache entry
        self.centry.write()
