from genshi.builder import tag
from trac.core import *
from trac.wiki.macros import WikiMacroBase
from trac.wiki.formatter import format_to_html


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
        title_tag = args.get('tag', 'span')
        title_tag_function = getattr(tag, title_tag)
        title_html = title_tag_function(title_text, class_="foldable")
        content_html = format_to_html(self.env, formatter.context, content)
        return tag.div(
                  tag(title_html,
                      tag.div(content_html)))
