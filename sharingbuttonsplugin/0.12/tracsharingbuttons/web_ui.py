# -*- coding: utf-8 -*-

import re

from genshi.builder import tag
from genshi.filters import Transformer
try:
    from babel.core import LOCALE_ALIASES
except ImportError:
    LOCALE_ALIASES = {}

from trac.core import Component, implements
from trac.config import ListOption, BoolOption, Option
from trac.web.api import IRequestFilter, ITemplateStreamFilter
from trac.web.chrome import Chrome, add_meta
from trac.util.compat import partial
from trac.util.translation import dgettext


__all__ = ['SharingButtonsModule']


DESCRIPTION_SIZE = 200


class SharingButtonsModule(Component):
    implements(IRequestFilter, ITemplateStreamFilter)

    _buttons = ListOption('sharing-buttons', 'buttons', 'twitter,facebook')
    _buttons_class = Option('sharing-buttons', 'buttons_class', '')
    _buttons_style = Option('sharing-buttons', 'buttons_style', '')
    _transform_xpath = Option('sharing-buttons', 'transform_xpath', '')
    _transform_method = Option('sharing-buttons', 'transform_method', '')

    _default_settings = {
        'buttons_class': 'noprint sharing-buttons',
        'buttons_style': 'margin-left:6px',
        'transform_xpath': '//div[@id="content"]//h1',
        'transform_method': 'append',
        'buttons_class.wiki_view': 'noprint sharing-buttons',
        'buttons_style.wiki_view': 'margin-left:6px',
        'transform_xpath.wiki_view': '//div[@id="pagepath"]',
        'transform_method.wiki_view': 'append',
    }

    _twitter_data_count = Option('sharing-buttons', 'twitter.data-count',
        'horizon')

    _facebook_width = Option('sharing-buttons', 'facebook.width', '112')
    _facebook_font = Option('sharing-buttons', 'facebook.font', 'arial')
    _facebook_layout = Option('sharing-buttons', 'facebook.layout',
        'button_count')

    _hatena_bookmark_layout = Option('sharing-buttons',
        'hatena-bookmark.layout', 'standard')

    _wiki_enabled = BoolOption('sharing-buttons', 'wiki_enabled', 'true')
    _milestone_enabled = BoolOption('sharing-buttons', 'milestone_enabled',
        'true')
    _browser_enabled = BoolOption('sharing-buttons', 'browser_enabled', 'true')
    _report_enabled = BoolOption('sharing-buttons', 'report_enabled', 'true')
    _ticket_enabled = BoolOption('sharing-buttons', 'ticket_enabled', 'true')

    def pre_process_request(self, req, handler):
        return handler

    def post_process_request(self, req, template, data, content_type):
        if req.method == 'GET':
            if template == 'ticket.html':
                self._add_metas_ticket(req, data)
            elif template in ('wiki_view.html', 'wiki_diff.html'):
                self._add_metas_wiki(req, data)
            elif template == 'milestone_view.html':
                self._add_metas_milestone(req, data)
            elif template == 'report_view.html':
                self._add_metas_report(req, data)
        return template, data, content_type

    def filter_stream(self, req, method, filename, stream, data):
        if req.method != 'GET':
            return stream

        if filename == 'ticket.html':
            if self._ticket_enabled:
                model = data.get('ticket')
                if model and model.exists:
                    return self._transform(stream, req, filename)
            return stream

        if filename in ('wiki_view.html', 'wiki_diff.html'):
            if self._wiki_enabled:
                model = data.get('page')
                if (model and model.exists and
                    req.args.get('action', 'view') == 'view' and
                    not req.args.get('page')):
                    return self._transform(stream, req, filename,
                                           req.abs_href.wiki(model.name))
            return stream

        if filename == 'milestone_view.html':
            if self._milestone_enabled:
                model = data.get('milestone')
                if model and model.exists:
                    return self._transform(stream, req, filename)
            return stream

        if filename == 'roadmap.html':
            if self._milestone_enabled:
                return self._transform(stream, req, filename)
            return stream

        if filename in ('dir_entries.html', 'browser.html', 'changeset.html',
                        'diff_form.html', 'revisionlog.html'):
            if self._browser_enabled:
                return self._transform(stream, req, filename)
            return stream

        if filename == 'report_view.html':
            if self._report_enabled:
                return self._transform(stream, req, filename)
            return stream

        return stream

    def _add_metas(self, req, title, description, url=None):
        if title:
            title = u'%s – %s' % (title, self.env.project_name)
        else:
            title = self.env.project_name
        description = re.compile(r'\s+', re.U).sub(' ', description or '')
        if len(description) > DESCRIPTION_SIZE:
            description = description[:DESCRIPTION_SIZE - 1] + u'\u2026'

        add_meta(req, 'summary', name='twitter:card')
        add_meta(req, title, name='twitter:title')
        add_meta(req, title, name='og:title')
        add_meta(req, description, name='twitter:description')
        add_meta(req, description, name='og:description')
        if url:
            add_meta(req, url, name='twitter:url')
            add_meta(req, url, name='og:url')
        data = Chrome(self.env).get_logo_data(req.href, req.abs_href)
        src = data.get('src_abs')
        if src:
            add_meta(req, src, name='twitter:image')
            add_meta(req, src, name='og:image')

    def _add_metas_ticket(self, req, data):
        if not self._ticket_enabled:
            return
        ticket = data.get('ticket')
        if not ticket or not ticket.exists:
            return
        title = '#%s (%s)' % (ticket.id, ticket['summary'])
        self._add_metas(title, ticket['description'],
                        req.abs_href.ticket(ticket.id))

    def _add_metas_wiki(self, req, data):
        if not self._wiki_enabled:
            return
        page = data.get('page')
        if not page or not page.exists:
            return
        if data.get('version'):
            url = req.abs_href.wiki(page.name, version=page.version)
        else:
            url = req.abs_href.wiki(page.name)
        self._add_metas(req, data.get('title'), page.text, url)

    def _add_metas_milestone(self, req, data):
        if not self._milestone_enabled:
            return
        milestone = data.get('milestone')
        if not milestone or not milestone.exists:
            return
        title = 'Milestone %s' % milestone.name
        url = req.abs_href.milestone(milestone.name)
        self._add_metas(req, title, milestone.description, url)

    def _add_metas_report(self, req, data):
        if not self._report_enabled:
            return
        report = data.get('report')
        if not report:
            return
        url = req.abs_href.report(report['id'])
        self._add_metas(req, data.get('title'), data.get('description'), url)

    def _get_config(self, name, filename):
        key = '%s.%s' % (name, filename)
        val = self.config.get('sharing-buttons', key)
        if not val and key in self._default_settings:
            return self._default_settings[key]
        val = self.config.get('sharing-buttons', name)
        return val or self._default_settings[name]

    def _transform(self, stream, req, filename, url=None):
        filename = filename.rstrip('.html')
        xpath = self._get_config('transform_xpath', filename)
        method = self._get_config('transform_method', filename)
        class_ = self._get_config('buttons_class', filename)
        style = self._get_config('buttons_style', filename)

        if method not in ('after', 'before', 'append', 'prepend'):
            return stream

        locale = req.locale and str(req.locale)
        kwargs = {'class_': class_ or None, 'style': style or None}
        create = partial(self._create_buttons, url, locale, kwargs)
        if create:
            stream |= getattr(Transformer(xpath), method)(create)
        return stream

    def _create_buttons(self, url, locale, kwargs):
        args = []
        for button in self._buttons:
            if button == 'twitter':
                args.extend(self._create_twitter_button(url, locale))
            elif button == 'facebook':
                args.extend(self._create_facebook_button(url, locale))
            elif button == 'hatena-bookmark':
                args.extend(self._create_hatena_bookmark_button(url, locale))
        if args:
            return tag.span(*args, **kwargs)

    def _create_twitter_button(self, url, locale):
        return [
            tag.a('Tweet',
                  href='//twitter.com/share',
                  class_='twitter-share-button',
                  data_url=url, data_counturl=url,
                  data_lang=locale or None,
                  data_count=self._twitter_data_count),
            tag.script(type='text/javascript',
                       src='//platform.twitter.com/widgets.js'),
        ]

    def _create_facebook_button(self, url, locale):
        width = self._facebook_width
        font = self._facebook_font
        layout = self._facebook_layout

        kwargs = {'width': width, 'font': font, 'layout': layout,
                  'send': 'false', 'action': 'like', 'show_faces': 'false',
                  'colorscheme': 'light'}
        if url:
            kwargs['url'] = url
        if locale and '_' not in locale:
            locale = LOCALE_ALIASES.get(locale)
        kwargs = dict(('data_' + key, val) for key, val in kwargs.iteritems())
        kwargs['class_'] = 'fb-like'
        return [
            tag.div('', id='fb-root', style='display:inline-block'),
            tag.script(type='text/javascript')("""\
(function(d, s, id) {
  var js, fjs = d.getElementsByTagName(s)[0];
  if (d.getElementById(id)) return;
  js = d.createElement(s);
  js.id = id;
  js.src = '//connect.facebook.net/%s/all.js#xfbml=1';
  fjs.parentNode.insertBefore(js, fjs);
}(document, 'script', 'facebook-jssdk'));""" % (locale or 'en_US')),
            tag.div(**kwargs),
        ]

    def _create_hatena_bookmark_button(self, url, locale):
        href = '//b.hatena.ne.jp/entry/'
        if url:
            href += url.replace('#', '%23')
        return [
            tag.a(tag.img(src='//b.st-hatena.com/images/entry-button/button-only.gif',
                          alt=u'このエントリーをはてなブックマークに追加',
                          width='20', height='20', style='border:none'),
                  href=href, class_='hatena-bookmark-button',
                  data_hatena_bookmark_layout=self._hatena_bookmark_layout,
                  title=u'このエントリーをはてなブックマークに追加'),
            tag.script(type='text/javascript', charset='utf-8', async='async',
                       src='//b.st-hatena.com/js/bookmark_button_wo_al.js'),
        ]
