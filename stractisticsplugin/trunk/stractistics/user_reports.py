# -*- coding: utf-8 -*-
#
# Copyright (C) 2008 GMV SGI Team <http://www.gmv-sgi.es>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

from trac.util.datefmt import from_utimestamp, to_datetime, to_utimestamp

from util import *


def user_reports(req, env, config):
    data = {}
    start, end, weeks_back = parse_time_gap(req, data)

    trac_users = _retrieve_trac_users(req, config, env)
    data['trac_users'] = trac_users
    user = _get_default_user(req.args, trac_users)
    data['default_user'] = user

    data['repository_activity'] = _user_svn_activity(req, user, config,
                                        start, end, weeks_back, env)

    data['wiki_activity'] = _user_wiki_activity(req, env, user, config,
                                                start, end, weeks_back)

    data['ticket_activity'] = _user_ticket_activity(req, user, config, start, end,
                                         weeks_back, env)
    return 'user_reports.html', data

def _user_ticket_activity(req, user, config, start, end, weeks_back, env):
    """
    This function calculates:
      * number of tickets opened per week
      * number of tickets closed per week
      * number of tickets assigned per week <-- NO
      * number of tickets reopened per week
    between start and end
    """
    created = _get_created_tickets(env, user, start, end)
    closed_or_reopened = _get_closed_or_reopened_tickets(env, user, start, end)

    weeks_dic = get_weeks_elapsed(start, end)
    tickets_data = _count_tickets(created, closed_or_reopened, weeks_dic)

    weeks_list = weeks_dic.keys()
    weeks_list.sort()
    weeks_list = [swap_week_year(week) for week in weeks_list]


    query_response = QueryResponse("ticket_activity", req.href('/chrome'))
    query_response.set_title("Ticket activity (last %s weeks)" % weeks_back)

    columns, rows = adapt_to_table(weeks_list, tickets_data, config)
    query_response.set_columns(columns)
    query_response.set_results(rows)

    chart = query_response.chart_info
    chart.type = 'Line'
    chart.x_labels = weeks_list
    chart.x_legend = 'Weeks'
    chart.y_legend = 'Tickets'
    chart.data = tickets_data
    chart.set_tool_tip("#key#<br>week:#x_label#<br>tickets:#val#")
    return query_response

def _count_tickets(created, closed_or_reopened, weeks_dic):
    tickets_data = {'created': dict(weeks_dic),
                    'closed': dict(weeks_dic),
                    'reopened': dict(weeks_dic)
                    }
    for ticket in created:
        week = format_to_week(ticket[1])
        tickets_data['created'][week] += 1
    for ticket in closed_or_reopened:
        week = format_to_week(ticket[1])
        action = ticket[2]
        if action == 'closed':
            tickets_data['closed'][week] += 1
        elif action == 'reopened':
            tickets_data['reopened'][week] += 1

    for category in tickets_data.iterkeys():
        tickets_data[category] = sort_values_by_key(tickets_data[category])
    return tickets_data

def _get_created_tickets(env, user, start, end):
    """
    Retrieves all the tickets created by 'user' between start and date.
    """
    sql_expr = """
    SELECT id, time
    FROM ticket
    WHERE reporter = '%s' AND time >= %s AND time <= %s
    """
    sql_expr = sql_expr % (user,
                           datetime_to_secs(start),
                           datetime_to_secs(end))
    def map_rows(xx):
        import datetime
        return xx[0], datetime.datetime.fromtimestamp(xx[1]), None
    user_created_tickets = execute_sql_expression(env, sql_expr, map_rows)
    return user_created_tickets

def _get_closed_or_reopened_tickets(env, user, start, end):
    """
    Retrieves all the tickets closed or reopened by 'user' between start
    and date.
    """
    sql_expr = """
    SELECT  ticket, time, newvalue
    FROM ticket_change
    WHERE author = '%s' AND time >= %s AND time <= %s
        AND (newvalue = 'closed' or newvalue = 'reopened')
    """
    sql_expr = sql_expr % (user,
                           datetime_to_secs(start),
                           datetime_to_secs(end))
    def map_rows(xx):
        import datetime
        return xx[0], datetime.datetime.fromtimestamp(xx[1]), xx[2]
    closed_or_reopened_tickets = execute_sql_expression(env, sql_expr, map_rows)
    return closed_or_reopened_tickets


def _user_wiki_activity(req, env, user, config, start, end, weeks_back):
    """
    Computes the number of pages created and the number of pages edited by the
    user between start and end.
    """
    wiki_pages = []
    for time, version in env.db_query("""
            SELECT time, version
            FROM wiki
            WHERE author=%s AND time>=%s AND time<=%s
        """, (user, to_utimestamp(to_datetime(start, req.tz)),
              to_utimestamp(to_datetime(end, req.tz)))):
        wiki_pages += [(from_utimestamp(time), version)]

    weeks_dic = get_weeks_elapsed(start, end)
    wiki_data = _group_wiki_pages(wiki_pages, weeks_dic)

    weeks_list = weeks_dic.keys()
    weeks_list.sort()
    weeks_list = [swap_week_year(week) for week in weeks_list]

    query_response = QueryResponse("wiki_activity", req.href('/chrome'))
    query_response.set_title("Wiki activity (last %s weeks)" % weeks_back)
    columns, rows = adapt_to_table(weeks_list, wiki_data, config)
    query_response.set_columns(columns)
    query_response.set_results(rows)

    chart = query_response.chart_info
    chart.type = 'Line'
    chart.x_labels = weeks_list
    chart.x_legend = 'Weeks'
    chart.y_legend = 'Pages'
    chart.data = wiki_data
    chart.set_tool_tip("#key#<br>week:#x_label#<br>pages:#val#")
    return query_response

def _group_wiki_pages(wiki_pages, weeks_dic):
    """
    Counts how many page editions and how many wiki page creations per week
    the user has done.
    """
    wiki_data = {'created' : dict(weeks_dic),
                 'modified' : dict(weeks_dic)
                 }
    for wiki in wiki_pages:
        week = format_to_week(wiki[0])
        version = wiki[1]
        if version == 1:
            wiki_data['created'][week] += 1
        else:
            wiki_data['modified'][week] +=1
    for action in wiki_data:
        wiki_data[action] = sort_values_by_key(wiki_data[action])
    return wiki_data

def _user_svn_activity(req, user, config, start, end, weeks_back, env):
    """
    Computes the number of commits per week done by the user between start
    and end.
    """
    sql_expr = """
    SELECT rr.time
    FROM revision rr
    WHERE rr.author ='%s' AND time > %s AND time < %s
    """
    sql_expr = sql_expr % (user,
                           datetime_to_secs(start),
                           datetime_to_secs(end))
    def map_rows(xx):
        import datetime
        return datetime.datetime.fromtimestamp(xx[0])
    raw_commits = execute_sql_expression(env, sql_expr, map_rows)

    weeks_dic = get_weeks_elapsed(start, end)
    commits_per_week = _count_commits(user, raw_commits, weeks_dic)

    weeks_list = weeks_dic.keys()
    weeks_list.sort()
    weeks_list = [swap_week_year(week) for week in weeks_list]

    query_response = QueryResponse("svn_activity", req.href('/chrome'))
    query_response.set_title("SVN activity (last %s weeks)" % weeks_back)

    columns, rows = adapt_to_table(weeks_list, commits_per_week, config)
    query_response.set_columns(columns)
    query_response.set_results(rows)

    weeks_list = [swap_week_year(week) for week in weeks_list]

    chart = query_response.chart_info
    chart.type = 'Line'
    chart.x_labels = weeks_list
    chart.x_legend = 'Weeks'
    chart.y_legend = 'Commits'
    chart.data = restructure_data(commits_per_week)
    chart.set_tool_tip("#key#<br>week:#x_label#<br>commits:#val#")
    return query_response

def _count_commits(user, commits, weeks_dic):
    """
    We count how many commits per week the user has submitted.
    """
    user_data = dict(weeks_dic)
    svn_data = {}
    for com in commits:
        week = format_to_week(com)
        user_data[week] += 1
    svn_data[user] = user_data

    for user in svn_data:
        svn_data[user] = sort_values_by_key(svn_data[user])
    return svn_data

def _get_default_user(args, trac_users):
    default_user = trac_users[0]
    if args.has_key('user'):
        url_user = args['user']
        if url_user in trac_users:
            default_user = url_user
    return default_user


#If I figure a database independent query to do this, this function code
#will go the way of the dodo.
def _retrieve_trac_users(req, config, env):
    """
    Returns a list with the user name of whoever has ever committed to the
    repository, contributed to the wiki, modified or created a ticket.
    Trac DB doesn't contain a table with user names so we need to search
    across tables to collect user names.
    Syntax for performing left outer joins are database dependent so I prefer
    three independent queries and then gather the results manually.
    """
    users_list = []

    wiki_users = _retrieve_wiki_users(config, env)
    ticket_users = _retrieve_ticket_users(config, env)
    repo_users = _retrieve_repo_users(config, env)
    print "wiki_users %r" % wiki_users
    print "ticket_users %r" % ticket_users
    print "repo_users %r" % repo_users
    #Not elegant at all.
    users_list.extend(wiki_users)
    users_list.extend(ticket_users)
    users_list.extend(repo_users)
    users_list = remove_duplicates(users_list)

    return users_list


def _retrieve_wiki_users(config, env):
    sql_expr = """
        SELECT DISTINCT ww.author
        FROM wiki ww;
    """
    wiki_users = execute_sql_expression(env, sql_expr, lambda x:x[0])
    return wiki_users


def _retrieve_repo_users(config, env):
    sql_expr = """
        SELECT DISTINCT rr.author
        FROM revision rr;
    """
    repo_users = execute_sql_expression(env, sql_expr, lambda x:x[0])
    return repo_users


def _retrieve_ticket_users(config, env):
    """
    We are interested only in those users who have either created, closed,
    reopened or accepted a ticket.
    """

    sql_expr = "SELECT DISTINCT author FROM ticket_change"
    tc_users = execute_sql_expression(env, sql_expr, lambda x:x[0])

    sql_expr = "SELECT DISTINCT reporter FROM ticket"
    reporters = execute_sql_expression(env, sql_expr, lambda x:x[0])
    tc_users.extend(reporters)
    ticket_users = remove_duplicates(tc_users)

    return ticket_users
