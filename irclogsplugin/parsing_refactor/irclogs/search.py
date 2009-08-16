from datetime import datetime
from os import path
from pytz import timezone, UTC
from time import strftime, strptime, gmtime, mktime
import os
import sys

from trac.util.datefmt import localtz
from trac.core import *
from trac.search import ISearchSource
from trac.config import Option, IntOption

import web_ui
from api import IIRCLogIndexer, IRCChannelManager

whoosh_loaded = False
try:
    from whoosh.filedb.filestore import FileStorage
    from whoosh.fields import Schema, TEXT, STORED
    from whoosh.qparser import QueryParser
    from whoosh import index
    whoosh_loaded = True
except Exception, e:
    sys.__stderr__.write("WARNING: Failed to load whoosh library.  Whoosh index disabled")
    sys.__stderr__.write(e.message)

if whoosh_loaded:
    class WhooshIrcLogsIndex(Component):
        implements(ISearchSource)
        implements(IIRCLogIndexer)

        TIMESTAMP_FORMAT = '%Y%m%d%H%M%S'
        SCHEMA = Schema(channel=STORED, timestamp=STORED, content=TEXT(stored=True))
        PARSER = QueryParser("content", schema=SCHEMA)

        indexpath = Option('irclogs', 'search_db_path', 'irclogs-index',
                doc="Location of irclogs whoosh index")
        last_index = IntOption('irclogs', 'last_index', 239414400,
                doc="Epoch of last index.  Aug 7th, 1977 GMT by default.")

        # Start ISearchSource impl
        def get_search_filters(self, req):
            if not req.perm.has_permission('IRCLOGS_VIEW'):
                return []
            return [('irclogs', 'IRC Logs', True)]


        def get_search_results(self, req, terms, filters):
            usertz = timezone('utc')
            logtz = timezone('utc')

            if not 'irclogs' in filters:
                return
            
            #logview = web_ui.IrcLogsView(self.env)
            chmgr = IRCChannelManager(self.env)
            for result in self.search(terms, tz=logtz):
                dt = None
                dt_str = ''
                if result.get('timestamp'):
                    dt = chmgr.to_user_tz(req, result['timestamp'])
                    d_str = "%04d/%02d/%02d"%(
                        dt.year,
                        dt.month,
                        dt.day,
                    )
                    t_str = "%02d:%02d:%02d"%(
                        dt.hour,
                        dt.minute,
                        dt.second
                    )
                channel = ''
                if result.get('channel'):
                    channel = '%s/'%result['channel']

                url = '/irclogs/%s%s'%(channel, d_str)
                yield "%s#%s"%(req.href(url), t_str), 'irclogs for %s'%result['channel'], dt, 'irclog',\
                    result['content']
        # End ISearchSource impl

        def update_index(self):
            last_index_dt = datetime(*gmtime(self.last_index)[:6]).\
                replace(tzinfo=UTC)
            now = datetime.utcnow().replace(tzinfo=UTC)
            idx = self.get_index()
            writer = idx.writer()
            try:
                chmgr = IRCChannelManager(self.env)
                for channel_name in chmgr.get_channel_names():
                    channel = chmgr.get_channel_by_name(channel_name)
                    provider = chmgr.get_provider(channel)
                    ls = provider.get_events_in_range(channel['name'], last_index_dt, now)
                    for line in ls:
                        if line['type'] == 'comment': 
                            content = "<%s> %s"%(line['nick'], line['comment'])
                            writer.add_document(
                                channel=channel['name'],
                                timestamp=line['timestamp'].strftime(self.TIMESTAMP_FORMAT),
                                content=content
                            )
                        if line['type'] == 'action':
                            content = "* %s %s"%(line['nick'], line['action'])
                            writer.add_document(
                                channel=channel['name'],
                                timestamp=line['timestamp'].strftime(self.TIMESTAMP_FORMAT),
                                content=content
                            )
                writer.commit()
                epoch_now = int(mktime(now.timetuple()))
                self.config['irclogs'].set('last_index', epoch_now)
                self.config.save()
            except Exception, e:
                writer.cancel()
                raise e

        def get_index(self):
            ip = self.indexpath
            if not self.indexpath.startswith('/'):
                ip = path.join(self.env.path, ip)
            if not path.exists(ip):
                os.mkdir(ip)
            if not index.exists_in(ip):
                index.create_in(ip, self.SCHEMA)
            return index.open_dir(ip)

        def index_lines(self, lines, channel):
            ix = self.get_index()
            writer = ix.writer()
            for line in lines:
                ts = line.get('timestamp')
                if ts:
                    ts = ts.strftime(self.TIMESTAMP_FORMAT)
                ch = channel['name']
                c = line['content']
                writer.add_document(channel=ch, timestamp=ts, content=c)
            writer.commit()

        def search(self, terms, tz='utc'):
            if isinstance(tz, str):
                tz = timezone(tz)
            ix = self.get_index()
            searcher = ix.searcher()
            parsed_terms = self.PARSER.parse(' or '.join(terms))
            if terms:
                for f in searcher.search(parsed_terms):
                    timestamp = strptime(f['timestamp'], self.TIMESTAMP_FORMAT)
                    dt = datetime(*timestamp[:6]).replace(tzinfo=tz)
                    f['timestamp'] = dt
                    yield f
