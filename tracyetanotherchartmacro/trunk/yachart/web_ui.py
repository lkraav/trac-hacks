# -*- coding: utf-8 -*-
#
# Copyright (C) 2018 Theodor Norup <theodor.norup@gmail.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

import re

from trac.config      import IntOption
from trac.core        import *
from trac.web.chrome  import ITemplateProvider, add_script
from trac.web.main    import IRequestFilter, IRequestHandler
from trac.wiki.macros import WikiMacroBase
from trac.util.html   import tag, Fragment, Markup

from tracadvparseargs import *

import jinja2


class yachart(WikiMacroBase):
    implements(IRequestFilter,ITemplateProvider)

    """Embed a bar/line/bar chart in a wiki page.

    Example:
    {{{
        [[yachart(id=chart1; title=Ticket statuses; query=SELECT status , COUNT(status) FROM ticket GROUP BY status)]]
    }}}
    """

    # Options
    opt_w  = IntOption('yachart', 'width', default=400,
                       doc='Default width of plot (in pixels)')

    opt_h  = IntOption('yachart', 'height', default=200,
                       doc='Default height of plot (in pixels)')

    opt_tm = IntOption('yachart', 'top_margin', default=50,
                       doc='Default top margin of plot (in pixels)')

    opt_bm = IntOption('yachart', 'bottom_margin', default=30,
                       doc='Default bottom margin of plot (in pixels)')

    opt_lm = IntOption('yachart', 'left_margin', default=5,
                       doc='Default left margin of plot (in pixels)')

    opt_rm = IntOption('yachart', 'right_margin', default=5,
                       doc='Default right margin of plot (in pixels)')

    # ITemplateProvider methods
    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('yachart', resource_filename(__name__, 'htdocs'))]

    def get_templates_dirs(self):
        return []

    # IRequestFilter methods
    def pre_process_request(self, req, handler):
        return handler

    def post_process_request(self, req, template, data, content_type):
        add_script(req, 'yachart/plotly-latest.min.js')
        return template, data, content_type

    # private methods

    def _get_data(self, options):

        def _encode(col):
            if type(col) == unicode:
                return ''.join(col.splitlines())
            return str(col)

        q = self.env.db_query(options.get('query', None), ())
        x,y = ([],[])
        for r in q:
            x.append(_encode(r[0]))
            y.append(_encode(r[1]))

        return '"' + '","'.join(x) + '"', '"' + '","'.join(y) + '"' 
            
    pie_template = jinja2.Template(\
    """
    {
    labels: [{{ labels }}],
    values: [{{ values }}],
    type:   '{{ chart_type }}',
    name:   '{{ name }}',
    title:  '{{ title }}',
    }
    """
    )

    bar_and_line_template = jinja2.Template(\
    """
    {
    x:     [{{ x_data }}],
    y:     [{{ y_data }}],
    type:  '{{ chart_type }}',
    name:  '{{ name }}',
    title: '{{ title }}',
    }
    """
    )

    layout_template = jinja2.Template(\
        """
        {
        title  : '{{ title }}',
        width  : {{ width }},
        height : {{ height }},
        margin: { t: {{ top_margin }},
                  b: {{ bottom_margin }},
                  l: {{ left_margin }}, 
                  r: {{ right_margin }},
                  pad: 4,
                 }
        }
        """
    )
       
    script_template = jinja2.Template(\
    """
        <script type="text/javascript">
           jQuery(document).ready(function(){
               Plotly.plot(
                    document.getElementById("{{ id }}") ,
                    [ {{ data }} ],
                    {{ layout }});
               });
         </script> """
    ) 

    def expand_macro(self, formatter, name, text, args):
        req = formatter.req
        largs, options = parse_args(text,
                                    quotechar = '"', 
                                    escchar = '\\', 
                                    delim = ';', 
                                    delquotes = True)
        if not options.get('query', None):
            raise TracError('Mandatory query argument is missing')
        if options['query'].find('$USER') >= 0:
           options['query'] = options['query']\
               .replace('$USER', "'"+formatter.req.authname+"'")
        id = options.get('id', '')

        x,y = self._get_data(options)
        chart_type =options.get('chart_type', 'bar')
        if chart_type == 'pie':
            data = self.pie_template.render(
                title      = options.get('title', ''),
                name       = options.get('legend', ''),
                chart_type = 'pie',
                labels     = x,
                values     = y,
            )
        else:
            data  = self.bar_and_line_template.render(
                title      = options.get('title', ''),
                name       = options.get('legend', ''),
                chart_type = chart_type,
                x_data     = x,
                y_data     = y,
                )

        try:
            w  = int(options.get('width', self.opt_w))
            h  = int(options.get('height', self.opt_h))
            tm = int(options.get('top_margin', self.opt_tm))
            bm = int(options.get('bottom_margin', self.opt_bm))
            lm = int(options.get('left_margin', self.opt_lm))
            rm = int(options.get('right_margin', self.opt_rm))
        except ValueError as e:
            raise TracError('width/height arguments must be integers. Are values seprated by semicolons?')

        layout = self.layout_template.render(
            title         = options.get('title', ''),
            width         = w,
            height        = h,
            top_margin    = tm,
            bottom_margin = bm,
            left_margin   = lm,
            right_margin  = rm,
            )
            
        script = self.script_template.render(
            id     = id,
            data   = data,
            layout = layout,
            )

        return tag.div( \
            tag.div(id="%s" % id, 
                    ),
            Markup(script)
            )

         
