# -*- coding: utf-8 -*-
#
# Copyright (C) 2018 Theodor Norup <theodor.norup@gmail.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

import re

from trac.config      import ListOption
from trac.core        import *
from trac.web.chrome  import ITemplateProvider, add_script
from trac.web.main    import IRequestFilter, IRequestHandler
from trac.wiki.macros import WikiMacroBase
from trac.util.html   import tag, Fragment, Markup

from tracadvparseargs import *

import jinja2

print 'LOADED!'


class yachart(WikiMacroBase):
    implements(ITemplateProvider, IRequestFilter)

    """Embed a bar/line/bar chart in a wiki page.

    Example:
    {{{
        [[yachart(id=chart1; title=Ticket statuses; query=SELECT status , COUNT(status) FROM ticket GROUP BY status)]]
    }}}
    """
    # ITemplateProvider methods
    def get_htdocs_dirs(self):
        print 'IN get_htdocs_dirs'
        from pkg_resources import resource_filename
        return [('yachart', resource_filename(__name__, 'htdocs'))]

    def get_templates_dirs(self):
        print 'IN get_templates_dirs'
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]

    # IRequestFilter methods
    def pre_process_request(self, req, handler):
        return handler

    def post_process_request(self, req, template, data, content_type):
        if True: #self._is_valid_request(req):
            add_script(req, 'yachart/plotly-latest.min.js')
        return template, data, content_type

    # private methods


    def _get_data(self, options):
        q = self.env.db_query(options.get('query', None), ())
        x,y = ([],[])
        for r in q:
            x.append(str(r[0]))
            y.append(str(r[1]))
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
        title: '{{ title }}',
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
        print text, type(options), options, args
        #options = eval("dict(%s)" % text)
        if not options.get('query', None):
            raise TracError('Mandatory query argument is missing')
        if options['query'].find('$USER') >= 0:
           options['query'] = options['query']\
               .replace('$USER', "'"+formatter.req.authname+"'")
        id = options.get('id', '')
        try:
            w = int(options.get('width', 600))
            h = int(options.get('height', 400))
        except ValueError as e:
            raise TracError('width/height arguments must be integers')

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

        layout = self.layout_template.render(
            title =  options.get('title', ''),
            )
            
        script = self.script_template.render(
            id     = id,
            data   = data,
            layout = layout,
            )

        return tag.div( \
            tag.div(id="%s" % id, 
                    style="width: %dpx;height:%dpx;" % (w,h)
                    ),
            Markup(script)
            )

         
