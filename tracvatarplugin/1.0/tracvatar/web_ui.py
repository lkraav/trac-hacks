from trac.core import Component, implements
from trac.config import Option
from trac.web.chrome import ITemplateProvider, add_stylesheet
from trac.web.api import ITemplateStreamFilter
from genshi.filters.transform import Transformer
from genshi.builder import tag
import tracvatar
from pkg_resources import resource_filename
import itertools
import hashlib
import re


class AvatarModule(Component):
    implements(ITemplateStreamFilter, ITemplateProvider)

    ticket_reporter_size = Option("tracvatar", "ticket_reporter_size", default="60")
    ticket_comment_size = Option("tracvatar", "ticket_comment_size", default="40")
    ticket_comment_diff_size = Option("tracvatar", "ticket_comment_size", default="40")
    timeline_size = Option("tracvatar", "timeline_size", default="30")
    browser_lineitem_size = Option("tracvatar", "browser_lineitem_size", default="20")
    browser_changeset_size = Option("tracvatar", "browser_changeset_size", default="40")
    prefs_form_size = Option("tracvatar", "prefs_form_size", default="40")
    metanav_size = Option("tracvatar", "metanav_size", default="30")
    default = Option('tracvatar', 'avatar_default', default='default',
                            doc="The default value to pass along to avatar to "
                            "use if the email address does not match.")
    backend = Option('tracvatar', 'backend', default='gravatar',
                            doc="The name of the avatar service to use as a "
                            "backend.  Currently gravatar and libravatar "
                            "are supported.")

    # A mapping of possible backends to their peculiarities
    backends = {
        "gravatar": {
            "url": "gravatar.com",
            "base": "http://www.gravatar.com/avatar/",
            "base_ssl": "https://gravatar.com/avatar/",
        },
        "libravatar": {
            "url": "libravatar.org",
            "base": "http://cdn.libravatar.org/avatar/",
            "base_ssl": "https://seccdn.libravatar.org/avatar/",
        },
    }

    def filter_stream(self, req, method, filename, stream, data):
        filter_ = []
        author_data = {}
        context = dict(
            is_https = req.base_url.startswith("https://"),
            author_data = author_data,
            data = data
        )

        filter_.append(self._metanav(req, context))

        if req.path_info.startswith("/ticket"):
            if "action=comment-diff" in req.query_string:
                filter_.append(self._ticket_comment_diff_filter(context))
            else:
                filter_.append(self._ticket_reporter_filter(context))
                filter_.append(self._ticket_comment_filter(context))
        elif req.path_info.startswith("/timeline"):
            filter_.append(self._timeline_filter(context))
        elif req.path_info.startswith("/browser"):
            filter_.append(self._browser_filter(context))
        elif req.path_info.startswith("/log"):
            filter_.append(self._log_filter(context))
        elif req.path_info == "/prefs":
            filter_.append(self._prefs_filter(context))

        filter_.append(self._footer())

        self._lookup_email(author_data)
        for f in filter_:
            if f is not None:
                stream |= f
        add_stylesheet(req, 'tracvatar/tracvatar.css')
        return stream

    # ITemplateProvider methods
    def get_htdocs_dirs(self):
        yield 'tracvatar', resource_filename(__name__, 'htdocs')

    def get_templates_dirs(self):
        return []

    def _metanav(self, req, context):
        data = req.session

        if 'email' not in data:
            return

        email = data['email']

        return Transformer('//*/div[@id="metanav"]/ul/li[@class="first"]').append(
            self._generate_avatar(
                context,
                email,
                "metanav-avatar",
                self.metanav_size
            )
        )

    def _footer(self):
        return Transformer('//div[@id="footer"]/p[@class="left"]').append(tag.p(
            "%s support by " % self.backend.title(),
            tag.a(
                "Tracvatar %s" % tracvatar.__version__,
                href="https://bitbucket.org/zzzeek/tracvatar"),
            class_="left",
        ))

    def _generate_avatar(self, context, author, class_, size):
        author_data = context['author_data']
        email_hash = author_data.get(author, None) or self._avatar_slug(author)
        if context['is_https']:
            href = self.backends[self.backend]['base_ssl'] + email_hash
        else:
            href = self.backends[self.backend]['base'] + email_hash
        href += "?size=%s" % size
        # for some reason sizing doesn't work if you pass "default=default"
        if self.default != 'default':
            href += "&default=%s" % (self.default,)
        return tag.img(src=href, class_='tracvatar %s' % class_, width=size, height=size).generate()

    def _browser_filter(self, context):
        data, author_data = context['data'], context['author_data']
        if not data.get('dir'):
            return self._browser_changeset_filter(context)
        else:
            return self._browser_lineitem_filter(context)

    def _browser_changeset_filter(self, context):
        data, author_data = context['data'], context['author_data']
        if 'file' not in data or \
            not data['file'] or \
            'changeset' not in data['file']:
            return
        author = data['file']['changeset'].author
        author_data[author]  = None
        return lambda stream: Transformer('//table[@id="info"]//th').prepend(
            self._generate_avatar(
                    context,
                    author,
                    "browser-changeset",
                    self.browser_changeset_size)
        )(stream)

    def _prefs_filter(self, context):
        data, author_data = context['data'], context['author_data']
        if 'settings' not in data or \
            'session' not in data['settings'] or \
            'email' not in data['settings']['session']:
            email = ''
        else:
            email = data['settings']['session']['email']

        return Transformer('//form[@id="userprefs"]/table').append(
            tag.tr(
                tag.th(
                    tag.label(
                        self.backend.title() + ":",
                        for_="avatar"
                    )
                ),
                tag.td(
                    self._generate_avatar(
                         context,
                         email,
                         "prefs-avatar",
                         self.prefs_form_size
                    ),
                    " Change your avatar at ",
                    tag.a(
                        self.backends[self.backend]['url'],
                        href="http://" + self.backends[self.backend]['url'],
                    ),
                    class_="tracvatar prefs-avatar",
                ),
                class_="field"
            )
        )

    def _log_filter(self, context):
        data, author_data = context['data'], context['author_data']
        if 'changes' not in data:
            return
        for change in data['changes'].values():
            author_data[change.author] = None
        return self._browser_lineitem_render_filter(context)

    def _browser_lineitem_filter(self, context):
        data, author_data = context['data'], context['author_data']
        if 'dir' not in data or 'changes' not in data['dir']:
            return
        for trac_cset in data['dir']['changes'].values():
            author_data[trac_cset.author] = None
        return self._browser_lineitem_render_filter(context)

    def _browser_lineitem_render_filter(self, context):
        data, author_data = context['data'], context['author_data']
        def find_change(stream):
            author = stream[1][1]
            tag = self._generate_avatar(
                context,
                author,
                'browser-lineitem',
                self.browser_lineitem_size)
            return itertools.chain([stream[0]], tag, stream[1:])

        return Transformer('//td[@class="author"]').filter(find_change)

    def _ticket_reporter_filter(self, context):
        data, author_data = context['data'], context['author_data']
        if 'ticket' not in data:
            return
        author = data['ticket'].values['reporter']
        author_data[author] = None

        return lambda stream: Transformer('//div[@id="ticket"]').\
                    prepend(
                        self._generate_avatar(
                            context,
                            author,
                            'ticket-reporter',
                            self.ticket_reporter_size)
                        )(stream)

    def _ticket_comment_filter(self, context):
        data, author_data = context['data'], context['author_data']
        if 'changes' not in data:
            return

        apply_authors = []
        for change in data['changes']:
            try:
                author = change['author']
            except KeyError:
                continue
            else:
                author_data[author] = None
                apply_authors.insert(0, author)

        def find_change(stream):
            stream = iter(stream)
            author = apply_authors.pop()
            tag = self._generate_avatar(
                        context,
                        author,
                        'ticket-comment',
                        self.ticket_comment_size)
            return itertools.chain([next(stream)], tag, stream)

        return Transformer('//div[@id="changelog"]/div[@class="change"]/h3[@class="change"]').\
                        filter(find_change)

    def _ticket_comment_diff_filter(self, context):
        data, author_data = context['data'], context['author_data']

        author = data['change']['author']
        author_data[author] = None
        return lambda stream: Transformer('//dd[@class="author"]').prepend(
            self._generate_avatar(
                    context,
                    author,
                    "ticket-comment-diff",
                    self.ticket_comment_diff_size)
        )(stream)

    def _timeline_filter(self, context):
        data, author_data = context['data'], context['author_data']
        if 'events' not in data:
            return
        apply_authors = []
        for event in reversed(data['events']):
            author = event['author']
            author_data[author] = None
            apply_authors.append(author)

        def find_change(stream):
            stream = iter(stream)
            author = apply_authors.pop()
            tag = self._generate_avatar(
                        context,
                        author,
                        'timeline',
                        self.timeline_size)
            return itertools.chain(tag, stream)

        return Transformer('//div[@id="content"]/dl/dt/a/span[@class="time"]').\
                            filter(find_change)

    # from trac source
    _long_author_re = re.compile(r'.*<([^@]+)@([^@]+)>\s*|([^@]+)@([^@]+)')

    def _avatar_slug(self, email):
        if email is None:
            email = ''
        return hashlib.md5(email.lower()).hexdigest()

    def _lookup_email(self, author_data):
        author_names = [a for a in author_data if a]
        lookup_authors = sorted([a for a in author_names
                                if '@' not in a])
        email_authors = set(author_names).difference(lookup_authors)

        if lookup_authors:
            for sid, email in self.env.db_query("""
                    SELECT sid, value from SESSION_ATTRIBUTE
                    WHERE name=%%s and sid in (%s)
                    """ % ','.join(['%s'] * len(lookup_authors)),
                    ('email',) + tuple(lookup_authors)):
                author_data[sid] = self._avatar_slug(email)

        for author in email_authors:
            author_info = self._long_author_re.match(author)
            if author_info:
                if author_info.group(1):
                    name, host = author_info.group(1, 2)
                elif author_info.group(3):
                    name, host = author_info.group(3, 4)
                else:
                    continue
                author_data[name] = \
                    author_data[author] = \
                    self._avatar_slug("%s@%s" % (name, host))
