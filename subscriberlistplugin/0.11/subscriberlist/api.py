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
# $Revision: 271 $
# $Date: 2009-07-25 02:12:36 -0700 (Sat, 25 Jul 2009) $
# $URL: https://svn.mayastudios.de/mtpp/repos/plugins/subscriberlist/0.11/subscriberlist/api.py $
#
################################################################################

import re

from trac.core import *
from trac.notification import EMAIL_LOOKALIKE_PATTERN
from trac.util.text import obfuscate_email_address

def get_user_info(env, user):
  """ Returns the info for the given user as tupel:
      
        (username, name, email)
        
      or "None" if the user couldn't be found. The user can be specified either
      as username or as email address (where the latter may not be unambiguously
      when there are more than one user with the same email address)-
  """
  
  # IMPORTANT: We can't cache the results here as the cache may live longer than
  #   the current request (for example when tracd is used). We always have to 
  #   obtain the user information from "env.get_known_users()" as they unlikely
  #   stay the same over the lifetime of the server Trac runs on.
  #   This is, however, no big deal when looking at the performance.
  for username, name, email in env.get_known_users(env.get_db_cnx()):
    if user.find('@') != -1:
      if user == email:
        return (username, name, email)
    else:
      if user == username:
        return (username, name, email)
    
  return None
  
def can_see_email(req, config, resource):
  return config.getbool('trac', 'show_email_addresses') or 'EMAIL_VIEW' in req.perm(resource)

def get_recipients_for_ticket(env, req, config, ticket):
  #
  # This code is partially taken from: 
  #
  #  trac.ticket.notification.TicketNotifyEmail.get_recipients()
  # 
  notify_reporter = config.getbool('notification', 'always_notify_reporter')
  notify_owner = config.getbool('notification', 'always_notify_owner')
  notify_updater = config.getbool('notification', 'always_notify_updater')
  ticket_id = ticket.id

  recipients = RecipientList(env, can_see_email(req, config, ticket.resource))
  cursor = env.get_db_cnx().cursor()

  # Harvest email addresses from the cc, reporter, and owner fields
  cursor.execute("SELECT cc,reporter,owner FROM ticket WHERE id=%s", (ticket_id,))
  row = cursor.fetchone()
  if row:
    recipients.add(row[1], Recipient.REPORTER_ROLE, notify_reporter)
    recipients.add(row[2], Recipient.OWNER_ROLE, notify_owner)
    
    ccrecipients = row[0] and row[0].replace(',', ' ').split() or []
    for recipient in ccrecipients:
      recipients.add(recipient, Recipient.SUBSCRIBER_ROLE, True)

  # Harvest email addresses from the author field of ticket_change(s)
  cursor.execute("SELECT DISTINCT author,ticket FROM ticket_change WHERE ticket=%s", (ticket_id,))
  for author,ticket in cursor:
    recipients.add(author, Recipient.PARTICIPANT_ROLE, notify_updater)
    
  also_notified_list = config.getlist('notification', 'smtp_always_cc', default=[])
  if not isinstance(also_notified_list, list):
    also_notified_list = [ also_notified_list ]

  also_notified_bcc = config.getlist('notification', 'smtp_always_bcc', default=[])
  if not isinstance(also_notified_bcc, list):
    also_notified_list.append(also_notified_bcc)
  else:
    also_notified_list.extend(also_notified_bcc)
    
  for recipient_mail in also_notified_list:
    if (not recipient_mail) or len(recipient_mail) == 0 or recipient_mail.find('@') == -1:
      continue

    userinfo = get_user_info(env, recipient_mail)
    if userinfo:
      # Username is known
      username, fullname, email = userinfo
      recipients.add(userinfo[0], Recipient.ALWAYS_ROLE, True)
    else:
      recipients.add(recipient_mail, Recipient.ALWAYS_ROLE, True)

  return recipients
  
def is_user_notified(config, env, username, ticket_id):
  if ticket_id:
    notify_reporter = config.getbool('notification', 'always_notify_reporter')
    notify_owner = config.getbool('notification', 'always_notify_owner')
    notify_updater = config.getbool('notification', 'always_notify_updater')

    cursor = env.get_db_cnx().cursor()
    emailchecker = EmailChecker(env)
    
    # Harvest email addresses from the cc, reporter, and owner fields
    cursor.execute("SELECT cc,reporter,owner FROM ticket WHERE id=%s", (ticket_id,))
    row = cursor.fetchone()
    if row:
      # Reporter - if one is set (theoretically there should always be a reporter but who knows...)
      if row[1]:
        userinfo = get_user_info(env, row[1])
        if userinfo and notify_reporter and userinfo[0] == username and emailchecker.match_short_address(userinfo[2]):
          return True
      
      # Owner - if one is set
      if row[2]:
        userinfo = get_user_info(env, row[2])
        if userinfo and notify_owner and userinfo[0] == username and emailchecker.match_short_address(userinfo[2]):
          return True

      # CC
      ccrecipients = row[0] and row[0].replace(',', ' ').split() or []
      for recipient in ccrecipients:
        userinfo = get_user_info(env, recipient)
        if userinfo and userinfo[0] == username and emailchecker.match_short_address(userinfo[2]):
          return True

    if notify_updater:
      # Harvest email addresses from the author field of ticket_change(s)
      cursor.execute("SELECT DISTINCT author,ticket FROM ticket_change WHERE ticket=%s", (ticket_id,))
      for author,ticket in cursor:
        userinfo = get_user_info(env, author)
        if userinfo and userinfo[0] == username and emailchecker.match_short_address(userinfo[2]):
          return True
    
  also_notified_list = config.getlist('notification', 'smtp_always_cc', default=[])
  if not isinstance(also_notified_list, list):
    also_notified_list = [ also_notified_list ]

  also_notified_bcc = config.getlist('notification', 'smtp_always_bcc', default=[])
  if not isinstance(also_notified_bcc, list):
    also_notified_list.append(also_notified_bcc)
  else:
    also_notified_list.extend(also_notified_bcc)
    
  for recipient_mail in also_notified_list:
    if (not recipient_mail) or len(recipient_mail) == 0 or recipient_mail.find('@') == -1:
      continue

    userinfo = get_user_info(env, recipient_mail)
    if userinfo and userinfo[0] == username and emailchecker.match_short_address(userinfo[2]):
      return True

  return False
  

class EmailChecker(object):
  def __init__(self, env):
    ##########################################################################
    # This code is taken from: trac.notification.NotifyEmail.__init__()
    addrfmt = EMAIL_LOOKALIKE_PATTERN
    admit_domains = env.config.get('notification', 'admit_domains')
    if admit_domains:
        pos = addrfmt.find('@')
        domains = '|'.join([x.strip() for x in \
                            admit_domains.replace('.','\.').split(',')])
        addrfmt = r'%s@(?:(?:%s)|%s)' % (addrfmt[:pos], addrfmt[pos+1:], 
                                          domains)
    self.__shortaddr_re = re.compile(r'%s$' % addrfmt)
    self.__longaddr_re = re.compile(r'^\s*(.*)\s+<(%s)>\s*$' % addrfmt);
    #
    ##########################################################################

  def match_short_address(self, address):
    return self.__shortaddr_re.search(address)

  def match_long_address(self, address):
    return self.__longaddr_re.search(address)


class RecipientList(object):
  def __init__(self, env, show_email):
    self.__recipients = {}
    self._show_email = show_email
    self._env = env
    self._emailchecker = EmailChecker(env)

  def add(self, name, role, is_notified):
    # If the name is not known (for instance when no one is assigned as owner)
    # go out here.
    if not name:
      return
    
    try:
      #self._env.log.debug("Possible recipient: " + name + " (Role: " + str(role) + ")")
      recipient = Recipient(self._env, name, role, self._show_email, is_notified,
                            self._emailchecker)
      #self._env.log.debug("Possible new recipient: " + unicode(recipient))
    except NoRecipientAddressException:
      # No email address was provided for this name. Ignore it.
      return
      
    if self.__recipients.has_key(recipient.mail):
      old_recipient = self.__recipients[recipient.mail]
      
      if recipient.weight >= old_recipient.weight:
        # Always merge information. This is necessary if "notify_owner" is "false"
        # and the owner subscribed. In this case the subscription recipient has
        # a higher weight and is therefor discarded.
        old_recipient.merge(recipient)
        # The new recipient doesn't provide more information than the old one
        return
        
      recipient.merge(old_recipient)

        
    self.__recipients[recipient.mail] = recipient
    
    #self._env.log.debug(unicode(recipient))
    
  def __iter__(self):
    return RecipientIterator(self.__recipients)
    
class RecipientIterator(object):
  def __init__(self, recipients):
    self.__order = []
    for recipient in recipients.values():
      self.__order.append(recipient)
      
    self.__key = 0
    self.__order.sort(cmp=lambda x,y: cmp(x.name.lower(), y.name.lower()))
    
  def next(self):
    if self.__key < len(self.__order): 
      recipient = self.__order[self.__key]
      self.__key += 1
      return recipient
    else: 
      raise StopIteration
  
  
class Recipient(object):
  """ Provides information about a certain recipient. At least the attributes
      "name", "mail", "id", "role" and "weight" are always available.
  """
  
  REPORTER_ROLE = 1
  OWNER_ROLE = 2
  SUBSCRIBER_ROLE = 4
  PARTICIPANT_ROLE = 8
  ALWAYS_ROLE = 16
  
  def __init__(self, env, name, role, show_email, is_notified, emailchecker):
    self.role = role
    self.is_notified = is_notified
    
    if name.find('@') == -1:
      # Username or "normal" name
      userinfo = get_user_info(env, name)
      if userinfo:
        # Username is known
        username, fullname, email = userinfo
        if not email:
          raise NoRecipientAddressException
        
        matcher = emailchecker.match_short_address(email)
        if not matcher:
          raise NoRecipientAddressException
        
        self.id = username
        self.mail = email
        if fullname:
          self.name = fullname
          self.weight = 1
        else:
          self.name = username
          self.weight = 2
      else:
        # Username is unknown and doesn't contain a '@' sign. So it can't 
        # recieve any email.
        raise NoRecipientAddressException
    else:
      # Mail address (plus possible a name)
      matcher = emailchecker.match_long_address(name)
      if matcher:
        self.name = matcher.group(1)
        self.mail = matcher.group(2)
        self.id = self.mail
        self.weight = 3
      else:
        matcher = emailchecker.match_short_address(name)
        if not matcher:
          raise NoRecipientAddressException
        
        self.mail = matcher.group(0)

        if show_email:
          self.name = self.mail
        else:
          self.name = obfuscate_email_address(self.mail)
        
        self.id = self.mail
        self.weight = 4
        
  def merge(self, other_recipient):
    if not self.is_notified and other_recipient.is_notified:
      self.is_notified = True
      
    self.role = self.role | other_recipient.role
        
  def __str__(self):
    return u"Recipient(name='" + unicode(self.name) + u"'" + \
           u" mail='" + unicode(self.mail) + u"'" + \
           u" id='" + unicode(self.id) + u"'" + \
           u" weight='" + unicode(self.weight) + u"'" + \
           u" role='" + unicode(self.role) + u"'" + \
           u" is_notified='" + str(self.is_notified) + "')"
    
class NoRecipientAddressException(Exception):
  pass
