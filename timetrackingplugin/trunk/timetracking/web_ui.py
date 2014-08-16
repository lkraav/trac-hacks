# -*- coding: utf-8 -*-

from datetime import datetime

from genshi.builder import tag

from trac.admin import *
from trac.core import *
from trac.util.datefmt import parse_date
from trac.util.presentation import Paginator
from trac.web.chrome import Chrome, add_link, add_script, add_stylesheet, add_notice, add_warning

from timetracking.model import LogEntry, Task

class LogEntryAdminPanel(Component):

    implements(IAdminPanelProvider)

    # IAdminPanelProvider methods

    def get_admin_panels(self, req):
        if 'TIME_TRACKING' in req.perm:
            yield ('timetracking', "Time Tracking", 'log', "Log")
            yield ('timetracking', "Time Tracking", 'tasks', "Tasks")

    def render_admin_panel(self, req, category, panel, path_info):
        req.perm.require('TIME_TRACKING')

        if panel == 'log':
            return self.render_log_panel(req, category, panel, path_info)
        if panel == 'tasks':
            return self.render_tasks_panel(req, category, panel, path_info)

    def render_log_panel(self, req, category, panel, path_info):
        # Detail view?
        if path_info:
            id = path_info
            logentry = LogEntry.select_by_id(self.env, id)
            if not logentry:
                raise TracError("Log entry does not exist!")
            if req.method == 'POST':
                if req.args.get('save'):
                    logentry.date = parse_date(req.args.get('date'))
                    logentry.location = req.args.get('location')
                    logentry.spent_hours = int(req.args.get('spent_hours'))
                    logentry.task_id = int(req.args.get('task_id'))
                    logentry.comment = req.args.get('comment')
                    LogEntry.update(self.env, logentry)
                    add_notice(req, 'Your changes have been saved.')
                    task = Task.select_by_id(self.env, logentry.task_id)
                    if task is None:
                        add_warning(req, 'Task does not exist!')
                    elif logentry.date.year != task.year:
                        add_warning(req, 'Inconsistent date (%s) and task year (%s)!' % (logentry.date.year, task.year))
                    req.redirect(req.href.admin(category, panel))
                elif req.args.get('cancel'):
                    req.redirect(req.href.admin(category, panel))

            tasks = Task.select_by_year(self.env, logentry.date.year)
            tasks_by_id = dict((task.id, task) for task in tasks)

            if logentry.task_id not in tasks_by_id:
                task = Task.select_by_id(self.env, logentry.task_id)
                if task is None:
                    add_warning(req, 'Task does not exist!')
                else:
                    tasks.append(task)
                    tasks_by_id[task.id] = task
                    add_warning(req, 'Inconsistent date (%s) and task year (%s)!' % (logentry.date.year, task.year))

            Chrome(self.env).add_wiki_toolbars(req)
            data = {'view': 'detail',
                    'entry': logentry,
                    'tasks': tasks,
                    'tasks_by_id': tasks_by_id,
            }

        else:
            user = req.args.get('user', req.authname)
            year = int(req.args.get('year', datetime.now().year))
            if req.method == 'POST':
                if req.args.get('add'):
                    # Add Entry
                    logentry = LogEntry(None, None, None, None, None, None, None)
                    logentry.user = user
                    logentry.date = parse_date(req.args.get('date'))
                    logentry.location = req.args.get('location')
                    logentry.spent_hours = int(req.args.get('spent_hours'))
                    logentry.task_id = int(req.args.get('task_id'))
                    logentry.comment = req.args.get('comment')
                    LogEntry.add(self.env, logentry)
                    add_notice(req, 'The entry has been added.')
                    task = Task.select_by_id(self.env, logentry.task_id)
                    if task is None:
                        add_warning(req, 'Task does not exist!')
                    elif logentry.date.year != task.year:
                        add_warning(req, 'Inconsistent date (%s) and task year (%s)!' % (logentry.date.year, task.year))
                    req.redirect(req.href.admin(category, panel, user=user, year=year))
                elif req.args.get('remove'):
                    # Remove entries
                    logentry_ids = req.args.get('sel')
                    if not logentry_ids:
                        raise TracError('No entries selected')
                    if not isinstance(logentry_ids, list):
                        logentry_ids = [logentry_ids]
                    LogEntry.delete_by_ids(self.env, logentry_ids)
                    add_notice(req, 'The entries have been removed.')
                    req.redirect(req.href.admin(category, panel, user=user, year=year))

            users = sorted(username for username, name, email in self.env.get_known_users())
            if users and user not in users:
                user = users[0]

            years = Task.get_known_years(self.env)
            if year not in years:
                years.append(year)

            tasks = Task.select_by_year(self.env, year)
            tasks_by_id = dict((task.id, task) for task in tasks)

            #Pagination
            page = int(req.args.get('page', 1))
            max_per_page = int(req.args.get('max', 10))

            entries = LogEntry.select_by_user_paginated(self.env, user, page, max_per_page)
            total_count = LogEntry.count_by_user(self.env, user)

            paginator = Paginator(entries, page - 1, max_per_page, total_count)
            if paginator.has_next_page:
                next_href = req.href.admin(category, panel, user=user, max=max_per_page, page=page + 1)
                add_link(req, 'next', next_href, 'Next Page')
            if paginator.has_previous_page:
                prev_href = req.href.admin(category, panel, user=user, max=max_per_page, page=page - 1)
                add_link(req, 'prev', prev_href, 'Previous Page')
    
            pagedata = []
            shown_pages = paginator.get_shown_pages(21)
            for page in shown_pages:
                pagedata.append([req.href.admin(category, panel, user=user, max=max_per_page, page=page), None,
                                str(page), 'Page %d' % (page,)])
            paginator.shown_pages = [dict(zip(['href', 'class', 'string', 'title'], p)) for p in pagedata]
            paginator.current_page = {'href': None, 'class': 'current',
                                    'string': str(paginator.page + 1),
                                    'title':None}

            data = {'view': 'list',
                    'paginator': paginator,
                    'max_per_page': max_per_page,
                    'entries': entries,
                    'selected_user': user,
                    'users': users,
                    'selected_year': year,
                    'years': years,
                    'tasks': tasks,
                    'tasks_by_id': tasks_by_id,
            }

        Chrome(self.env).add_jquery_ui(req)
        add_script(req, 'timetracking/chosen/chosen.jquery.js')
        add_stylesheet(req, 'timetracking/chosen/chosen.css')
        return 'timetracking_logentries.html', data

    def render_tasks_panel(self, req, category, panel, path_info):
        # Detail view?
        if path_info:
            id = path_info
            task = Task.select_by_id(self.env, id)
            if task is None:
                raise TracError("Task does not exist!")
            if req.method == 'POST':
                if req.args.get('save'):
                    task.name = req.args.get('name')
                    task.description = req.args.get('description')
                    task.project = req.args.get('project')
                    task.category = req.args.get('category')
                    task.year = int(req.args.get('year'))
                    task.estimated_hours = int(req.args.get('estimated_hours'))
                    Task.update(self.env, task)
                    add_notice(req, 'Your changes have been saved.')
                    req.redirect(req.href.admin(category, panel))
                elif req.args.get('cancel'):
                    req.redirect(req.href.admin(category, panel))
            Chrome(self.env).add_wiki_toolbars(req)
            data = {'view': 'detail', 'task': task}
        else:
            year = int(req.args.get('year', datetime.now().year))
            if req.method == 'POST':
                if req.args.get('add'):
                    # Add Task
                    task = Task(None, None, None, None, None, None, None)
                    task.name = req.args.get('name')
                    task.description = req.args.get('description')
                    task.project = req.args.get('project')
                    task.category = req.args.get('category')
                    task.year = year
                    task.estimated_hours = int(req.args.get('estimated_hours'))
                    Task.add(self.env, task)
                    add_notice(req, 'The task has been added.')
                    req.redirect(req.href.admin(category, panel, year=year))
                elif req.args.get('remove'):
                    # Remove tasks
                    task_ids = req.args.get('sel')
                    if not task_ids:
                        raise TracError('No tasks selected')
                    if not isinstance(task_ids, list):
                        task_ids = [task_ids]
                    Task.delete_by_ids(self.env, task_ids)
                    add_notice(req, 'The tasks have been removed.')
                    orphaned_entries = LogEntry.select_by_task_ids(self.env, task_ids)
                    if orphaned_entries:
                        add_warning(req, tag('Orphaned log entries: ', tag.ul(tag.li(tag.a("log:%s" % e.id, href=req.href.admin('timetracking', 'log', e.id))) for e in orphaned_entries)))
                    req.redirect(req.href.admin(category, panel, year=year))

            years = Task.get_known_years(self.env)
            if year not in years:
                years.append(year)

            tasks = Task.select_by_year(self.env, year)

            data = {'view': 'list',
                    'tasks': tasks,
                    'selected_year': year,
                    'years': years,
            }

        add_script(req, 'timetracking/chosen/chosen.jquery.js')
        add_stylesheet(req, 'timetracking/chosen/chosen.css')
        return 'timetracking_tasks.html', data
