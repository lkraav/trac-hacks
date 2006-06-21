#! /usr/bin/python
from trac.core import *
from trac.env import *
import sys, sre, os, time, optparse

__all__ = ['main', 'rename_page']

def rename_page(env, oldname, newname, user, ip, debug=False, db=None):
    """Rename a wiki page from oldname to newname, using env as the environment."""
    handle_commit = False
    if not db:
        db = env.get_db_cnx()
        handle_commit = True
    cursor = db.cursor()

    sqlbase = ' FROM wiki w1, ' + \
        '(SELECT name, MAX(version) AS max_version FROM wiki GROUP BY name) w2 ' + \
        'WHERE w1.version = w2.max_version AND w1.name = w2.name '

    sql = 'SELECT w1.version,w1.text' + sqlbase + 'AND w1.name = \'%s\'' % oldname
    if debug: print "Running query '%s'" % sql
    cursor.execute(sql)

    row = cursor.fetchone()

    if not row:
        raise TracError, 'Page not found'
    
    new_wiki_page = (newname,row[0]+1,int(time.time()),user,ip,row[1],'Name changed from %s to %s'%(oldname,newname),0)

    # Create a new page with the needed comment
    if debug: print "Inserting new page '%s'" % repr(new_wiki_page)
    cursor.execute('INSERT INTO wiki (name,version,time,author,ipnr,text,comment,readonly) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)', new_wiki_page)

    # Move all the old versions of the page
    if debug: print "Moving all old versions of page"
    cursor.execute('UPDATE wiki SET name=%s WHERE name=%s', (newname,oldname))

    # Move any attachments that are on the page
    if debug: print "Moving all attachments in database"
    cursor.execute('UPDATE attachment SET id=%s WHERE type=%s AND id=%s', (newname,'wiki',oldname))

    if debug: print "Found %s attachments on that page" % cursor.rowcount
    if cursor.rowcount > 0:
        # Change the directory where the attachments are stored, if there were any
        if debug: print "Moving all attachments on file system"
        os.renames(os.path.join(env.path, 'attachments/wiki', oldname), os.path.join(env.path, 'attachments/wiki', newname))

    # Get a list of all wiki pages containing links to the old page
    if debug: print "Trying to fix links"
    sql = 'SELECT w1.version,w1.name,w1.text' + sqlbase + "AND w1.text like '%%[wiki:%s%%'" % oldname
    if debug: print "Running query '%s'" % sql
    cursor.execute(sql)

    # Rewrite all links to the old page, such as to point to the new page
    for row in list(cursor):
        if debug: print "Found a page with a backlink in it: %s (v%s)" % (row[1],row[0])
        newtext = sre.sub('\[wiki:%s'%oldname,'[wiki:%s'%newname,row[2])
        cursor.execute('UPDATE wiki SET text=%s WHERE name=%s AND version=%s', (newtext,row[1],row[0]))

    if handle_commit:
        db.commit()


