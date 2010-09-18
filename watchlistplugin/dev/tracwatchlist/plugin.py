# -*- coding: utf-8 -*-
"""
 Watchlist Plugin for Trac
 Copyright (c) 2008-2009  Martin Scharrer <martin@scharrer-online.de>
 This is Free Software under the BSD license.

 This program is free software: you can redistribute it and/or modify
 it under the terms of the GNU General Public License as published by
 the Free Software Foundation, either version 3 of the License, or
 (at your option) any later version.

 This program is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 GNU General Public License for more details.

 You should have received a copy of the GNU General Public License
 along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

__url__      = ur"$URL$"[6:-2]
__author__   = ur"$Author$"[9:-2]
__revision__ = int("0" + ur"$Rev$"[6:-2].strip('M'))
__date__     = ur"$Date$"[7:-2]

from  pkg_resources          import  resource_filename
from  urllib                 import  quote_plus

from  genshi.builder         import  tag, Markup
from  trac.config            import  BoolOption, ListOption
from  trac.core              import  *
from  trac.db                import  Table, Column, Index, DatabaseManager
from  trac.ticket.model      import  Ticket
#from  trac.ticket.web_ui     import  TicketModule
from  trac.ticket.api        import  TicketSystem
from  trac.util.datefmt      import  pretty_timedelta, to_datetime, \
                                     datetime, utc, to_timestamp
from  trac.util.text         import  to_unicode
from  trac.web.api           import  IRequestFilter, IRequestHandler, \
                                     RequestDone, HTTPNotFound, HTTPBadRequest
from  trac.web.chrome        import  ITemplateProvider, add_ctxtnav, \
                                     add_link, add_script, add_notice, \
                                     Chrome
from  trac.util.text         import  obfuscate_email_address
from  trac.web.href          import  Href
from  trac.wiki.model        import  WikiPage
from  trac.wiki.formatter    import  format_to_oneliner
from  trac.mimeview.api      import  Context

from  tracwatchlist.api      import  BasicWatchlist, IWatchlistProvider
from  tracwatchlist.translation import  add_domain, _, N_, T_, t_, tag_, gettext, ngettext
from  tracwatchlist.render   import  render_property_diff
from  tracwatchlist.util     import  moreless, ensure_string, format_datetime,\
                                     current_timestamp


class WatchlistPlugin(Component):
    """Main class of the Trac WatchlistPlugin.

    Displays watchlist for wiki pages, ticket and possible other Trac realms.

    For documentation see http://trac-hacks.org/wiki/WatchlistPlugin.
    """
    providers = ExtensionPoint(IWatchlistProvider)

    implements( IRequestHandler, IRequestFilter, ITemplateProvider )

    OPTIONS = {
        'notifications': ( False, N_("Notifications")),
        'display_notify_navitems': ( False, N_("Display notification navigation items")),
        'display_notify_column': ( True, N_("Display notification column in watchlist tables")),
        'notify_by_default': ( False, N_("Enable notifications by default for all watchlist entries")),
        'stay_at_resource': ( False, N_("The user stays at the resource after a watch/unwatch operation and the watchlist page is not displayed")),
        'stay_at_resource_notify': ( True, N_("The user stays at the resource after a notify/do-not-notify operation and the watchlist page is not displayed")),
        'show_messages_on_resource_page': ( True, N_("Action messages are shown on resource pages")),
        'show_messages_on_watchlist_page': ( True, N_("Action messages are shown when going to the watchlist page")),
        'show_messages_while_on_watchlist_page': ( True, N_("Show action messages while on watchlist page")),
        'autocomplete_inputs': ( True, N_("Autocomplete input fields (add/remove resources)")),
        'dynamic_tables': ( True, N_("Dynamic watchlist tables")),
        'individual_column_filtering': ( True, N_("Individual column filtering")),
    }

    global_options = [ BoolOption('watchlist',name,data[0],doc=data[1]) for (name,data) in OPTIONS.iteritems() ]
    realm_order = ListOption('watchlist','display_sections', 'wiki,ticket',
            doc=N_("Display only the given watchlist sections in the given order"))

    wsub = None


    def __init__(self):
        # bind the 'watchlist' catalog to the specified locale directory
        locale_dir = resource_filename(__name__, 'locale')
        add_domain(self.env.path, locale_dir)

        #
        self.realms = []
        self.realm_handler = {}
        for provider in self.providers:
            for realm in provider.get_realms():
                assert realm not in self.realms
                self.realms.append(realm)
                self.realm_handler[realm] = provider

        try:
            # Import methods from WatchSubscriber of the AnnouncerPlugin
            from  announcerplugin.subscribers.watchers  import  WatchSubscriber
            self.wsub = self.env[WatchSubscriber]
            if self.wsub:
                self.log.debug("WS: WatchSubscriber found in announcerplugin")
        except Exception, e:
            try:
                # Import fallback methods for AnnouncerPlugin's dev version
                from  announcer.subscribers.watchers  import  WatchSubscriber
                self.wsub = self.env[WatchSubscriber]
                if self.wsub:
                    self.log.debug("WS: WatchSubscriber found in announcer")
            except Exception, ee:
                self.log.debug("WS! " + str(e))
                self.log.debug("WS! " + str(ee))
                self.wsub = None


    ## User settings ########################################################
    def get_settings(self, user):
        settings = {}
        settings['useroptions'] = dict([
            ( name,self.config.getbool('watchlist',name) ) for name in self.OPTIONS.keys() ])
        usersettings = self._get_user_settings(user)
        if 'useroptions' in usersettings:
            settings['useroptions'].update( usersettings['useroptions'] )
            del usersettings['useroptions']
        settings.update( usersettings )
        return settings


    def _delete_user_settings(self, user):
        """Deletes all user settings in 'watchlist_settings' table.
           This can be done to reset all settings to the default values
           and to resolve possible errors with wrongly stored settings.
           This can happen while using the develop version of this plugin."""
        db = self.env.get_db_cnx()
        cursor = db.cursor()

        cursor.execute("""
          DELETE
            FROM watchlist_settings
           WHERE wluser=%s
        """, (user,))
        db.commit()
        return


    def _save_user_settings(self, user, settings):
        """Saves user settings in 'watchlist_settings' table.
           Only saving of all user settings is supported at the moment."""
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        options = settings['useroptions']

        settingsstr = "&".join([ "=".join([k,unicode(v)])
                            for k,v in options.iteritems()])

        cursor.execute("""
          DELETE
            FROM watchlist_settings
           WHERE wluser=%s
        """, (user,))

        cursor.execute("""
          INSERT
            INTO watchlist_settings (wluser,name,type,settings)
          VALUES (%s,'useroptions','ListOfBool',%s)
          """, (user, settingsstr) )

        cursor.executemany("""
          INSERT
            INTO watchlist_settings (wluser,name,type,settings)
          VALUES (%s,%s,'ListOfStrings',%s)
          """, [(user, realm + '_fields', settings[realm + '_fields'])
                for realm in self.realms if realm + '_fields' in settings ] )

        db.commit()
        return True


    def _get_user_settings(self, user):
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute("""
          SELECT name,type,settings
            FROM watchlist_settings
           WHERE wluser=%s
        """, (user,))

        settings = dict()
        for name,type,settingsstr in cursor.fetchall():
            if type == 'ListOfBool':
                settings[name] = dict([
                    (k,v=='True') for k,v in
                        [ kv.split('=') for kv in settingsstr.split("&") ] ])
            elif type == 'ListOfStrings':
                settings[name] = filter(None,settingsstr.split(','))
            else:
                settings[name] = settingsstr
        return settings


    ## Change/access watch status ###########################################
    def has_watchlist(self, user):
        """Checks if user has a non-empty watchlist."""
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute("""
          SELECT count(*)
            FROM watchlist
           WHERE wluser=%s;
        """, (user,)
        )
        count = cursor.fetchone()
        if not count or not count[0]:
            return False
        else:
            return True


    def get_watched_resources(self, realm, user, db=None):
        """Returns list of resources watched by the given user in the given realm.
           The list contains a list with the resource id and the last time it
           got visited."""
        if not db:
            db = self.env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute("""
        SELECT resid,lastvisit
            FROM watchlist
        WHERE realm=%s AND wluser=%s
        """, (realm, user)
        )
        return cursor.fetchall()



    def is_watching(self, realm, resid, user):
        """Checks if user watches the given resource(s).
           Returns True/False for a single resource or
           a list of watched resources."""
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        if getattr(resid, '__iter__', False):
            reses = list(resid)
            cursor.execute("""
                SELECT resid
                FROM watchlist
                WHERE wluser=%s AND realm=%s AND
                        resid IN (
            """ + ",".join(("%s",) * len(reses)) + ")",
            [user,realm] + reses)
            return [ res[0] for res in cursor.fetchall() ]
        else:
            cursor.execute("""
                SELECT count(*)
                  FROM watchlist
                 WHERE realm=%s AND resid=%s AND wluser=%s;
            """, (realm, to_unicode(resid), user)
            )
            count = cursor.fetchone()
            if not count or not count[0]:
                return False
            else:
                return True


    def visiting(self, realm, resid, user, db=None):
        """Marks the given resource as visited just now."""
        db = db or self.env.get_db_cnx()
        cursor = db.cursor()
        now = current_timestamp()
        cursor.log = self.log
        cursor.execute("""
          UPDATE watchlist
             SET lastvisit=%s
           WHERE realm=%s AND resid=%s AND wluser=%s;
        """, (now, realm, to_unicode(resid), user)
        )
        db.commit()
        return


    ## Change/access notification status ####################################
    def is_notify(self, req, realm, resid):
        try:
            return self.wsub.is_watching(req.session.sid, True, realm, resid)
        except AttributeError:
            return False
        except Exception, e:
            self.log.error("is_notify error: " + str(e))
            return False


    def set_notify(self, req, realm, resid):
        try:
            self.wsub.set_watch(req.session.sid, True, realm, resid)
        except AttributeError:
            return False
        except Exception, e:
            self.log.error("set_notify error: " + str(e))


    def unset_notify(self, req, realm, resid):
        try:
            self.wsub.set_unwatch(req.session.sid, True, realm, resid)
        except AttributeError:
            return False
        except Exception, e:
            self.log.error("unset_notify error: " + str(e))


    ## Methods for IRequestHandler ##########################################
    def match_request(self, req):
        return req.path_info.startswith("/watchlist")


    def process_request(self, req):
        """Processes requests to the '/watchlist' path."""
        user  = to_unicode( req.authname )

        # Reject anonymous users
        if not user or user == 'anonymous':
            # TRANSLATOR: Link part of
            # "Please %(log_in)s to view or change your watchlist"
            log_in=tag.a(_("log in"), href=req.href('login'))
            if tag_ == None:
                # For Trac 0.11
                raise HTTPNotFound(
                        tag("Please ", log_in, " to view or change your watchlist"))
            else:
                # For Trac 0.12
                raise HTTPNotFound(
                        tag_("Please %(log_in)s to view or change your watchlist",
                            log_in=log_in))

        # Get and format request arguments
        realm = to_unicode( req.args.get('realm', u'') )
        resid = ensure_string( req.args.get('resid', u'') )
        action = req.args.get('action','view')
        async = req.args.get('async', 'false') == 'true'

        # Handle AJAX search early to speed up things
        if action == "search":
            """AJAX search request. At the moment only used to get list
               of all not watched resources."""
            handler = self.realm_handler[realm]
            query = to_unicode( req.args.get('q', u'') ).strip()
            if not query:
                req.send('', 'text/plain', 200 )
            found = set(handler.resources_exists(realm, query + '*'))
            if not found:
                req.send('', 'text/plain', 200 )
            watched = set(self.get_watched_resources( realm, user ))
            notwatched = list(found.difference(watched))
            try:
                notwatched.sort(cmp=handler.get_sort_cmp(realm),
                                key=handler.get_sort_key(realm))
            except TypeError:
                # Ignore conversion errors in `key` function.
                # They will still abort the sorting.
                pass
            req.send( unicode(u'\n'.join(notwatched) + u'\n').encode("utf-8"),
                'text/plain', 200 )

        # DB cursor
        db = self.env.get_db_cnx()
        cursor = db.cursor()

        wldict = req.args.copy()
        wldict['action'] = action

        onwatchlistpage = req.environ.get('HTTP_REFERER','').find(
                          req.href.watchlist()) != -1

        settings = self.get_settings( user )
        options = settings['useroptions']
        # Needed here to get updated settings
        if action == "save":
            newoptions = req.args.get('options',[])
            for k in settings['useroptions'].keys():
                settings['useroptions'][k] = k in newoptions
            for realm in self.realms:
                settings[realm + '_fields'] = req.args.get(realm + '_fields', tuple())
            self._save_user_settings(req.authname, settings)

            # Clear session cache for nav items
            try:
                # Clear session cache for nav items, so that the post processor
                # rereads the settings
                del req.session['watchlist_display_notify_navitems']
            except:
                pass
            req.redirect(req.href('watchlist'))
        elif action == "defaultsettings":
            # Only execute if sent using the watchlist preferences form
            if onwatchlistpage and req.method == 'POST':
                self._delete_user_settings(req.authname)
            req.redirect(req.href('watchlist'))

        redirectback_notify = options['stay_at_resource_notify'] and not \
                              onwatchlistpage and not async
        if action == "notifyon":
            if not self.res_exists(realm, resid):
                raise HTTPNotFound(t_("Page %(name)s not found", name=resid))
            elif self.wsub and options['notifications']:
                self.set_notify(req, realm, resid)
                db.commit()
            if redirectback_notify:
                if options['show_messages_on_resource_page']:
                    req.session['watchlist_notify_message'] = _(
                      """
                      You are now receiving change notifications
                      about this resource.
                      """
                    )
                req.redirect(req.href(realm,resids[0]))
            if async:
                req.send("",'text/plain', 200)
            else:
                req.redirect(req.href('watchlist'))
        elif action == "notifyoff":
            if self.wsub and options['notifications']:
                self.unset_notify(req, realm, resid)
                db.commit()
            if redirectback_notify:
                if options['show_messages_on_resource_page']:
                    req.session['watchlist_notify_message'] = _(
                      """
                      You are no longer receiving
                      change notifications about this resource.
                      """
                    )
                req.redirect(req.href(realm,resids[0]))
                raise RequestDone
            if async:
                req.send("",'text/plain', 200)
            else:
                req.redirect(req.href('watchlist'))

        new_res = []
        del_res = []
        alw_res = []
        err_res = []
        err_pat = []
        redirectback = options['stay_at_resource'] and not onwatchlistpage
        if action == "watch":
            handler = self.realm_handler[realm]
            reses = set(handler.resources_exists(realm, resid))
            alw_res = set(self.is_watching(realm, reses, user))
            new_res.extend(reses.difference(alw_res))
            err_res.extend(reses.intersection(alw_res))

            if new_res:
                cursor.executemany("""
                  INSERT
                    INTO watchlist (wluser, realm, resid, lastvisit)
                  VALUES (%s,%s,%s,0)
                """, [(user, realm, res) for res in new_res]
                )
                db.commit()

            if options['show_messages_on_resource_page'] and not onwatchlistpage and redirectback:
                req.session['watchlist_message'] = _(
                  "You are now watching this resource."
                )
            if self.wsub and options['notifications'] and options['notify_by_default']:
                for res in new_res:
                    self.set_notify(req, realm, res)
                db.commit()
            if redirectback and len(new_res) == 1:
                req.redirect(req.href(realm,new_res[0]))
            action = 'view'

        elif action == "unwatch":
            handler = self.realm_handler[realm]
            reses = set(handler.resources_exists(realm, resid))
            alw_res = set(self.is_watching(realm, reses, user))
            del_res.extend(alw_res.intersection(reses))
            err_res.extend(reses.difference(alw_res))

            sql = ("""
                DELETE
                FROM watchlist
                WHERE wluser=%s AND realm=%s AND
                        resid IN (
            """ + ",".join(("%s",) * len(del_res)) + ")"
            )
            cursor.execute( sql, [user,realm] + del_res)
            db.commit()
            # Unset notification
            if self.wsub and options['notifications'] and options['notify_by_default']:
                for res in del_res:
                    self.unset_notify(req, realm, res)
                db.commit()
            # Send an empty response for asynchronous requests
            if async:
                req.send("",'text/plain', 200)
            # Redirect back to resource if so configured:
            if redirectback and len(del_res) == 1:
                if options['show_messages_on_resource_page']:
                    req.session['watchlist_message'] = _(
                    "You are no longer watching this resource."
                    )
                req.redirect(req.href(realm,del_res[0]))
            action = 'view'

        # Up to here all watchlist actions except 'view' got handled and
        # either redirected the request or set the action to 'view'.
        if action != "view":
            raise HTTPBadRequest(_("Invalid watchlist action '%(action)s'!", action=action))
        # Display watchlist page:

        wldict['del_res'] = sorted(del_res)
        wldict['err_res'] = sorted(err_res)
        wldict['err_pat'] = sorted(err_pat)
        wldict['new_res'] = sorted(new_res)
        wldict['alw_res'] = sorted(alw_res)

        if onwatchlistpage:
            wldict['show_messages'] = options['show_messages_while_on_watchlist_page']
        else:
            wldict['show_messages'] = options['show_messages_on_watchlist_page']

        wldict['perm']   = req.perm
        wldict['realms'] = [ r for r in self.realm_order if r in self.realms ]
        wldict['notifications'] = bool(self.wsub and options['notifications'] and options['display_notify_column'])
        wldict['OPTIONS'] = self.OPTIONS
        wldict['options'] = options
        wldict['wlgettext'] = gettext
        wldict['t_'] = t_
        def get_label(realm, n_plural=1):
            return self.realm_handler[realm].get_realm_label(realm, n_plural)
        wldict['get_label'] = get_label

        wldict['available_fields'] = {}
        wldict['default_fields'] = {}
        for r in self.realms:
            wldict['available_fields'][r],wldict['default_fields'][r] = self.realm_handler[r].get_fields(r)
        wldict['active_fields'] = {}
        for r in self.realms:
            cols = settings.get(r + '_fields',[])
            if not cols:
                cols = wldict['default_fields'].get(r,[])
            wldict['active_fields'][r] = cols

        for xrealm in wldict['realms']:
            xhandler = self.realm_handler[xrealm]
            if xhandler.has_perm(xrealm, req.perm):
                wldict[xrealm + 'list'] = xhandler.get_list(xrealm, self, req, wldict['active_fields'][xrealm])
                name = xhandler.get_realm_label(xrealm, n_plural=1000)
                # TRANSLATOR: Navigation link to point to watchlist section of this realm
                # (e.g. 'Wikis', 'Tickets').
                add_ctxtnav(req, _("Watched %(realm_plural)s", realm_plural=name),
                            href='#' + xrealm + 's')
        add_ctxtnav(req, t_("Preferences"), href='#preferences')
        return ("watchlist.html", wldict, "text/html")


    ## Methods for IRequestFilter ###########################################
    def pre_process_request(self, req, handler):
        return handler


    def post_process_request(self, req, template, data, content_type):
        """Executed after EVERY request is processed.
           Used to add navigation bars, display messages
           and to note visits to watched resources."""
        user = to_unicode( req.authname )
        if not user or user == "anonymous":
            return (template, data, content_type)

        # Extract realm and resid from path:
        parts = req.path_info[1:].split('/',1)

        try:
            realm, resid = parts[:2]
        except:
            # Handle special case for '/' and '/wiki'
            if parts[0] == 'wiki' or (parts[0] == '' and
               'WikiModule' == self.env.config.get('trac','default_handler') ):
                realm, resid = 'wiki', 'WikiStart'
            else:
                realm, resid = parts[0], ''

        if realm not in self.realms or not \
                self.realm_handler[realm].has_perm(realm, req.perm):
            return (template, data, content_type)

        notify = 'False'
        # The notification setting is stored in the session to avoid rereading
        # the whole user settings for every page displayed
        try:
            notify = req.session['watchlist_display_notify_navitems']
        except KeyError:
            settings = self.get_settings(user)
            options = settings['useroptions']
            notify = (self.wsub and options['notifications']
                  and options['display_notify_navitems']) and 'True' or 'False'
            req.session['watchlist_display_notify_navitems'] = notify

        try:
            add_notice(req, req.session['watchlist_message'])
            del req.session['watchlist_message']
        except KeyError:
            pass
        try:
            add_notice(req, req.session['watchlist_notify_message'])
            del req.session['watchlist_notify_message']
        except KeyError:
            pass

        href = Href(req.base_path)
        if self.is_watching(realm, resid, user):
            add_ctxtnav(req, _("Unwatch"),
                href=req.href('watchlist', action='unwatch',
                    resid=resid, realm=realm),
                title=_("Remove %(document)s from watchlist",
                    document=realm))
            self.visiting(realm, resid, user)
        else:
            add_ctxtnav(req, _("Watch"),
                href=req.href('watchlist', action='watch',
                resid=resid, realm=realm),
                title=_("Add %(document)s to watchlist", document=realm))
        if notify == 'True':
            if self.is_notify(req, realm, resid):
                add_ctxtnav(req, _("Do not Notify me"),
                    href=req.href('watchlist', action='notifyoff',
                        resid=resid, realm=realm),
                    title=_("Do not notify me if %(document)s changes",
                        document=realm))
            else:
                add_ctxtnav(req, _("Notify me"),
                    href=req.href('watchlist', action='notifyon',
                        resid=resid, realm=realm),
                    title=_("Notify me if %(document)s changes",
                        document=realm))

        return (template, data, content_type)


    def res_exists(self, realm, resid):
        return self.realm_handler[realm].res_exists(realm, resid)


    ## Methods for ITemplateProvider ########################################
    def get_htdocs_dirs(self):
        return [('watchlist', resource_filename(__name__, 'htdocs'))]


    def get_templates_dirs(self):
        return [ resource_filename(__name__, 'templates') ]

# EOF
