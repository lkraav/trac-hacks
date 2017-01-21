# -*- coding: utf-8 -*-

import os
from PIL import Image

from trac.db import Table, Column, DatabaseManager

from tracscreenshots.init import db_version_key

tables = [
    Table('screenshot', key='id')[
        Column('id', type='integer', auto_increment=True),
        Column('name'),
        Column('description'),
        Column('time', type='integer'),
        Column('author'),
        Column('tags'),
        Column('file'),
        Column('width', type='integer'),
        Column('height', type='integer')
    ],
    Table('screenshot_component', key='id')[
        Column('id', type='integer', auto_increment=True),
        Column('screenshot', type='integer'),
        Column('component')
    ],
    Table('screenshot_version', key='id')[
        Column('id', type='integer', auto_increment=True),
        Column('screenshot', type='integer'),
        Column('version')
    ]
]


def do_upgrade(env, version, cursor):
    dbm = DatabaseManager(env)

    with env.db_transaction as db:
        # Backup old screenshot table.
        db("""
            CREATE TEMPORARY TABLE screenshot_old AS SELECT * FROM screenshot
            """)
        dbm.drop_tables(('screenshot', 'screenshot_component',
                         'screenshot_version'))
        dbm.create_tables(tables)

        # Get all screenshots from old table.
        columns = ('id', 'name', 'description', 'time', 'author', 'tags',
                   'large_file', 'medium_file', 'small_file')
        screenshots = [dict(zip(columns, row)) for row in db("""
                          SELECT %s FROM screenshot_old
                          """ % ','.join(columns))]

        # Rename images and get its dimensions.
        for screenshot in screenshots:
            # Prepare filename of screenshot image.
            path = os.path.join(env.config.get('screenshots', 'path'),
                                unicode(screenshot['id']))
            old_filename = screenshot['large_file']

            # Open image to get its dimensions.
            image = Image.open(os.path.join(path, old_filename))
            width = image.size[0]
            height = image.size[1]

            # Prepare new filename.
            name, ext = os.path.splitext(old_filename)
            name = name[:-6]
            ext = ext.lower()
            new_filename = '%s-%sx%s%s' % (name, width, height, ext)

            # Save image under different name.
            image.save(os.path.join(path, new_filename))

            # Remove old image files.
            os.remove(os.path.join(path, screenshot['large_file']))
            os.remove(os.path.join(path, screenshot['medium_file']))
            os.remove(os.path.join(path, screenshot['small_file']))

            #  Append new and remove old screenshot attributes.
            screenshot['width'] = width
            screenshot['height'] = height
            screenshot['file'] = name + ext
            del screenshot['large_file']
            del screenshot['medium_file']
            del screenshot['small_file']

        # Copy them to new tables.
        for screenshot in screenshots:
            fields = screenshot.keys()
            values = screenshot.values()
            db("""
                INSERT INTO screenshot (%s)
                VALUES (%s)
                """ % (','.join(fields)), ['%s'] * len(fields),
               tuple(values))

    DatabaseManager(env).set_database_version(version, db_version_key)
