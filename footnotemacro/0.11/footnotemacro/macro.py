from trac.core import *
from trac.web.chrome import add_stylesheet, add_script, ITemplateProvider
from trac.wiki.formatter import format_to_oneliner
from trac.wiki.macros import WikiMacroBase
from trac.util.text import shorten_line

from genshi.builder import tag
from pkg_resources import resource_filename

class FootNoteMacro(WikiMacroBase):
    """Collates and generates foot-notes. Call the macro with the
    foot-note content as the only argument:
    {{{
       [[FootNote(This is a footnote)]]
    }}}
    
    Foot-notes are numbered by the order in which they appear. To create a
    reference to an existing foot-note, pass the footnote number as
    argument to the macro:
    {{{
       [[FootNote(1)]]
    }}}
    
    In addition, identical foot-notes are coalesced into one entry. The
    following will generate one footnote entry with two references: 
    {{{
       Some text[[FootNote(A footnote)]] and some more text [[FootNote(A footnote)]].
    }}}
    
    A list of footnotes generated by one or more of the above commands is
    produced by calling the macro without arguments: 
    {{{
       [[FootNote]]
    }}}
    
    Once a set of footnotes has been displayed, a complete new set of
    footnotes can be created. This allows multiple sets of footnotes per
    page.
    """
    
    implements(ITemplateProvider)
    
    def expand_macro(self, formatter, name, content):
        # Make sure data capsule is in place
        if not hasattr(formatter, '_footnotes'):
            formatter._footnotes = []

        # Chrome
        add_stylesheet(formatter.req, 'footnote/footnote.css')
        add_script(formatter.req, 'footnote/footnote.js')

        if content:
            # Add a new footnote
            try:
                # Reference to an existing footnote
                output_id = int(content)

                try:
                    content = formatter._footnotes[output_id-1][0]
                except IndexError:
                    content = 'Unknown footnote'
            except ValueError:
                output_id = None

                # Try to collate with an existing footnote
                for i in xrange(len(formatter._footnotes)):
                    if formatter._footnotes[i][0] == content:
                        output_id = i + 1
                        break

                # Format markup
                markup = format_to_oneliner(self.env, formatter.context, content)

                # Adding a new footnote
                if not output_id:
                    formatter._footnotes.append((content, markup))
                    output_id = len(formatter._footnotes)

            return tag.sup(
                tag.a(
                    output_id,
                    title=shorten_line(content, 50),
                    id='FootNoteRef%s'%output_id,
                    href='#FootNote%s'%output_id,
                ),
                class_='footnote',
            )
        else:
            # Dump all accumulated notes
            footnotes = formatter._footnotes[:]
            formatter._footnotes = [(content, None) for content, markup in footnotes]
            if formatter._footnotes:
                return tag.div(
                    tag.hr(),
                    tag.ol(
                        [tag.li(
                            tag.a(
                                '%s.'%(i+1),
                                href='#FootNoteRef%s'%(i+1),
                                class_='sigil',
                            ),
                            ' ',
                            markup,
                            id='FootNote%s'%(i+1),
                        ) for i, (content, markup) in enumerate(footnotes) if markup],
                    ),
                    class_='footnotes',
                )
            else:
                return []

    # ITemplateProvider methods
    def get_htdocs_dirs(self):
        return [('footnote', resource_filename(__name__, 'htdocs'))]

    def get_templates_dirs(self):
        #return [resource_filename(__name__, 'templates')]
        return []

