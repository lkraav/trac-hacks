# -*- coding: utf-8 -*-
# redone according to http://trac.edgewall.org/browser/tags/trac-0.11/wiki-macros/README 

from trac.wiki.macros import WikiMacroBase

revison="$Rev: 8404 $"
url="$URL: http://trac-hacks.org/svn/anchormacro/0.10/Anchor.py $"

class AnchorMacro(WikiMacroBase):
        """
        This macro allows you to add anchor.

        Author: Dmitri Khijniak
        Modified for 0.11: Leho Kraav

        Usage:
        {{{
          [[Anchor(anchor_name,text )]]
        }}}
        or
        {{{
          [[Anchor(anchor_name)]]
        }}}
        Where:
        anchor_name::
          is a URL used to reference the anchor
        text::
          visible text describing the anchor

        Example:
        {{{
          [[Anchor(anchor)]]
          [[Anchor(anchor, name)]]
        }}}
        """


        def expand_macro(self, formatter, name, args):
                args = tuple(args.split(","))
                print args

                if len(args) == 2 :
                        return '<a class="mytabel" id="%s" href="#%s">%s</a>' % (args[0],args[1],args[1])
                else:
                        return '<a class="mytabel" id="%s"></a>' % args


