# -*- coding: utf8 -*-

from tracdiscussion.api import *
from tracdiscussion.core import *
from trac.core import *
from trac.wiki import IWikiSyntaxProvider, IWikiMacroProvider
from trac.web.main import IRequestHandler, IRequestFilter
from trac.web.chrome import Chrome, add_stylesheet
from trac.util import format_datetime
from trac.util.html import html
import time, re

view_topic_doc = """Displays content of discussion topic. If no argument passed
tries to find topic with same name as name of current wiki page. If topic name
passed displays that topic. """

class DiscussionWiki(Component):
    """
        The wiki module implements macros for forums, topics and messages
        referencing.
    """
    implements(IWikiSyntaxProvider, IWikiMacroProvider, IRequestFilter)

    # IWikiSyntaxProvider methods
    def get_link_resolvers(self):
        yield ('forum', self._discussion_link)
        yield ('topic', self._discussion_link)
        yield ('message', self._discussion_link)

    def get_wiki_syntax(self):
        return []

    # IWikiMacroProvider methods
    def get_macros(self):
        yield 'ViewTopic'

    def get_macro_description(self, name):
        if name == 'ViewTopic':
            return view_topic_doc
        else:
            return ""

    def expand_macro(self, formatter, name, content):
        if name == 'ViewTopic':
            self.log.debug("Rendering ViewTopic macro...")

            # Determine topic subject
            page_name = formatter.req.path_info[6:] or 'WikiStart'
            subject = content or page_name

            # Create request context.
            context = formatter.context('discussion-wiki')
            context.cursor = context.db.cursor()

            # Get API object.
            api = self.env[DiscussionApi]

            # Get topic by subject
            topic = api.get_topic_by_subject(context, subject)
            self.log.debug('subject: %s' % (subject,))
            self.log.debug('topic: %s' % (topic,))

            # Prepare request object.
            if topic:
                formatter.req.args['forum'] = topic['forum']
                formatter.req.args['topic'] = topic['id']

            # Process discussion request.
            template, data = api.process_discussion(context)

            if context.req.args.get('body') == '':
               context.req.args['body'] = ' '

            # Return rendered template.
            data['discussion']['mode'] = 'message-list'
            data['discussion']['page_name'] = page_name
            return Chrome(self.env).render_template(formatter.req, template,
              data, 'text/html', True)
        else:
            raise TracError('Not implemented macro %s' % (name))

    # IRequestFilter methods
    def pre_process_request(self, req, handler):
        # Change method from POST to GET.
        match = re.match(r'^/wiki(?:/(.*))?', req.path_info)
        action = req.args.get('discussion_action')
        if match and action and req.method == 'POST':
            req.environ['REQUEST_METHOD'] = 'GET'

        # Continue processing request.
        return handler

    def post_process_request(self, req, template, content_type):
        return (template, content_type)

    # Core code methods
    def _discussion_link(self, formatter, ns, params, label):
        id = params

        db = self.env.get_db_cnx()
        cursor = db.cursor()
        if ns == 'forum':
            columns = ('subject',)
            sql = "SELECT f.subject FROM forum f WHERE f.id = %s"
            self.log.debug(sql % (id,))
            cursor.execute(sql, (id,))
            for row in cursor:
                row = dict(zip(columns, row))
                return html.a(label, href = formatter.href.discussion(id),
                  title = row['subject'])
            return html.a(label, href = '%s/%s' % (formatter.href.discussion(),
              id), title = label, class_ = 'missing')
        elif ns == 'topic':
            columns = ('forum', 'forum_subject', 'subject')
            sql = "SELECT t.forum, f.subject, t.subject FROM topic t LEFT" \
              " JOIN forum f ON t.forum = f.id WHERE t.id = %s"
            self.log.debug(sql % (id,))
            cursor.execute(sql, (id,))
            for row in cursor:
                row = dict(zip(columns, row))
                return html.a(label, href = '%s#-1' % \
                  (formatter.href.discussion(row['forum'], id),), title =
                  '%s: %s' % (row['forum_subject'], row['subject']))
            return html.a(label, href = '%s/%s' % (formatter.href.discussion(),
              id), title = label, class_ = 'missing')
        elif ns == 'message':
            columns = ('forum', 'topic', 'forum_subject', 'subject')
            sql = "SELECT m.forum, m.topic, f.subject, t.subject FROM" \
              " message m, (SELECT subject, id FROM forum) f," \
              " (SELECT subject, id FROM topic) t WHERE" \
              " m.forum = f.id AND m.topic = t.id AND m.id = %s"
            self.log.debug(sql % (id,))
            cursor.execute(sql, (id,))
            for row in cursor:
                row = dict(zip(columns, row))
                return html.a(label, href = '%s#%s' % \
                  (formatter.href.discussion(row['forum'], row['topic'], id),
                  id), title = '%s: %s' % (row['forum_subject'],
                  row['subject']))
            return html.a(label, href = '%s/%s' % (formatter.href.discussion(),
              id), title = label, class_ = 'missing')
        else:
            return html.a(label, href = '%s/%s' % (formatter.href.discussion(),
              id), title = label, class_ = 'missing')
