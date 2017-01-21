# -*- coding: utf-8 -*-

from trac.core import Component, Interface
from trac.util.datefmt import to_datetime, utc, pretty_timedelta
from trac.wiki.formatter import format_to_oneliner


class IScreenshotChangeListener(Interface):
    """Extension point interface for components that require notification
    when screenshots are created, modified, or deleted."""

    def screenshot_created(req, screenshot):
        """Called when a screenshot is created. Only argument `screenshot` is
        a dictionary with screenshot field values."""

    def screenshot_changed(req, screenshot, old_screenshot):
        """Called when a screenshot is modified.
        `old_screenshot` is a dictionary containing the previous values of the
        fields and `screenshot` is a dictionary with new values. """

    def screenshot_deleted(req, screenshot):
        """Called when a screenshot is deleted. `screenshot` argument is
        a dictionary with values of fields of just deleted screenshot."""


class IScreenshotsRenderer(Interface):
    """Extension point interface for components providing view on
       screenshots."""

    def render_screenshots(req, name):
        """Provides template and data for screenshots view. Inputs request
           object and dictionary with screenshots data and should return tuple
           with template name and content type."""

    def get_screenshots_view(req):
        """Returns tuple with name and title of implemented screenshots
           view."""


class ScreenshotsApi(Component):

    default_priority = 0

    # Get list functions

    def _get_items(self, table, columns, where='', values=()):
        sql_values = {
            'columns': ', '.join(columns),
            'table': table,
            'where': (' WHERE ' + where) if where else ''
        }

        return [dict(zip(columns, row)) for row in self.env.db_query("""
                    SELECT %(columns)s FROM %(table)s %(where)s
                    """ % sql_values, values)]

    def get_versions(self):
        return self._get_items('version', ('name', 'description'))

    def get_components(self):
        return self._get_items('component', ('name', 'description'))

    def get_screenshots(self):
        return self._get_items('screenshot', ('id', 'name', 'description',
                                              'time', 'author', 'tags',
                                              'file', 'width', 'height',
                                              'priority'))

    def get_screenshots_complete(self):
        screenshots = self.get_screenshots()
        for screenshot in screenshots:
            screenshot['components'] = self.get_screenshot_components(
                screenshot['id'])
            screenshot['versions'] = self.get_screenshot_versions(
                screenshot['id'])
        return screenshots

    def get_filtered_screenshots(self, components, versions, relation='or',
                                 orders=('id', 'name', 'time')):
        columns = ('id', 'name', 'description', 'time', 'author', 'tags',
                   'file', 'width', 'height', 'priority')

        # Prepare SQL statement substrings.
        versions_str = ', '.join(['%s'] * len(versions)) or 'NULL'
        components_str = ', '.join(['%s'] * len(components)) or 'NULL'
        orders_str = ', '.join('%s %s' % (field, direction.upper())
                               for field, direction in orders)

        # Join them.
        sql_values = {
            'columns': ', '.join(columns),
            'versions_str': versions_str,
            'none_version_exp': ' OR v.version IS NULL '
                                if 'none' in versions else '',
            'relation': 'AND' if (relation == 'and') else 'OR',
            'components_str': components_str,
            'none_components_exp': ' OR c.component IS NULL '
                                   if 'none' in components else '',
            'orders_str': orders_str
        }
        sql = """
            SELECT DISTINCT %(columns)s
            FROM screenshot s
            LEFT JOIN (SELECT screenshot,version FROM screenshot_version) v
             ON s.id = v.screenshot
            LEFT JOIN (SELECT screenshot,component FROM screenshot_component) c
             ON s.id = c.screenshot
            WHERE (v.version IN (%(versions_str)s) %(none_version_exp)s)
                  %(relation)s
                  (c.component IN (%(components_str)s) %(none_components_exp)s)
            ORDER BY %(orders_str)s
            """ % sql_values

        return [dict(zip(columns, row))
                for row in self.env.db_query(sql, versions + components)]

    def get_new_screenshots(self, start, stop):
        columns = ('id', 'name', 'description', 'time', 'author', 'tags',
                   'file', 'width', 'height')
        return [dict(zip(columns, row)) for row in self.env.db_query("""
                    SELECT %(columns)s FROM screenshot
                    WHERE time BETWEEN %%s AND %%s
                    """ % ','.join(columns), (start, stop))]

    # Get one item functions

    def _get_item(self, table, columns, where='', values=()):
        sql_values = {
            'columns': ', '.join(columns),
            'table': table,
            'where': (' WHERE ' + where) if where else ''
        }
        for row in self.env.db_query("""
                SELECT %(columns)s FROM %(table)s %(where)s
                """ % sql_values, values):
            return dict(zip(columns, row))

    def _format_screenshot(self, context, screenshot):
        screenshot['author'] = format_to_oneliner(self.env, context,
          screenshot['author'])
        screenshot['name'] = format_to_oneliner(self.env, context,
          screenshot['name'])
        screenshot['description'] = format_to_oneliner(self.env, context,
          screenshot['description'])
        screenshot['width'] = int(screenshot['width'])
        screenshot['height'] = int(screenshot['height'])
        screenshot['time'] = pretty_timedelta(to_datetime(screenshot['time'],
          utc))
        return screenshot

    def get_screenshot(self, id):
        screenshot = self._get_item('screenshot', ('id', 'name',
          'description', 'time', 'author', 'tags', 'file', 'width', 'height',
          'priority'), 'id = %s', (id,))

        if screenshot:
            screenshot['components'] = self.get_screenshot_components(
                screenshot['id'])
            screenshot['versions'] = self.get_screenshot_versions(
                screenshot['id'])
            screenshot['width'] = int(screenshot['width'])
            screenshot['height'] = int(screenshot['height'])
            return screenshot
        else:
            return None

    def get_screenshot_by_time(self, time):
        screenshot = self._get_item('screenshot', ('id', 'name',
          'description', 'time', 'author', 'tags', 'file', 'width', 'height',
          'priority'), 'time = %s', (time,))

        if screenshot:
            screenshot['components'] = self.get_screenshot_components(
                screenshot['id'])
            screenshot['versions'] = self.get_screenshot_versions(
                screenshot['id'])
            screenshot['width'] = int(screenshot['width'])
            screenshot['height'] = int(screenshot['height'])
            return screenshot
        else:
            return None

    def get_screenshot_components(self, id):
        return [component for component, in self.env.db_query("""
                    SELECT component FROM screenshot_component
                    WHERE screenshot=%s
                    """, (id,))]

    def get_screenshot_versions(self, id):
        return [version for version, in self.env.db_query("""
                    SELECT version FROM screenshot_version
                    WHERE screenshot=%s
                    """, (id,))]

    # Add item functions

    def _add_item(self, table, item):
        fields = item.keys()
        values = item.values()
        sql_values = {
            'table': table,
            'fields': ', '.join(fields),
            'values': ', '.join(['%s'] * len(fields)),
        }
        self.env.db_transaction("""
                INSERT INTO %(table)s (%(fields)s)
                VALUES (%(values)s)
                """ % sql_values, tuple(values))

    def add_screenshot(self, screenshot):
        self._add_item('screenshot', screenshot)

    def add_component(self, component):
        self._add_item('screenshot_component', component)

    def add_version(self, version):
        self._add_item('screenshot_version', version)

    # Edit item functions

    def _edit_item(self, table, id, item):
        fields = item.keys()
        values = item.values()
        sql_values = {
            'table': table,
            'fields': ', '.join(("%s = %%s" % field) for field in fields),
            'id': id
        }
        self.env.db_transaction("""
                UPDATE %(table)s SET %(fields)s WHERE id=%(id)s
                """ % sql_values, tuple(values))

    def edit_screenshot(self, id, screenshot):
        # Replace components.
        self.delete_components(id)
        for component in screenshot['components']:
            component = {'screenshot': id,
                         'component': component}
            self.add_component(component)

        # Replace versions.
        self.delete_versions(id)
        for version in screenshot['versions']:
            version = {'screenshot': id, 'version': version}
            self.add_version(version)

        # Update screenshot values.
        tmp_screenshot = screenshot.copy()
        del tmp_screenshot['components']
        del tmp_screenshot['versions']
        self._edit_item('screenshot', id, tmp_screenshot)

    # Delete item functions

    def delete_screenshot(self, id):
        self.env.db_transaction("""
            DELETE FROM screenshot WHERE id=%s
            """, (id,))

        self.delete_versions(id)
        self.delete_components(id)

    def delete_versions(self, id):
        self.env.db_transaction("""
            DELETE FROM screenshot_version WHERE screenshot=%s
            """, (id,))

    def delete_components(self, id):
        self.env.db_transaction("""
            DELETE FROM screenshot_component WHERE screenshot=%s
            """ % (id,))
