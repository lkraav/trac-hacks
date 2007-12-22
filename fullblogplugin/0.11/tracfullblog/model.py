# -*- coding: utf-8 -*-
"""
Entity models supporting the basic features of the plugin.
 * CRUD code - create, read, update and delete.
 * Various get and search util function for getting lists of items

License: BSD

(c) 2007 ::: www.CodeResort.com - BV Network AS (simon-code@bvnetwork.no)
"""

import datetime
from operator import itemgetter

from trac.attachment import Attachment
from trac.resource import Resource
from trac.search import search_to_sql
from trac.util.compat import sorted, set
from trac.util.datefmt import to_datetime, to_timestamp, utc, localtz
from trac.util.text import to_unicode

__all__ = ['BlogComment', 'BlogPost', 'get_months_authors_categories',
           'search_blog_posts', 'search_blog_comments',
           'get_blog_posts', 'get_blog_comments',
           'group_posts_by_month']

# Public functions

def search_blog_posts(env, terms):
    """ Free text search for content of blog posts.
    Input is a list of terms.
    Returns a list of tuples with:
        (name, version, publish_time, author, title, body) """
    assert terms
    cnx = env.get_db_cnx()
    cursor = cnx.cursor()
    # SQL
    columns = ['bp1.name', 'bp1.title', 'bp1.body',
               'bp1.author', 'bp1.categories']
    search_clause, args = search_to_sql(cnx, columns, terms)
    sql = "SELECT bp1.name, bp1.version, bp1.publish_time, bp1.author, " \
               "bp1.title, bp1.body " \
               "FROM fullblog_posts bp1," \
               "(SELECT name, max(version) AS ver " \
               "FROM fullblog_posts GROUP BY name) bp2 " \
               "WHERE bp1.version = bp2.ver AND bp1.name = bp2.name " \
               "AND " + search_clause
    env.log.debug("search_blog_posts() SQL: %r" % sql)
    cursor.execute(sql, args)
    # Return the items we have found
    return [(row[0], row[1], to_datetime(row[2], utc), row[3],
            row[4], row[5]) for row in cursor]

def search_blog_comments(env, terms):
    """ Free text search for content of blog posts.
    Input is a list of terms.
    Returns a list of tuples with:
        (post_name, comment_number, comment, comment_author, comment_time) """
    assert terms
    cnx = env.get_db_cnx()
    cursor = cnx.cursor()
    # SQL
    columns = ['author', 'comment']
    search_clause, args = search_to_sql(cnx, columns, terms)
    sql = "SELECT name, number, comment, author, time " \
          "FROM fullblog_comments WHERE " + search_clause
    env.log.debug("search_blog_comments() SQL: %r" % sql)
    cursor.execute(sql, args)
    # Return the items we have found
    return [(row[0], row[1], row[2], row[3], to_datetime(row[4], utc))
            for row in cursor]

def get_blog_posts(env, category='', author='', from_dt=None, to_dt=None,
        all_versions=False):
    """ Utility method to fetch one or more posts from the database.

    Needs one or more selection criteria (empty will not restrict search):
     * category - posts needs to be tagged with the catogory (contains)
     * user - posts with given user as author (equeals)
     * from_dt - posted on or after the given time (datetime)
     * to_dt - posted on or before the given time (datetime)
     * all_versions - if all versions are needed, like for timeline display
    
    Note: For datetime criteria the 'publish_time' is the default field searched,
    but if all_versions is requested the 'version_time' is used instead.
    
    Returns a list of tuples of the form:
        (name, version, time, author, title, body, category_list)
    Use 'name' and 'version' to instantiate BlogPost objects."""

    cnx = env.get_db_cnx()
    cursor = cnx.cursor()

    # Build the list of WHERE restrictions
    time_field = 'bp1.publish_time'
    join_operation = ",(SELECT name, max(version) AS ver " \
                     "FROM fullblog_posts GROUP BY name) bp2 " \
                     "WHERE bp1.version = bp2.ver AND bp1.name = bp2.name "
    where_clause = ""
    where_values = None
    if all_versions:
        time_field = 'bp1.version_time'
        join_operation = ""
    elif category:
        # Make sure we use a valid category when only latest version,
        # if not return empty. Needed as we do LIKE and can catch all
        # kinds of permutations of the category input text.
        valid_categories = [cat for cat, count in
                get_months_authors_categories(env)[2]]
        if not category in valid_categories:
            return [] 
    args = [category and ("bp1.categories "+cnx.like(), "%"+category+"%"),
            author and ("bp1.author=%s", author) or None,
            from_dt and (time_field+">%s", to_timestamp(from_dt)) or None,
            to_dt and (time_field+"<%s", to_timestamp(to_dt)) or None]
    args = [arg for arg in args if arg]  # Ignore the None values
    if args:
        where_start = "AND "
        if not join_operation:
            where_start = "WHERE "
        where_clause = where_start + " AND ".join([arg[0] for arg in args])
        where_values = tuple([arg[1] for arg in args])

    # Run the SQL
    sql = "SELECT bp1.name, bp1.version, bp1.publish_time, bp1.author, " \
               "bp1.title, bp1.body, bp1.categories " \
               "FROM fullblog_posts bp1 " \
               + join_operation + where_clause \
               + " ORDER BY bp1.publish_time DESC"
    env.log.debug("get_blog_posts() SQL: %r (%r)" % (sql, where_values))
    cursor.execute(sql, where_values)

    # Return the rows
    blog_posts = []
    for row in cursor:
        # Extra check needed to weed out almost-matches where requested
        # category is a substring of another (searched using LIKE)
        categories = _parse_categories(row[6])
        if category and category not in categories:
            continue
        blog_posts.append((row[0], row[1], to_datetime(row[2], utc), row[3],
                row[4], row[5], categories))
    return blog_posts

def get_blog_comments(env, post_name='', from_dt=None, to_dt=None):
    """ Returns comments as a list of tuples from search based on
    AND input for post_name, and datetime span (from_dt and to_dt):
        (post_name, number, comment, author, time) 
    Instantiate BlogComment objects to get further details of each.
    Example of sorting the output by time, newest first:
        from trac.util.compat import sorted
        from operator import itemgetter
        comments = get_blog_comments(env)
        sorted(comments, key=itemgetter(4), reverse=True) """

    # Build the list of WHERE restrictions
    args = [post_name and ("name=%s", post_name) or None,
            from_dt and ("time>%s", to_timestamp(from_dt)) or None,
            to_dt and ("time<%s", to_timestamp(to_dt)) or None]
    args = [arg for arg in args if arg]
    where_clause = ""
    where_values = None
    if args:
        where_clause = "WHERE " + " AND ".join([arg[0] for arg in args])
        where_values = tuple([arg[1] for arg in args])

    # Do the SELECT
    cnx = env.get_db_cnx()
    cursor = cnx.cursor()
    sql = "SELECT name, number, comment, author, time " \
            "FROM fullblog_comments " + where_clause
    env.log.debug("get_blog_comments() SQL: %r (%r)" % (sql, where_values))
    cursor.execute(sql, where_values or None)

    # Return the items we have found
    return [(row[0], row[1], row[2], row[3], to_datetime(row[4], utc))
            for row in cursor]

def get_months_authors_categories(env, from_dt=None, to_dt=None):
    """ Returns a structure of post metadata:
        ([ ((year1, month1), count), ((year1, month2), count) ], # newest first
         [ (author1, count), (author2, count) ],                 # alphabetical
         [ (category1, count), (category2, count) ],             # alphabetical
         total )                                                 # num of posts
    * Use 'from_dt' and 'to_dt' (datetime objects) to restrict search to
    posts with a publish_time within the intervals (None means ignore).
    * Note also that it only fetches from most recent version. """
    blog_posts = get_blog_posts(env, from_dt=from_dt, to_dt=to_dt)
    a_dict = {}
    c_dict = {}
    m_dict = {}
    total = 0
    for post in blog_posts:
        post_time = post[2]
        m_dict[(post_time.year, post_time.month)] = m_dict.get(
                (post_time.year, post_time.month), 0) + 1
        author = post[3]
        a_dict[author] = a_dict.get(author, 0) + 1
        categories = post[6] # a list
        for category in set(categories):
            c_dict[category] = c_dict.get(category, 0) + 1
        total += 1
    return ([(m, m_dict.get(m, 0)) for m in sorted(m_dict.keys(), reverse=True)],
            [(a, a_dict.get(a, 0)) for a in sorted(a_dict.keys())],
            [(c, c_dict.get(c, 0)) for c in sorted(c_dict.keys())],
            total )

# Utility functions

def group_posts_by_month(posts):
    """ Groups the posts into time periods (months, and return them
    using the following return format:
        [(datetime(year, month, 1), [posts_for_period])]
    It presumes the input is a sorted list of posts, newest first. And,
    that the format of 'view' is the one returned from get_blog_posts(). """
    grouped_list = []
    count = len(posts)
    if not count:
        return [()]
    # Get starting period from first post
    current_period = datetime.datetime(
                posts[0][2].year, posts[0][2].month, 1)
    posts_per_month = []
    for index, post in enumerate(posts):
        year = post[2].year
        month = post[2].month
        if (current_period.month != month) or (
                current_period.year != year):
            # New period starting
            grouped_list.append((current_period, posts_per_month))
            current_period = datetime.datetime(year, month, 1)
            posts_per_month = [post,]
        else:
            posts_per_month.append(post)
        if count == index + 1:
            # Last one, append it before exiting
            grouped_list.append((current_period, posts_per_month))
    return grouped_list

# Internal functions
    
def _parse_categories(categories, sep=' '):
    """ Parses the string containing categories separated by sep.
    Internal method, used in case we want to change split strategy later. """
    categories = categories.replace(',', ' ') # drop commas
    categories = categories.replace(';', ' ') # drop semi-colons
    # Return the list, leaving out any empty items from split()
    return [category for category in categories.split(sep) if category]

# Classes

class BlogComment(object):
    """ Model class representing a comment on a given post.
    Various methods supporting CRUD management of the comment. """
    
    # Default values (fields from table)
    post_name = '' # required ('name' = column definition)
    number = 0     # auto
    comment = ''   # required
    author = ''    # required
    time = datetime.datetime.now(utc) # Now
    
    def __init__(self, env, post_name, number=0):
        """ Requires a name for the blog post that the comment belongs to.
        If no comment_id is passed, it is assumed to not exist. """
        self.env = env
        self.post_name = post_name
        if number:
            self._load_comment(number)
    
    def create(self, comment='', author=''):
        """ Creates a comment in the database.
        Comment and author needs to be set either by passing values
        as args, or previously setting them as properties on the object
        and not passing values. """
        comment = comment or self.comment
        author = author or self.author
        if not (comment and author):
            return False
        if self.number:
            return False
        if not comment or not author:
            return False
        cnx = self.env.get_db_cnx()
        cursor = cnx.cursor()
        number = self._next_comment_number()
        if not number:
            self.env.log.debug("Cannot create comment from %r as post %r "
                "does not exist." % (author, self.post_name))
            return False
        self.env.log.debug("Creating blog comment number %d for %r" % (
                number, self.post_name))
        cursor.execute("INSERT INTO fullblog_comments "
                "VALUES (%s, %s, %s, %s, %s)", (self.post_name,
                number, comment, author, to_timestamp(self.time)) )
        cnx.commit()
        self._load_comment(number)
        return True
    
    def delete(self):
        if not self.post_name and not self.number:
            return False
        cnx = self.env.get_db_cnx()
        cursor = cnx.cursor()
        self.env.log.debug("Deleting blog comment number %d for %r" % (
                self.number, self.post_name))
        cursor.execute("DELETE FROM fullblog_comments "
                "WHERE name=%s AND number=%s",  (
                self.post_name, self.number))
        cnx.commit()
        return True

    # Internal methods
    
    def _load_comment(self, number):
        """ Loads a comment from database if found. """
        cnx = self.env.get_db_cnx()
        cursor = cnx.cursor()
        self.env.log.debug("Fetching blog comment number %d for %r" % (
                number, self.post_name))
        cursor.execute("SELECT comment, author, time "
                "FROM fullblog_comments "
                "WHERE name=%s AND number=%s",
                (self.post_name, number))
        for row in cursor:
            self.number = number
            self.comment = row[0]
            self.author = row[1]
            self.time = to_datetime(row[2], utc)
            return True
        return False
    
    def _next_comment_number(self):
        """ Function that returns the next available comment number.
        If no blog post exists (can't attach comment), it returns 0. """
        cnx = self.env.get_db_cnx()
        cursor = cnx.cursor()
        cursor.execute("SELECT number FROM fullblog_comments "
            "WHERE name=%s", (self.post_name,))
        cmts = sorted([row[0] for row in cursor])
        if cmts:
            return cmts[-1] + 1 # Add 1 for next free
        # No item found - need to double-check to find out why
        bp = BlogPost(self.env, self.post_name)
        if bp.get_versions():
            return 1
        else:
            return 0

class BlogPost(object):
    """ Model class representing a blog post with various methods
    to do CRUD and manipulation as needed by the plugin. """
    
    # Fields of database - will be expanded into object properties
    _db_default_fields = {'name': u'',  # required
                    'version': 0, # auto
                    'title': u'', # required
                    'body': u'',  # required
                    'publish_time': datetime.datetime.now(utc),  # now
                    'version_time': datetime.datetime.now(utc),  # now
                    'version_comment': u'',
                    'version_author': u'',  # required
                    'author': u'',          # required
                    'categories': u''}
    # Other data - fetched or computed
    category_list = []
    versions = []
    
    def __init__(self, env, name, version=0):
        self.env = env
        # Expand the default values as object properties
        for prop in self._db_default_fields.keys():
            setattr(self, prop, self._db_default_fields[prop])
        self.name = name
        self._load_post(version)
        
    def save(self, version_author, version_comment=u''):
        """ Saves the post as a new version in the database.
        Returns True if saved, False if aborted for some reason.
        As this does not check for changes, the common usage is:
            if the_post.update_fields(fields_dict):
                the_post.save('the_user', 'My view on things.')
            else:
                print 'New version not saved as no changes made.' """
        if not (self.name and self.title and self.body and self.author \
                and version_author):
            self.env.log.debug("Cannot create new version of blog entry %r "
                "as name, title, body, author or version_author is missing" % (
                        self.name,) )
            return False
        version_time = to_timestamp(datetime.datetime.now(utc))
        self.versions = sorted(self.get_versions())
        version = 1
        if self.versions:
            version = self.versions[-1] + 1
        self.env.log.debug("Saving new version %d of blog post %r "
                "from author %r" % (version, self.name, version_author))
        cnx = self.env.get_db_cnx()
        cursor = cnx.cursor()
        cursor.execute("INSERT INTO fullblog_posts "
                "(name, version, title, body, publish_time, version_time, "
                "version_comment, version_author, author, categories) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                (self.name, version, self.title, self.body,
                to_timestamp(self.publish_time), version_time,
                version_comment, version_author, self.author, self.categories))
        cnx.commit()
        self._load_post(version)
        return True
    
    def update_fields(self, fields={}):
        """" Takes in a dictionary of arbitrary number of fields with
        properties as keys, and used for updating the various object properties.
        If no field values have actually changed it will return False, or
        True if one or more fields where updated. """
        changes_made = False
        for field in fields.keys():
            if not hasattr(self, field):
                continue    # skip non-existing attributes
            if field in ['name', 'version']:
                continue    # skip the database keys
            if fields[field] != getattr(self, field):
                setattr(self, field, fields[field])
                if field == 'categories':
                    # Just a convenience to see categories as a list as well
                    self.category_list = _parse_categories(fields[field])
                changes_made = True
        return changes_made
    
    def delete(self, version=0):
        """ Deletes a specific version, or if none is provided
        then all versions will be deleted. If all (or just one version exists) it
        will also delete all comments and any attachments attached to the post. """
        cnx = self.env.get_db_cnx()
        cursor = cnx.cursor()
        if version:
            cursor.execute("DELETE FROM fullblog_posts "
                    "WHERE name=%s AND version=%s",
                    (self.name, version))
        else:
            cursor.execute("DELETE FROM fullblog_posts "
                    "WHERE name=%s", (self.name,))
        cnx.commit()
        if not len(self.get_versions()):
            # Delete comments
            for comment in self.get_comments():
                comment.delete()
            # Delete attachments
            Attachment.delete_all(self.env, 'blog', self.name, cnx)
            cnx.commit()
        return True
    
    def get_versions(self):
        """ Returns a sorted list of versions stored for the blog post.
        Returns empty list ([]) if no versions exists. """
        cnx = self.env.get_db_cnx()
        cursor = cnx.cursor()
        cursor.execute("SELECT version from fullblog_posts "
                "WHERE name=%s", (self.name,) )
        self.versions = sorted([row[0] for row in cursor])
        return self.versions
        
    def get_comments(self):
        """ Returns a list of used comment numbers attached to the post.
        It instantiates BlogComment objects for comments attached to the
        current BlogPost, and returns them in a list sorted by number. """
        comments = sorted(get_blog_comments(self.env, post_name=self.name),
                    key=itemgetter(1))
        return [BlogComment(self.env, comment[0],
                        comment[1]) for comment in comments]
    
    # Internal methods

    def _load_post(self, version=0):
        """ Loads the record from the database into the object.
        Will load the most recent if none is specified.
        Also creates a Resource instance for the object. """
        self.resource = Resource('blog', self.name)
        self.versions = self.get_versions()
        if not self.versions or (version and not version in self.versions):
            # No blog post with the name exists
            return False
        version = version or self.versions[-1]
        cnx = self.env.get_db_cnx()
        cursor = cnx.cursor()
        cursor.execute("SELECT title, body, publish_time, version_time, "
                "version_comment, version_author, author, categories "
                "FROM fullblog_posts "
                "WHERE name=%s AND version=%s",
                (self.name, version) )
        for row in cursor:
            self.version = version
            self.title = row[0]
            self.body = row[1]
            self.publish_time = to_datetime(row[2], utc)
            self.version_time = to_datetime(row[3], utc)
            self.version_comment = row[4]
            self.version_author = row[5]
            self.author = row[6]
            self.categories = row[7]
            self.category_list = _parse_categories(row[7])
        return True
