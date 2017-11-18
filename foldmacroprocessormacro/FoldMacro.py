from trac.core import *
from trac.util.html import html as tag
from trac.wiki.formatter import format_to_html, format_to_oneliner
from trac.wiki.macros import WikiMacroBase

author = "Peter Suter"
version = "1.0 ($Rev$)"
license = "BSD"
url = "https://trac-hacks.org/wiki/FoldMacroProcessorMacro"


class FoldMacro(WikiMacroBase):
    """Expands to a foldable section.

    The Wiki processor content is the folded wiki text.

    Wiki processor parameters:
    * `title`: The text in the folding header.
    * `tag`: The HTML element used for the title (Default: span)

    Example:
    {{{
        {{{#!Fold title="A title for the folded section" tag=h2
        This section of the wiki page is folded up and can be expanded by
        clicking on the title.

        This can contain any ''formatted'' **wiki** content, including macros
        and nested Fold sections.
        }}}
    }}}
    """

    def expand_macro(self, formatter, name, content, args):
        title_text = args.get('title', 'Use {{{#!Fold title="Your title"}}}')
        title_oneliner = format_to_oneliner(self.env, formatter.context,
                                        title_text)
        title_tag = args.get('tag', 'span')
        title_tag_function = getattr(tag, title_tag)
        title_html = title_tag_function(title_oneliner, class_="foldable")
        content_html = format_to_html(self.env, formatter.context, content)
        return tag.div(
                  tag(title_html,
                      tag.div(content_html)))
