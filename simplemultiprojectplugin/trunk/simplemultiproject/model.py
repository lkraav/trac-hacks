# -*- coding: utf-8 -*-
#
# Copyright (C) 2011 Christopher Paredes
#

from trac.core import Component


class SmpModel(Component):
    # Common Methods

    def get_all_projects(self):
        projects = self.env.db_query("""
                SELECT id_project,name,summary,description,closed,restrict_to
                FROM smp_project
                """)

        project_names = [r[1] for r in sorted(projects, key=lambda k: k[1])]
        self.config.set('ticket-custom', 'project.options',
                        '|'.join(project_names))

        return projects

    # AdminPanel Methods

    def insert_project(self, name, summary, description, closed, restrict):
        self.env.db_transaction("""
                INSERT INTO smp_project
                  (name, summary, description, closed, restrict_to)
                VALUES (%s,%s,%s,%s,%s)
                """, (name, summary, description, closed, restrict))

        # Keep internal list of values for ticket-custom field 'project'
        # updated. This list is used for the dropdown on the query page.
        self.get_all_projects()
