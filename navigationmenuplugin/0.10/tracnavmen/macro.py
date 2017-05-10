# vim: expandtab tabstop=4

from trac.core import *
from trac.wiki.macros import WikiMacroBase
from trac.wiki.model import WikiPage
from trac.wiki.formatter import Formatter, OutlineFormatter
from StringIO import StringIO
import os, re

__all__ = ['NavigationMenu']

class NullOut(object):
   def write(self, *args): pass

class MyOutlineFormatter(OutlineFormatter):

    def format(self, active_page, page, text, out, min_depth, max_depth):
        # XXX Code copied straight out of OutlineFormatter
        self.outline = []
        Formatter.format(self, text)

        active = ''
        if page == active_page:
            active = ' class="active"'

        if min_depth > max_depth:
            min_depth, max_depth = max_depth, min_depth
        max_depth = min(6, max_depth)
        min_depth = max(1, min_depth)

        curr_depth = min_depth - 1

        for depth, anchor, heading in self.outline:
            if depth < min_depth or depth > max_depth:
                continue
            if depth < curr_depth:
                out.write('</li></ol><li%s>' % active * (curr_depth - depth))
            elif depth > curr_depth:
                out.write('<ol><li%s>' % active * (depth - curr_depth))
            else:
                out.write("</li><li%s>\n" % active)
            curr_depth = depth
            out.write('<a href="%s#%s">%s</a>' %
                      (self.href.wiki(page), anchor, heading))
        out.write('</li></ol>' * curr_depth)

    def getHeader(self, page, text):
        a = page
        try:
            self.outline = []
            Formatter.format(self, text)
            a = self.outline[0][2]
        except:
            a = page
        return a

def treeCount(thePath):
    # This simple function just counts how deep we are in a tree
    count = 0
    symbol = '/'
    index = thePath.find(symbol)  # use default start
    while index != -1:
        count += 1
        start = index + 1
        index = thePath.find(symbol, start)  # set new start
    return count

def sub_wiki(self, req, name, args, current_page, Oformatter):
    #Makes ok looking subtrees
    db = self.env.get_db_cnx()
    cursor = db.cursor()

    prefix = None
    	
    if args:
        prefix = args
    else :
	prefix = req.hdf.getValue('wiki.page_name', '') + '/'
    if prefix:
        SQLargs = []
        SQLargs.append(prefix + '%')
        cursor.execute("SELECT DISTINCT name FROM wiki WHERE name LIKE %s ORDER BY name",SQLargs)
    else:
        return "error, no name passed to sub_wiki function"

    depth = 1
    curr_depth = 0
    buf = StringIO()
    while 1:
        row = cursor.fetchone()
        if row == None:
            break
        active = ''
        if row[0] == current_page:
            active = ' class="active"'

        depth = treeCount(row[0])+1
        if depth < curr_depth:
            buf.write('</li></ol><li%s>' % active * (curr_depth - depth))
        elif depth > curr_depth:
            buf.write('</li><ol><li%s>' % active * (depth - curr_depth))
        else:
            buf.write("</li><li%s>\n" % active)
        curr_depth = depth

        buf.write('<a href="%s">' % (self.env.href.wiki(row[0])))
        #The following two lines are there to make sure we write the first header instead
        #of the page path, if it is found that is.
        page = WikiPage(self.env,row[0])
        buf.write(Oformatter.getHeader(row[0], page.text))
        buf.write('</a>\n')
    buf.write('</li></ol>' * curr_depth)

    return buf.getvalue()
		    
class TOCMacro(WikiMacroBase):
    """
    This is a newer version of the menu. It was originally just a simple menu based on SubWiki and TocMacro but now I have expanded it with a bunch of new functionality to make it more flexible. This menu is intended to be a heavy setup / low maintainance menu.

    Here is a list of the most general features.

     - A default menu for all pages read from a wikipage (DefaultNavigationMenu)
     - Ability to add sections or include other menus within menus (like the default one)
     - Ability to generate subtrees from pages
     - Ability to use WikiFormatting inside the menu
     - Generate a menu over headings on the current page
    
    === Menu scripting documentation ===
    
    First of all make a new page called !DefaultNavigationMenu, and then add the {{{[[TOC]]}}} reference into some page where you want the menu, NOT on !DefaultNavigationMenu
    
    ''Optional Way''[[BR]]
    Make a new page called whatever you like, example : !MyMenu. Then add {{{[[TOC(incmenu=MyMenu]]}}} to the page where you want to display the menu.
    
    Now go and edit either DefaultNavigationMenu or the page you decided on for your menu. Then just start designing the menu as you like with the commands below, use new line (enter) to separate commands. You may also add empty lines but you may not have two commands on the same line.
    
    || '''Argument'''       || '''Meaning''' ||
    || SETTINGS             ||               ||
    || {{{heading=<x>}}}    || Override the default heading of "Table of Contents" ||
    || {{{noheading}}}      || Suppress display of the heading. ||
    || {{{inline}}}         || Display TOC inline rather than as a side-bar. ||
    || ACTIONS              ||                             ||
    || #text                || A comment line. Start the line with a hash sign (#) ||
    || {{{[CPH]}}}          || Creates a page header list for the current page ||
    || {{{[S]Some/Page/Path}}} || Starts a section. If you specify something like !GameDesign, it will display on the !GameDesign page and all subpages !GameDesign/*. Sections can have multiple subsections. Note: It will also display on any similar pages like !GameDesign2/*. ||
    || {{{[!S]x}}}  || Ends the last opened section. You may place a comment where it says x to make it easier to read ||
    || {{{[N]}}}    || New line. Adds an empty line, similar to {{{[[BR]]}}} for WikiFormatting ||
    || {{{[H]x}}}   || Adds a header with the text x. ||
    || {{{[***}}}   || Starts a WikiFormatting section. Make sure you close it because all menu commands are ignored inside it, and it will not be rendered unless it is closed. You may include macros / other plugins or just wiki format code. Has to be written on a line by itself. ||
    || {{{***]}}}   || Ends the WikiFormatting section. Make sure you close all WikiFormatting sections or they will not render. ||
    """
    def render_macro(self, req, name, args):

        #db = self.env.get_db_cnx()
        
        # Bail out if we are in a no-float zone
        # Note for 0.11: if 'macro_no_float' in formatter.properties
        if 'macro_no_float' in req.hdf:
            return ''
        
        # If this is a page preview, try to figure out where its from
        # Note for 0.11: formatter.context could be the main `object`
        # to which the text being formatted belongs to...
        current_page = req.hdf.get('wiki.page_name','WikiStart')
        in_preview = req.args.has_key('preview')
        
        # Split the args
        if not args: args = 'incmenu=DefaultNavigationMenu'
        args = [x.strip() for x in args.split(',')]
        
        #A function to load in a def menu
        #Returns a modified version of args with the menu loaded into it
        def loadDef(path,i,args):
            page = WikiPage(self.env,path)
            if page.exists:
               tmpArgs = []
               for a in page.text.split('\n'):
                   tmpArgs.append(a.strip())
               tmpArgs += args[i+1:]
               return tmpArgs

        #Lists used in the loop
        defMenuList = [] #Used to make sure menues are not included twice (to avoid infinite loops)
        sectionList = [] #This is the section stack
        #Other things used
        formatter = Formatter(self.env, req)
        Oformatter = MyOutlineFormatter(self.env) # FIXME 0.11: give 'req'
        outFormat = StringIO()
        formatText = ''
        wikiFormat = 0
        #formatter.format(formatText,outFormat)
        # Options
        inline = False
        heading = 'Table of Contents'
        pagenames = []
        defmenu = ''
        # Global options
        i = -1
        while i < len(args)-1:
          for i in range(len(args)):

              #This is used for wiki formatted text, to read it and stop reading it
              if args[i].strip().startswith('***]'):
                  wikiFormat = 0
                  formatter.format(formatText,outFormat)
                  pagenames.append('[wiki]' + outFormat.getvalue()[5:len(outFormat.getvalue())-6])
                  outFormat = StringIO()
                  formatText = ''
                  continue
              elif wikiFormat == 1:
                  formatText += args[i]
                  continue

              #Comments, Section Start, Section End
              if args[i].strip().startswith('#'):
                  #print 'Ignoring Comment'
                  continue
              elif args[i].strip().startswith('[S]'):
                  sectionList.append(args[i][3:].strip())
                  #print 'Section Start'
                  continue
              elif args[i].strip().startswith('[!S]'):
                  if len(sectionList) > 0:
                     del sectionList[len(sectionList)-1]
                  #print 'Section End'
                  continue

              #Section testing. Skips if you are not in the section
              if len(sectionList) > 0:
                 if not current_page.startswith(sectionList[len(sectionList)-1]):
                     continue

              #Settings and includes
              if args[i].strip() == 'inline':
                  inline = True
              elif args[i].strip() == 'noheading':
                  heading = ''
              elif args[i].strip().startswith('[***'):
                  wikiFormat = 1
                  formatText = ''
              elif args[i].strip().startswith('heading='):
                  heading = args[i][8:].strip()
              elif args[i].strip().startswith('[H]'):
                  pagenames.append('[head]' + args[i][3:].strip())
              elif args[i].strip().startswith('[N]'):
                  pagenames.append('[line]')
              elif args[i].strip().startswith('[CPH]'):
                  pagenames.append('[cph_]')
              elif args[i].strip().startswith('incmenu='):
                  defmenu = args[i][8:].strip()
                  if defmenu != '':
                     defdupe = 0
                     #This is here to avoid infinite loops, if you include a defmenu inside itself
                     for a in defMenuList:
                         if a == defmenu:
                            defdupe = 1
                     if defdupe != 1:
                        defMenuList.append(defmenu)
                        args = loadDef(defmenu,i,args)
                        i = -1
                        break
              elif args[i].strip() != '':
                  pagenames.append('[page]' + args[i].strip())

        # Has the user supplied a list of pages?
        if not pagenames:
            pagenames.append('[page]' + current_page)

        out = StringIO()
        if not inline:
            out.write("<div class='wiki-toc'>\n")
        if heading:
            out.write("<h4>%s</h4>\n" % heading)

        for pagename in pagenames:
            if pagename.startswith('[page]'):
               out.write(sub_wiki(self, req, name, pagename[6:], current_page, Oformatter))
            elif pagename.startswith('[wiki]'):
               out.write(pagename[6:])
            elif pagename.startswith('[cph_]'):
               page = WikiPage(self.env,current_page)
               Oformatter.format('', current_page, page.text, out, 0, 6)
            elif pagename.startswith('[head]'):
               out.write("<h4>%s</h4>\n" % pagename[6:])
            elif pagename.startswith('[line]'):
               out.write("<br>\n")
        if not inline:
            out.write("</div>\n")

        return out.getvalue()