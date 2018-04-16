# -*- coding: utf-8 -*-
#
# Copyright (c) 2008-2010 by Martin Scharrer <martin@scharrer-online.de>
# All rights reserved.
#
# The i18n support was added by Steffen Hoffmann <hoff.st@web.de>.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# For a copy of the GNU General Public License see
# <http://www.gnu.org/licenses/>.

from trac.attachment import Attachment
from trac.resource import Resource
from trac.ticket.api import TicketSystem
from trac.ticket.model import Ticket
from trac.util.datefmt import format_datetime as trac_format_datetime
from trac.util.datefmt import datetime, pretty_timedelta, to_timestamp, utc
from trac.util.html import tag
from trac.util.text import to_unicode, obfuscate_email_address
from trac.web.chrome import Chrome, web_context
from trac.wiki.formatter import format_to_oneliner

from tracwatchlist.api import BasicWatchlist
from tracwatchlist.render import render_property_diff
from tracwatchlist.translation import _, N_, T_, t_, ngettext
from tracwatchlist.util import moreless, format_datetime, LC_TIME, \
    decode_range_sql


class TicketWatchlist(BasicWatchlist):
    """Watchlist entry for tickets."""
    realms = ['ticket']
    fields = {'ticket': {
        'author': T_("Author"),
        'changes': N_("Changes"),
        # TRANSLATOR: '#' stands for 'number'.
        # This is the header label for a column showing the number
        # of the latest comment.
        'commentnum': N_("Comment #"),
        'unwatch': N_("U"),
        'notify': N_("Notify"),
        'comment': T_("Comment"),
        'attachment': T_("Attachments"),
        # Plus further pairs imported at __init__.
    }}

    default_fields = {'ticket': [
        'id', 'changetime', 'author', 'changes', 'commentnum',
        'unwatch', 'notify', 'comment',
    ]}
    sort_key = {'ticket': int}

    tagsystem = None

    def __init__(self):
        labels = self.env[TicketSystem].get_ticket_field_labels()
        self.fields['ticket'].update(labels)
        self.fields['ticket']['id'] = self.get_realm_label('ticket')

        try:  # Try to support the Tags Plugin
            from tractags.api import TagSystem
        except ImportError:
            pass
        else:
            self.tagsystem = self.env[TagSystem]
            if self.tagsystem:
                self.fields['ticket']['tags'] = _("Tags")

    def get_realm_label(self, realm, n_plural=1, astitle=False):
        if astitle:
            # TRANSLATOR: 'ticket(s)' as title
            return ngettext("Ticket", "Tickets", n_plural)
        else:
            # TRANSLATOR: 'ticket(s)' inside a sentence
            return ngettext("ticket", "tickets", n_plural)

    def _get_sql(self, resids, fuzzy, var='id'):
        if isinstance(resids, basestring):
            sql = decode_range_sql(resids) % {'var': var}
            args = []
        else:
            args = resids
            if len(resids) == 1:
                sql = ' ' + var + '=%s '
            else:
                sql = ' ' + var + ' IN (' + ','.join(
                    ('%s',) * len(resids)) + ') '
        return sql, args

    def resources_exists(self, realm, resids, fuzzy=0):
        if not resids:
            return []
        sql, args = self._get_sql(resids, fuzzy)
        if not sql:
            return []
        return [unicode(v[0]) for v in self.env.db_query("""
                SELECT id FROM ticket WHERE %s
                """ % sql, args)]

    def watched_resources(self, realm, resids, user, wl, fuzzy=0):
        if not resids:
            return []
        sql, args = self._get_sql(resids, fuzzy, 'CAST(resid AS decimal)')
        if not sql:
            return []
        return [unicode(v[0]) for v in self.env.db_query("""
                SELECT resid FROM watchlist
                WHERE wluser=%%s AND realm='ticket' AND (%s)
                """ % sql, [user] + args)]

    def unwatched_resources(self, realm, resids, user, wl, fuzzy=0):
        if not resids:
            return []
        sql, args = self._get_sql(resids, fuzzy)
        if not sql:
            return []
        return [unicode(v[0]) for v in self.env.db_query("""
                SELECT id FROM ticket
                WHERE id NOT IN (
                  SELECT CAST(resid AS DECIMAL) FROM watchlist
                  WHERE wluser=%%s AND realm='ticket')
                 AND (%s)
                """ % sql, [user] + args)]

    def get_list(self, realm, wl, req, fields=None):
        context = web_context(req)
        locale = getattr(req, 'locale', None) or LC_TIME

        author = min_time = max_time = None
        min_changetime = max_changetime = None

        ticketlist = []
        extradict = {}
        if not fields:
            fields = set(self.default_fields['ticket'])
        else:
            fields = set(fields)

        if 'changetime' in fields:
            max_changetime = datetime(1970, 1, 1, tzinfo=utc)
            min_changetime = datetime.now(utc)
        if 'time' in fields:
            max_time = datetime(1970, 1, 1, tzinfo=utc)
            min_time = datetime.now(utc)

        for sid, last_visit in wl.get_watched_resources('ticket',
                                                        req.authname):
            ticketdict = {}
            try:
                ticket = Ticket(self.env, sid)
            except:
                exists = False
            else:
                exists = ticket.exists

            if not exists:
                ticketdict['deleted'] = True
                if 'id' in fields:
                    ticketdict['id'] = sid
                    ticketdict['ID'] = '#' + sid
                if 'author' in fields:
                    ticketdict['author'] = '?'
                if 'changetime' in fields:
                    ticketdict['changedsincelastvisit'] = 1
                    ticketdict['changetime'] = '?'
                    ticketdict['ichangetime'] = 0
                if 'time' in fields:
                    ticketdict['time'] = '?'
                    ticketdict['itime'] = 0
                if 'comment' in fields:
                    ticketdict['comment'] = tag.strong(t_("deleted"),
                                                       class_='deleted')
                if 'notify' in fields:
                    ticketdict['notify'] = wl.is_notify(req, 'ticket', sid)
                if 'description' in fields:
                    ticketdict['description'] = ''
                if 'owner' in fields:
                    ticketdict['owner'] = ''
                if 'reporter' in fields:
                    ticketdict['reporter'] = ''
                ticketlist.append(ticketdict)
                continue

            if not (Chrome(self.env).show_email_addresses or
                    'EMAIL_VIEW' in req.perm(ticket.resource)):
                render_elt = obfuscate_email_address
            else:
                def render_elt(x):
                    return x

            # Copy all requested fields from ticket
            if fields:
                for f in fields:
                    ticketdict[f] = ticket.values.get(f, u'')
            else:
                ticketdict = ticket.values.copy()

            changetime = ticket.time_changed
            if wl.options['attachment_changes']:
                for attachment in Attachment.select(self.env, 'ticket', sid):
                    if attachment.date > changetime:
                        changetime = attachment.date
            if 'attachment' in fields:
                attachments = []
                for attachment in Attachment.select(self.env, 'ticket', sid):
                    wikitext = u'[attachment:"' + u':'.join(
                        [attachment.filename, 'ticket',
                         sid]) + u'" ' + attachment.filename + u']'
                    attachments.extend([tag(', '),
                                        format_to_oneliner(self.env, context,
                                                           wikitext,
                                                           shorten=False)])
                if attachments:
                    attachments.reverse()
                    attachments.pop()
                ticketdict['attachment'] = moreless(attachments, 5)

            # Changes are special. Comment, commentnum and last author are
            # included in them.
            if 'changes' in fields or 'author' in fields \
                    or 'comment' in fields or 'commentnum' in fields:
                changes = []
                # If there are now changes the reporter is the last author
                author = ticket.values['reporter']
                want_changes = 'changes' in fields
                for date, cauthor, field, oldvalue, newvalue, permanent \
                        in ticket.get_changelog(changetime):
                    author = cauthor
                    if field == 'comment':
                        if 'commentnum' in fields:
                            ticketdict['commentnum'] = to_unicode(oldvalue)
                        if 'comment' in fields:
                            comment = to_unicode(newvalue)
                            comment = moreless(comment, 200)
                            ticketdict['comment'] = comment
                        if not want_changes:
                            break
                    else:
                        if want_changes:
                            label = self.fields['ticket'].get(field, u'')
                            if label:
                                changes.extend(
                                    [tag(tag.strong(label), ' ',
                                         render_property_diff(self.env, req,
                                                              ticket, field,
                                                              oldvalue,
                                                              newvalue)
                                         ), tag('; ')])
                if want_changes:
                    # Remove the last tag('; '):
                    if changes:
                        changes.pop()
                    changes = moreless(changes, 5)
                    ticketdict['changes'] = tag(changes)

            if 'id' in fields:
                ticketdict['id'] = sid
                ticketdict['ID'] = format_to_oneliner(self.env, context,
                                                      '#' + sid, shorten=True)
            if 'cc' in fields:
                if render_elt == obfuscate_email_address:
                    ticketdict['cc'] = ', '.join(
                        [render_elt(c) for c in ticketdict['cc'].split(', ')])
            if 'author' in fields:
                ticketdict['author'] = render_elt(author)
            if 'changetime' in fields:
                ichangetime = to_timestamp(changetime)
                from_ = trac_format_datetime(changetime, 'iso8601',
                                             tzinfo=req.tz)
                ticketdict.update(
                    changetime=format_datetime(changetime, locale=locale,
                                               tzinfo=req.tz),
                    ichangetime=ichangetime,
                    changedsincelastvisit=last_visit < ichangetime and 1 or 0,
                    changetime_delta=pretty_timedelta(changetime),
                    changetime_link=req.href.timeline(precision='seconds',
                                                      from_=from_))
                if changetime > max_changetime:
                    max_changetime = changetime
                if changetime < min_changetime:
                    min_changetime = changetime
            if 'time' in fields:
                time = ticket.time_created
                from_ = trac_format_datetime(time, 'iso8601', tzinfo=req.tz)
                ticketdict.update(
                    time=format_datetime(time, locale=locale, tzinfo=req.tz),
                    itime=to_timestamp(time),
                    time_delta=pretty_timedelta(time),
                    time_link=req.href.timeline(precision='seconds',
                                                from_=from_))
                if time > max_time:
                    max_time = time
                if time < min_time:
                    min_time = time
            if 'description' in fields:
                description = ticket.values['description']
                description = moreless(description, 200)
                ticketdict['description'] = description
            if 'notify' in fields:
                ticketdict['notify'] = wl.is_notify(req, 'ticket', sid)
            if 'owner' in fields:
                ticketdict['owner'] = render_elt(ticket.values['owner'])
            if 'reporter' in fields:
                ticketdict['reporter'] = render_elt(ticket.values['reporter'])
            if 'tags' in fields and self.tagsystem:
                tags = []
                for t in self.tagsystem.get_tags(req,
                                                 Resource('ticket', sid)):
                    tags.extend(
                        [tag.a(t, href=req.href('tags', q=t)), tag(', ')])
                if tags:
                    tags.pop()
                ticketdict['tags'] = moreless(tags, 10)

            ticketlist.append(ticketdict)

        if 'changetime' in fields:
            extradict['max_changetime'] = format_datetime(max_changetime,
                                                          locale=locale,
                                                          tzinfo=req.tz)
            extradict['min_changetime'] = format_datetime(min_changetime,
                                                          locale=locale,
                                                          tzinfo=req.tz)
        if 'time' in fields:
            extradict['max_time'] = format_datetime(max_time, locale=locale,
                                                    tzinfo=req.tz)
            extradict['min_time'] = format_datetime(min_time, locale=locale,
                                                    tzinfo=req.tz)

        return ticketlist, extradict


_EXTRA_STRINGS = [_("%(value)s added")]
