# -*- coding: utf-8 -*-
#
# Copyright (c) 2009 Aviram C <aviramc@gmail.com>
# Copyright (c) 2013 Ryan J Ollos <ryan.j.ollos@gmail.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

import random
import string
from collections import defaultdict

from trac.config import IntOption
from trac.core import implements
from trac.db.api import get_column_names
from trac.web.chrome import ITemplateProvider
from trac.wiki.macros import WikiMacroBase
from trac.ticket.query import Query

import openFlashChart
from openFlashChart_varieties import (
    Bar_Stack, Pie, bar_stack_value, pie_value, x_axis_labels
)
from tracadvparseargs import parseargs

COLOURS = [
    '#00FFFF', '#7FFFD4', '#000000', '#0000FF', '#8A2BE2', '#A52A2A',
    '#DEB887', '#5F9EA0', '#7FFF00', '#D2691E', '#FF7F50', '#6495ED',
    '#DC143C', '#00FFFF', '#00008B', '#008B8B', '#B8860B', '#A9A9A9',
    '#A9A9A9', '#006400', '#BDB76B', '#8B008B', '#556B2F', '#FF8C00',
    '#9932CC', '#8B0000', '#E9967A', '#8FBC8F', '#483D8B', '#2F4F4F',
    '#2F4F4F', '#00CED1', '#9400D3', '#FF1493', '#00BFFF', '#696969',
    '#696969', '#1E90FF', '#B22222', '#228B22', '#FF00FF', '#FFD700',
    '#DAA520', '#808080', '#808080', '#008000', '#ADFF2F', '#FF69B4',
    '#CD5C5C', '#4B0082', '#F0E68C', '#7CFC00', '#ADD8E6', '#F08080',
    '#E0FFFF', '#D3D3D3', '#90EE90', '#FFB6C1', '#FFA07A', '#20B2AA',
    '#87CEFA', '#778899', '#778899', '#B0C4DE', '#00FF00', '#32CD32',
    '#FF00FF', '#800000', '#66CDAA', '#0000CD', '#BA55D3', '#9370D8',
    '#3CB371', '#7B68EE', '#00FA9A', '#48D1CC', '#C71585', '#191970',
    '#000080', '#808000', '#6B8E23', '#FFA500', '#FF4500', '#DA70D6',
    '#EEE8AA', '#98FB98', '#AFEEEE', '#D87093', '#FFDAB9', '#CD853F',
    '#FFC0CB', '#DDA0DD', '#B0E0E6', '#800080', '#FF0000', '#BC8F8F',
    '#4169E1', '#8B4513', '#FA8072', '#F4A460', '#2E8B57', '#FFF5EE',
    '#A0522D', '#C0C0C0', '#87CEEB', '#6A5ACD', '#708090', '#708090',
    '#FFFAFA', '#00FF7F', '#4682B4', '#D2B48C', '#008080', '#D8BFD8',
    '#FF6347', '#40E0D0', '#EE82EE', '#FFFF00', '#9ACD32'
]


class TicketChartMacro(WikiMacroBase):
    """
    !TicketChartsMacro - display ticket statistics charts.

    Make various types of charts regarding the number of tickets using
    !OpenFlashCharts.

    Chart types:
      * Pie charts.
      * Bar charts.
      * Stacked bar charts.

    The charts are created by the parameters that you give to the macro. See
    the examples below.

    All charts are clickable (see requirements) and will link to the query page
    of the graph.

    Configuration:
      * The following configuration should appear in trac.ini (default values are shown):
    {{{
    [ticket-charts]
    height = 300
    width = 500
    }}}

    Examples:
    {{{
    Number of tickets per milestone:
    [[TicketChart(type = pie, factor = milestone)]]

    Number of tickets per status for milestone4:
    [[TicketChart(type = pie, factor = status, query = milestone="milestone4")]]

    Number of tickets by status and owners:
    [[TicketChart(type = stacked_bars, key = owner, x_axis = status,
    height = 400, width = 600)]]

    Number of tickets by status and owner for milestone1:
    [[TicketChart(type = stacked_bars, key = owner, x_axis = status,
    query = milestone="milestone1",
    title = Tickets by status and owner for milestone1)]]

    Number of tickets by owner and type:
    [[TicketChart(type = stacked_bars, key = type, x_axis = owner)]]

    Number of tickets by status for milestone4:
    [[TicketChart(type = bars, x_axis = status, query = milestone="milestone4",
    title = Tickets by status for milestone4)]]
    }}}
    """
    implements(ITemplateProvider)

    height = IntOption('ticket-charts', 'height', 300,
                       doc="Default chart height.")

    width = IntOption('ticket-charts', 'width', 500,
                      doc="Default chart width.")

    def expand_macro(self, formatter, name, args):
        """Return some output that will be displayed in the Wiki content.

        `name` is the actual name of the macro (no surprise, here it'll be
        `'HelloWorld'`),
        `args` is the text enclosed in parenthesis at the call of the macro.
            Note that if there are ''no'' parenthesis (like in, e.g.
            [[HelloWorld]]), then `args` is `None`..
        """

        args = _parse_args(args)

        height = args.get('height') or self.height
        width = args.get('width') or self.width

        chart_creation = {'stacked_bars': stacked_bars_graph,
                          'bars': bars_graph,
                          'pie': pie_graph}

        chart, chart_div_id, additional_html = \
            chart_creation[args['type']](formatter.env, args)

        # Using OFCDZ in order to enable links in Bar Stack chart.
        return additional_html + \
               _get_chart_html(chart, chart_div_id,
                               formatter.req.href.chrome(),
                               height=height, width=width)

    ### ITemplateProvider methods

    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('ticketcharts', resource_filename(__name__, 'htdocs'))]

    def get_templates_dirs(self):
        return []


def _parse_args(args, args_dict = None):
    # The plugin of the args parser in not good enough because it doesn't
    # strip white spaces.
    # Since I didn't want to change the plugin itself, I'll do it here...
    args_list, args_keys = parseargs.parse_args(args, strict=False)

    if args_dict is None:
        stripped_args = {}
    else:
        stripped_args = args_dict     # This way we can use defaultdict
        
    for key, value in args_keys.iteritems():
        stripped_args[key] = value.strip()

    # I don't really need a list for arguments without values, I can make
    # their values None...
    for value in args_list:
        stripped_args[value.strip()] = None

    return stripped_args


def _create_chart(title, *elements):
    chart = openFlashChart.template(title)
    for element in elements:
        chart.add_element(element)
    return chart


def _safe_evaluate(string_object, mapping=None, **kw):
    if mapping is None:
        mapping = {}
    return string.Template(string_object).safe_substitute(mapping, **kw)


def _unique_list(iterable):
    return list(set(iterable))


def _create_javascript_array(array_name, values,
                             function=lambda x: x and unicode(x) or ''):
    from trac.util.text import to_js_string
    array_values = ', '.join([to_js_string(function(value))
                              for value in values])
    return 'var %s = new Array(%s)' % (array_name, array_values)


def _create_query_object(env, query, required_columns=None):
    """Create a query object from a query string. If query is None, the default
    Query is returned

    :param required_columns: Columns that must be included in the query.
    """

    if query is None:
        return Query(env, cols=required_columns)

    query_object = Query.from_string(env, query)

    # Add the required_columns
    for column in required_columns or []:
        if column not in query_object.cols:
            query_object.cols.append(column)

    return query_object


def _get_query_sql(env, query, required_columns=None):
    query_object = _create_query_object(env, query, required_columns)
    return query_object.get_sql()


def _get_stacked_bar_chart_stats(env, key, x_axis, query):
    required_columns = [x_axis]
    if key is not None:
        required_columns.append(key)
    sql, args = _get_query_sql(env, query, required_columns)
    db = env.get_db_cnx()
    cursor = db.cursor()
    cursor.execute(sql, args)

    query_columns = get_column_names(cursor)

    # Returning all the keys is kind of an optimization (so that we won't look
    # for all keys later on)
    keys = []
    x_axis_field_index = query_columns.index(x_axis)
    # Handle cases in which key is missing. In such cases, we'll form bar charts.
    if key:
        key_field_index = query_columns.index(key)

    # Stacked bar charts are represented by a dict of dicts:
    # {'x_axis_value' : {'key_value' : number_of_tickets}}
    # Regular bar charts will be here the same, but 'key_value' will be
    # replaced with None.
    ticket_stats = defaultdict(lambda: defaultdict(lambda: 0), {})

    for row in cursor:
        if key:
            key_field_value = row[key_field_index]
        else:
            key_field_value = None
        x_axis_field_value = row[x_axis_field_index]
        ticket_stats[x_axis_field_value][key_field_value] += 1
        keys.append(key_field_value)

    return ticket_stats, _unique_list(keys)


def _get_stacked_bar_max_y_value(ticket_stats):
    # x_axis_stats is a dict that its values are the number of tickets for
    # each key
    return max([sum(x_axis_stats.itervalues())
                for x_axis_stats in ticket_stats.itervalues()])


def _remove_query_special_characters(query):
    # The only special characters I know that need to be removed are the quotes.
    # Quotes must be in the query so that the SQL will be executed correctly,
    # but should not exist in links
    special_characters = ["'", '"']
    for special_character in special_characters:
        query = query.replace(special_character, "")
    return query


def _get_query_link(env, query):
    """
    Get a query in a string format, and return a link to the query
    """
    if query:
        query = _remove_query_special_characters(query)
    query_object = _create_query_object(env, query)

    return query_object.get_href(env.href)


def _create_stacked_bar_on_click_html(env, key, x_axis, ticket_stats, query,
                                      function_name):
    """
    Query in the string format
    """
    query_link = _get_query_link(env, query)
    array_name = 'array_%s' % (function_name, )

    if key:
        key_query_string = """+ "&%s=" + text""" % (key, )
    else:
        key_query_string = ''
    
    on_click_code = _safe_evaluate("""
<script type="text/javascript">
$array_code;

function $function_name(index, text)
{
   document.location = "$query_link&$x_axis=" + $array_name[index] $key_query_string;
}
</script>
""", {'array_code': _create_javascript_array(array_name,
                                             ticket_stats.iterkeys()),
      'function_name': function_name,
      'query_link': query_link,
      'x_axis': x_axis,
      'array_name': array_name,
      'key_query_string': key_query_string})
    return on_click_code


def _get_stacked_bar_tooltip(key, key_value):
    if key:
        key_string = ' of %s %s' % (key, key_value)
    else:
        key_string = ''
    return '#val# #x_label# tickets%s' % (key_string, )


def _stacked_bars_graph(env, key, x_axis, query=None, title=None):
    ticket_stats, keys = _get_stacked_bar_chart_stats(env, key, x_axis, query)

    plot = Bar_Stack()

    # Add the keys to the plot
    key_colours = {}
    for i, key_value in enumerate(keys):
        key_colours[key_value] = COLOURS[i]
        if key:
            plot.append_keys(COLOURS[i], key_value, 13)

    for x_axis_value, tickets_per_key in ticket_stats.iteritems():
        stack = []
        for i, (key_value, number_of_tickets) in enumerate(tickets_per_key.iteritems()):
            stack.append(bar_stack_value(number_of_tickets, key_colours[key_value], _get_stacked_bar_tooltip(key, key_value)))
        plot.append_stack(stack)

    chart_div_id = _create_chart_div_id()
    on_click_function_name = 'on_click_%s' % (chart_div_id, )
    plot['on-click'] = on_click_function_name
    plot['on-click-text'] = '#key#'

    if title is None:
        key_string = ''
        if key:
            key_string = ' and %s' % (key, )
        title = 'Tickets by %s%s' % (x_axis, key_string)

    chart = _create_chart(title, plot)
    if ticket_stats.keys():
        chart.set_x_axis(labels=x_axis_labels(labels=ticket_stats.keys(),
                                              size=13))
        chart.set_y_axis(min=0, max=_get_stacked_bar_max_y_value(ticket_stats))

    return chart, chart_div_id, \
           _create_stacked_bar_on_click_html(env, key, x_axis, ticket_stats,
                                             query, on_click_function_name)


def stacked_bars_graph(env, args):
    # Using **args here would be useful, but I want to be more precise
    return _stacked_bars_graph(env, key=args['key'], x_axis=args['x_axis'],
                               query=args.get('query'),
                               title=args.get('title'))


def bars_graph(env, args):
    # I don't want code repetition, so we'll simply use stacked bars chart
    # without keys. This is kind of a hack, but it's better than copy-paste.
    return _stacked_bars_graph(env, key=None, x_axis=args['x_axis'],
                               query=args.get('query'),
                               title=args.get('title'))


def _get_pie_graph_stats(env, factor, query=None):
    """
    Return a dict in which the keys are the factors and the values are the
    number of tickets of each factor.
    Example:

    >>> _get_pie_graph_stats(env, 'milestone')
    {'milestone1' : 20,
     'milestone2' : 12,
    }
    """
    sql, args = _get_query_sql(env, query, required_columns=[factor, ])
    db = env.get_db_cnx()
    cursor = db.cursor()
    cursor.execute(sql, args)

    query_columns = get_column_names(cursor)
    factor_index = query_columns.index(factor)

    ticket_stats = defaultdict(lambda: 0)
    for row in cursor:
        factor_value = row[factor_index]
        ticket_stats[factor_value] += 1

    return ticket_stats


def _create_pie_graph_on_click_html(env, ticket_stats, factor, query,
                                    function_name):
    query_link = _get_query_link(env, query)
    array_name = 'array_%s' % (function_name, )
    
    on_click_code = _safe_evaluate("""
<script type="text/javascript">
$array_code;

function $function_name(index)
{
    document.location = '$query_link&$factor=' + $array_name[index]
}
</script>
""", {'array_code': _create_javascript_array(array_name,
                                             ticket_stats.iterkeys()),
      'function_name': function_name,
      'query_link': query_link,
      'factor': factor,
      'array_name': array_name})

    return on_click_code


def _pie_graph(env, factor, query=None, title=None):
    """
    Create a pie graph of the number of tickets as a function of the factor.
    factor is a name of a field by which the tickets are counted.
    query can be None or any Trac query by which the data will be collected.
    """
    ticket_stats = _get_pie_graph_stats(env, factor, query)

    pie_values = []
    for factor_value, number_of_tickets in ticket_stats.iteritems():
        pie_values.append(pie_value(number_of_tickets,
                                    label=(factor_value, None, '13'),
                                    ))

    plot = Pie(start_angle=35, animate=True, values=pie_values,
               colours=COLOURS, label_colour='#432BAF')
    plot.set_tooltip('#label# - #val# tickets (#percent#)')

    chart_div_id = _create_chart_div_id()
    on_click_function_name = 'on_click_%s' % (chart_div_id, )
    plot.set_on_click(on_click_function_name)

    if not title:
        title = "Tickets per %s" % (factor, )

    chart = _create_chart(title, plot)

    on_click_html = _create_pie_graph_on_click_html(env, ticket_stats, factor,
                                                    query,
                                                    on_click_function_name)

    return chart, chart_div_id, on_click_html


def pie_graph(env, args):
    return _pie_graph(env, args['factor'], query=args.get('query'),
                      title=args.get('title'))


def _get_random_string(length):
    return ''.join([random.choice(string.letters + string.digits)
                    for i in xrange(length)])


def _create_chart_div_id():
    div_id_prefix = 'chart_'

    random_string = _get_random_string(10)

    return div_id_prefix + random_string


def _get_chart_html(chart_object, chart_div_id, htdocs_dir, height=300,
                    width=500):
    get_data_function = "get_%s" % (chart_div_id, )
    chart_html = """
<script type="text/javascript" src="$htdocs_dir/ticketcharts/js/swfobject.js">
</script>
<script type="text/javascript" src="$htdocs_dir/ticketcharts/js/json2.js">
</script>
<script type="text/javascript">
swfobject.embedSWF("$htdocs_dir/ticketcharts/open-flash-chart.swf",
                   "$chart_div_id", "$width", "$height", "9.0.0", "blah.swf",
                   {"get-data" : "$get_data_function"});
function $get_data_function()
{
  return JSON.stringify($chart_data);
}
</script>
<div id="$chart_div_id"></div>
"""
    return _safe_evaluate(chart_html, chart_div_id=chart_div_id,
                          htdocs_dir=htdocs_dir,
                          width=width, height=height,
                          chart_data=chart_object.encode(),
                          get_data_function=get_data_function)
