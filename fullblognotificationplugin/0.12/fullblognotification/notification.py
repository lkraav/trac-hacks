# -*- coding: utf-8 -*-
"""
Copyright Nick Loeve 2008
"""

import re
import hashlib

from tracfullblog.model import BlogPost, BlogComment

from genshi.template.text import NewTextTemplate
from trac import __version__
from trac.config import Option, ListOption, BoolOption
from trac.core import *
from trac.notification import NotifyEmail, NotificationSystem
from trac.util.datefmt import format_datetime
from trac.util.text import CRLF
from trac.util.translation import deactivate, reactivate

class FullBlogNotificationEmail(NotifyEmail):

    """ You can override this template in your local templates directory """
    template_name = "fullblognotification_email_template.txt"    
    
    def __init__(self, env):
        NotifyEmail.__init__(self, env)
        self.from_name = self.config.get('fullblog-notification', 'from_name')
        self.from_email = self.config.get('fullblog-notification', 'from_email')
        self.notification_actions = self.config.getlist('fullblog-notification', 
                                                        'notification_actions')  
        self.no_notification_categories = self.config.getlist('fullblog-notification',
                                                              'no_notification_categories')

    def notify(self, blog, action, version=None, time=None, comment=None,
               author=None):

        # Don't notify if action is explicitly omitted from notification_actions
        if self.notification_actions != [] and \
           action not in self.notification_actions:
            self.env.log.info('No notification sent because action is omitted ' \
                              'from notification_actions option list')
            return
        
        # Don't notify if post has one of the specified categories
        for category in blog.category_list:
            if category in self.no_notification_categories:
                self.env.log.info('No notification sent because there are one ' \
                                  'or more matches between post\'s categories list ' \
                                  'and no_notification_categories option list')
                return
        
        self.blog = blog
        self.change_author = author
        self.time = time
        self.action = action
        self.version = version

        self.data['name']= blog.name
        self.data['title']= blog.title
        self.data['body']= blog.body
        self.data['comment']= comment
        self.data['version']= version
        self.data['author']= author
        self.data['action']= action
        self.data['time'] = format_datetime(time, '%Y-%m-%d %H:%M')
        self.data['url']= self.env.abs_href.blog(blog.name)
        self.data['project'] = {'name': self.env.project_name,
                                'url': self.env.project_url,
                                'description': self.env.project_description}
        
        subject = self.format_subject()

        NotifyEmail.notify(self, blog.name, subject)

    def get_recipients(self, pagename):
        """Once day we could build a CC list from author/commenters"""
        if self.config.getbool('fullblog-notification', 'always_notify_author'):
            return ([self.blog.author], [self.change_author or 'anonymous']) 
        return ([self.blog.author], [])

    def send(self, torcpts, ccrcpts, mime_headers={}):
        """
        this method is based NotifyEmail in trac/notification.py

        As the default trac NotifyEmail class assumes alot, and will overwrite headers
        we do not call our ancestor class method here, but send the mail direct
        """
        from email.MIMEText import MIMEText
        from email.Utils import formatdate
        stream = self.template.generate(**self.data)
        # don't translate the e-mail stream 
        t = deactivate()
        try:
            body = stream.render('text')
        finally:
            reactivate(t) 
        projname = self.env.project_name
        public_cc = self.config.getbool('notification', 'use_public_cc')        
        headers = {}
        headers['X-Mailer'] = 'Trac %s, by Edgewall Software' % __version__
        headers['X-Trac-Version'] =  __version__
        headers['X-Trac-Project'] =  projname
        headers['X-URL'] = self.env.project_url
        headers['Precedence'] = 'bulk'
        headers['Auto-Submitted'] = 'auto-generated'
        headers['Subject'] = self.subject
        headers['From'] = (self.from_name or projname, self.from_email)
        headers['Reply-To'] = self.replyto_email
        
        # add Message-ID and In-Reply-To for threaded mail clients
        if self.action == 'post_created':
            headers['Message-ID'] = self.get_message_id(projname, self.blog.name)
        else:
            headers['Message-ID'] = self.get_message_id(projname, self.blog.name, self.time)
            headers['In-Reply-To'] = headers['References'] = self.get_message_id(projname, self.blog.name)

        def build_addresses(rcpts):
            """Format and remove invalid addresses"""
            return filter(lambda x: x, [self.get_smtp_address(addr) for addr in rcpts])

        def remove_dup(rcpts, all):
            """Remove duplicates"""
            tmp = []
            for rcpt in rcpts:
                if not rcpt in all:
                    tmp.append(rcpt)
                    all.append(rcpt)
            return (tmp, all)

        toaddrs = build_addresses(torcpts)
        ccaddrs = build_addresses(ccrcpts)
        accparam = self.config.getlist('fullblog-notification', 'smtp_always_cc')
        accaddrs = accparam and build_addresses(accparam) or []

        recipients = []
        (toaddrs, recipients) = remove_dup(toaddrs, recipients)
        (ccaddrs, recipients) = remove_dup(ccaddrs, recipients)
        (accaddrs, recipients) = remove_dup(accaddrs, recipients)

        # if there is not valid recipient, leave immediately
        if len(recipients) < 1:
            self.env.log.info('no recipient for a fullblog notification')
            return

        cc = accaddrs + ccaddrs
        if cc:
            headers['Cc'] = ', '.join(cc)
        if toaddrs:
            headers['To'] = ', '.join(toaddrs)
        headers['Date'] = formatdate()
        msg = MIMEText(body, 'plain')
        # Message class computes the wrong type from MIMEText constructor,
        # which does not take a Charset object as initializer. Reset the
        # encoding type to force a new, valid evaluation
        del msg['Content-Transfer-Encoding']
        msg.set_charset(self._charset)
        self.add_headers(msg, headers);
        self.add_headers(msg, mime_headers);
        NotificationSystem(self.env).send_email(self.from_email, recipients,
                                                msg.as_string())

    def format_subject(self):
        template = self.config.get('fullblog-notification', 'subject_template')
        template = NewTextTemplate(template.encode('utf8'))

        prefix = self.config.get('notification', 'smtp_subject_prefix')
        if prefix == '__default__':
            prefix = '[%s]' % self.config.get('project', 'name')
       
        action = self.action.strip('post_').replace('_', ' ')

        data = {
            'blog': self.blog,
            'prefix': prefix,
            'action': action
        }
        return template.generate(**data).render('text', encoding=None).strip()

    def get_message_id(self, project_name, blog_title, time=None):
        s = '%s.%s.%s' % (project_name, blog_title, time or "")
        digest = hashlib.md5(s).hexdigest()
        host = self.from_email[self.from_email.find('@') + 1:]
        msg_id = '<%03d.%s@%s>' % (len(s), digest, host)
        return msg_id
