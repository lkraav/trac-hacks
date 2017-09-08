# -*- coding: utf-8 -*-
#
#            Copyright (C) 2009 Massive Trac Provider Project
#
#                         All rights reserved.
#
################################################################################
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
# 
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in
#    the documentation and/or other materials provided with the
#    distribution.
# 3. The name of the author may not be used to endorse or promote
#    products derived from this software without specific prior
#    written permission.
# 
# THIS SOFTWARE IS PROVIDED BY THE AUTHOR `AS IS'' AND ANY EXPRESS
# OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE
# GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
# WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
################################################################################
# 
# This software consists of voluntary contributions made by many
# individuals. For the exact contribution history, see the revision
# history and logs, available at: https://svn.mayastudios.de/mtpp/log/
#
# Author: Sebastian Krysmanski
#
################################################################################
#
# $Revision: 262 $
# $Date: 2009-07-24 08:17:49 -0700 (Fri, 24 Jul 2009) $
# $URL: https://svn.mayastudios.de/mtpp/repos/plugins/subscriberlist/0.11/subscriberlist/web_ui.py $
#
################################################################################

from trac.core import *
from trac.config import OrderedExtensionsOption
from trac.web.api import IRequestFilter, ITemplateStreamFilter
from trac.web.chrome import add_stylesheet, ITemplateProvider

from genshi.builder import tag
from genshi.filters.transform import Transformer, StreamBuffer

from api import *

class ContentProvider(Component):
  """ Provides the files in the htdocs directory. The other components of this
      plugin depend on this component to be enabled.
  """
  implements(ITemplateProvider) 

  # ITemplateProvider methods
  
  def get_templates_dirs(self):
    return []
  
  def get_htdocs_dirs(self):
    from pkg_resources import resource_filename
    return [('subscriberlist', resource_filename(__name__, 'htdocs'))]


class SubscriberList(Component):
  """ Provides a list in the ticket view that contains all users that will be
      notified about ticket changes.
  """
  
  implements(IRequestFilter, ITemplateStreamFilter) 
  
  def __init__(self):
    self.hackergotchi_providers = None
    try:
      from hackergotchi.web_ui import HackergotchiModule
      if self.env.is_component_enabled(HackergotchiModule):
        self.hackergotchi_providers = HackergotchiModule(self.compmgr).providers
    except ImportError:
      # Ignore exception when Hackergotchi isn't installed
      pass
  
    self.notify_reporter = self.config.getbool('notification', 'always_notify_reporter')
    self.notify_owner = self.config.getbool('notification', 'always_notify_owner')
    self.notify_updater = self.config.getbool('notification', 'always_notify_updater')
  
  # IRequestFilter methods
  
  def post_process_request(self, req, template, data, content_type):
    """Do any post-processing the request might need; typically adding
    values to the template `data` dictionary, or changing template or
    mime type.
    
    `data` may be update in place.

    Always returns a tuple of (template, data, content_type), even if
    unchanged.

    Note that `template`, `data`, `content_type` will be `None` if:
     - called when processing an error page
     - the default request handler did not return any result

    (Since 0.11)
    """
    
    if template and req.path_info.startswith('/ticket/'):
      add_stylesheet(req, 'subscriberlist/list.css')
    
    return (template, data, content_type)

  def pre_process_request(self, req, handler):
    """Called after initial handler selection, and can be used to change
    the selected handler or redirect request.
    
    Always returns the request handler, even if unchanged.
    """
    return handler
    
  # ITemplateStreamFilter methods
    
  def filter_stream(self, req, method, filename, stream, data):
    """Return a filtered Genshi event stream, or the original unfiltered
    stream if no match.

    `req` is the current request object, `method` is the Genshi render
    method (xml, xhtml or text), `filename` is the filename of the template
    to be rendered, `stream` is the event stream and `data` is the data for
    the current template.

    See the Genshi documentation for more information.
    """
    if not req.path_info.startswith('/ticket/') or method != 'xhtml' or not data.has_key('ticket'):
      return stream

    ticket = data['ticket']
    
    recipients = get_recipients_for_ticket(self.env, req, self.config, ticket)
    
    div = tag.div(id='recipient-list')
    div(tag.p("This list contains all users that will be notified about changes made to this ticket.", class_='help'))
    notified_roles = Recipient.SUBSCRIBER_ROLE
    if self.notify_reporter:
      notified_roles |= Recipient.REPORTER_ROLE
    if self.notify_owner:
      notified_roles |= Recipient.OWNER_ROLE
    if self.notify_updater:
      notified_roles |= Recipient.PARTICIPANT_ROLE
    div(tag.p(tag("These roles will be notified: ", self._create_role_list(notified_roles, notified_roles)), class_='help'))
    
    user_list = tag.ul()    
    user_notified = False
    
    for recipient in recipients:
      if not recipient.is_notified:
        continue
      
      if self.hackergotchi_providers:
        # Try to find a provider
        for provider in self.hackergotchi_providers:
          if self.env.is_component_enabled(provider.__class__):
            href = provider.get_hackergotchi(req.href, recipient.id, recipient.name, recipient.mail)
            if href is not None:
              break
        else:
          href = req.href.chrome('subscriberlist/user.png')
      
        user_entry = tag.li(class_='hackergotchi', style='background-image: url(' + href + ');')
      else:
        user_entry = tag.li(class_='normal')
        
      user_entry(tag.span(recipient.name, class_='recipient-name'))
      
      if can_see_email(req, self.config, ticket.resource):
        user_entry(tag.span(tag.a(recipient.mail, href='mailto:' + recipient.mail), class_='recipient_mail'))
      
      info_span = tag.span('(', class_='recipient-info')
      info_span(self._create_role_list(recipient.role, notified_roles))
      info_span(')')
      user_entry(info_span)
      
      user_list(user_entry)
      user_notified = True
    
    if user_notified:
      div(user_list)
    else:
      div(tag.p('Nobody is currently notified about changes to this ticket.', class_='empty-list-warning'))
    
    # Insert template code
    headline = StreamBuffer()
    content = StreamBuffer()
  
    stream = stream | Transformer('//div[@id="content"]/h1[1]').cut(headline).end().\
                      buffer().select('//div[@id="content"]/*').cut(content, accumulate=True).end().buffer()

    table = tag.table(class_='subscriber-ticket-table')
    table(tag.tr(tag.td(headline, colspan=2)))
    tr = tag.tr()
    tr(tag.td(content, class_='ticket-content'))
    tr(tag.td(div, class_='subscriber-list'))
    table(tr)
    
    stream = stream | Transformer('//div[@id="content"]').attr('class', None).append(table)

    return stream
    
  def _create_role_list(self, roles, active_roles):
    role_fragment = tag()
    if (roles & Recipient.REPORTER_ROLE) != 0:
      if len(role_fragment.children) != 0:
        role_fragment.append(', ')
      role_tag = tag.span('Reporter', title='The user who created this ticket.')
      if (active_roles & Recipient.REPORTER_ROLE) != 0:
        role_tag(class_='role active-role')
      else:
        role_tag(class_='role inactive-role')
      role_fragment.append(role_tag)
    
    if (roles & Recipient.OWNER_ROLE) != 0:
      if len(role_fragment.children) != 0:
        role_fragment.append(', ')
      role_tag = tag.span('Owner', title='The user who should/will handle this ticket.')
      if (active_roles & Recipient.OWNER_ROLE) != 0:
        role_tag(class_='role active-role')
      else:
        role_tag(class_='role inactive-role')
      role_fragment.append(role_tag)
    
    if (roles & Recipient.SUBSCRIBER_ROLE) != 0:
      if len(role_fragment.children) != 0:
        role_fragment.append(', ')
      role_tag = tag.span('Subscriber', title='A user who is on the CC list.')
      if (active_roles & Recipient.SUBSCRIBER_ROLE) != 0:
        role_tag(class_='role active-role')
      else:
        role_tag(class_='role inactive-role')
      role_fragment.append(role_tag)
    
    if (roles & Recipient.PARTICIPANT_ROLE) != 0:
      if len(role_fragment.children) != 0:
        role_fragment.append(', ')
      role_tag = tag.span('Participant', title='A user who is listed in the change history of this ticket.')
      if (active_roles & Recipient.PARTICIPANT_ROLE) != 0:
        role_tag(class_='role active-role')
      else:
        role_tag(class_='role inactive-role')
      role_fragment.append(role_tag)

    if (roles & Recipient.ALWAYS_ROLE) != 0:
      if len(role_fragment.children) != 0:
        role_fragment.append(', ')
      role_tag = tag.span('Always', class_='role active-role', title='A user who is always notified about ticket changes.')
      role_fragment.append(role_tag)
      
    return role_fragment


class NotificationInfo(Component):
  """ Provides warnings when a user is not automatically notified about ticket
      changes of a ticket he/she has participated.
  """
  
  implements(ITemplateStreamFilter, IRequestFilter)
  
  ADD_CC = 'You won\'t be notified about changes made to this ticket unless '\
           'you add yourself to the Cc list.'
  ADD_CC_OWNER = 'You won\'t be notified about changes made to this ticket unless '\
                 'you add yourself to the Cc list or assign this ticket to yourself.'
  
  SPECIFY_MAIL = 'To be notified about changes to this ticket please specify your '\
                 'email address in the field below.'
  EMAIL_VISIBLE = tag(' Warning: Your email address ', tag.i('will be publicly visible.'))
  EMAIL_NOT_VISIBLE = tag(' Your email address ', tag.i('will not be visible.'))
  GRAVATAR_SUPPORTED = tag(' ', tag.a('Gravatar', href='http://gravatar.com/'), 
                           ' is supported.')

  SET_MAIL_ADDR = ('You don\'t have specified an email address in your ',
                   '. This prevents you from being notified about ticket changes.')
  INVALID_MAIL_ADDR = ('You have specified an invalid email address in your ',
                       '. This prevents you from being notified about ticket changes.')
                       

  def __init__(self):
    self.has_gravatar_support = False
    try:
      from hackergotchi.web_ui import HackergotchiModule
      from hackergotchi.providers import GravatarHackergotchiProvider
      
      if self.env.is_component_enabled(HackergotchiModule):
        for provider in HackergotchiModule(self.compmgr).providers:
          if isinstance(provider, GravatarHackergotchiProvider):
            self.has_gravatar_support = self.env.is_component_enabled(GravatarHackergotchiProvider)
            break
    except ImportError:
      # Ignore exception when Hackergotchi isn't installed
      pass

  # IRequestFilter methods
  
  def post_process_request(self, req, template, data, content_type):
    """Do any post-processing the request might need; typically adding
    values to the template `data` dictionary, or changing template or
    mime type.
    
    `data` may be update in place.

    Always returns a tuple of (template, data, content_type), even if
    unchanged.

    Note that `template`, `data`, `content_type` will be `None` if:
     - called when processing an error page
     - the default request handler did not return any result

    (Since 0.11)
    """
    
    if template and (req.path_info.startswith('/ticket/') or req.path_info.startswith('/newticket')):
      add_stylesheet(req, 'subscriberlist/warning.css')
    
    return (template, data, content_type)

  def pre_process_request(self, req, handler):
    """Called after initial handler selection, and can be used to change
    the selected handler or redirect request.
    
    Always returns the request handler, even if unchanged.
    """
    return handler
                 
  # ITemplateStreamFilter methods
    
  def filter_stream(self, req, method, filename, stream, data):
    """Return a filtered Genshi event stream, or the original unfiltered
    stream if no match.

    `req` is the current request object, `method` is the Genshi render
    method (xml, xhtml or text), `filename` is the filename of the template
    to be rendered, `stream` is the event stream and `data` is the data for
    the current template.

    See the Genshi documentation for more information.
    """
    if method != 'xhtml':
      return stream
      
    if req.path_info.startswith('/ticket/'):
      warning = self._get_warning(req, data, False)
      if warning:
        stream = stream | Transformer('//form[@id="propertyform"]/h3[1]').after(self._create_warning(warning))
    elif req.path_info.startswith('/newticket'):
      warning = self._get_warning(req, data, True)
      if warning:
        stream = stream | Transformer('//form[@id="propertyform"]').before(self._create_warning(warning))
      
    return stream
      
  def _create_warning(self, warning):
    return tag.div(warning, class_='notification-warning')
  
  def _get_warning(self, req, data, is_new_ticket):
    username = data['authname']
    is_logged_in = (username != 'anonymous')
    
    if is_logged_in:
      userinfo = get_user_info(self.env, username)
      if userinfo:
        if not userinfo[2]:
          return tag(self.SET_MAIL_ADDR[0], tag.a('preferences', href=req.href.prefs()), self.SET_MAIL_ADDR[1])
        if not EmailChecker(self.env).match_short_address(userinfo[2]):
          return tag(self.INVALID_MAIL_ADDR[0], tag.a('preferences', href=req.href.prefs()), self.INVALID_MAIL_ADDR[1])
      else:
        # This should never happen, but who knows...
        is_logged_in = False
        
    def get_anonymous_msg():
      anonymous_msg = tag(self.SPECIFY_MAIL)
      
      if self.config.getbool('trac', 'show_email_addresses'):
        anonymous_msg.append(self.EMAIL_VISIBLE)
      else:
        anonymous_msg.append(self.EMAIL_NOT_VISIBLE)
        
      if self.has_gravatar_support:
        anonymous_msg.append(self.GRAVATAR_SUPPORTED)
        
      return anonymous_msg
        
    def get_cc_msg():
      msg_suffix = ''
      if not is_logged_in:
        msg_suffix = tag(' ', get_anonymous_msg())
        
      if self.config.getbool('notification', 'always_notify_owner'):
        return tag(self.ADD_CC_OWNER, msg_suffix)
      return tag(self.ADD_CC, msg_suffix)
    
    if is_new_ticket:
      if not self.config.getbool('notification', 'always_notify_reporter'):
        return get_cc_msg()
      elif not is_logged_in:
        return get_anonymous_msg()
    else:
      if not self.config.getbool('notification', 'always_notify_updater'):
        ticket_id = data['ticket'].id
        if (not is_logged_in) or (not is_user_notified(self.config, self.env, username, ticket_id)):
          return get_cc_msg()
      elif not is_logged_in:
        return get_anonymous_msg()
      
    return None