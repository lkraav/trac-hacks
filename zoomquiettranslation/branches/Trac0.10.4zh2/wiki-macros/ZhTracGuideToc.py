# -*- coding: utf-8 -*-
"""
This macro shows a quick and dirty way to make a table-of-contents for a set
of wiki pages.
"""

Zh_TOC = [('ZhTracGuide',                    u'索引'),
       ('ZhTracInstall',                  u'安装'),
       ('ZhTracUpgrade',                  u'升级'),
       ('ZhTracIni',                      u'配置'),
       ('ZhTracAdmin',                    u'管理'),
       ('ZhTracBackup',                   u'恢复'),
       ('ZhTracLogging',                  u'日志'),
       ('ZhTracPermissions' ,             u'权限'),
       ('ZhTracWiki',                     u'Wiki帮助'),
       ('ZhWikiFormatting',               u'Wiki格式'),
       ('ZhTracTimeline',                 u'时间轴'),
       ('ZhTracBrowser',                  u'代码库'),
       ('ZhTracChangeset',                u'变量集'),
       ('ZhTracRoadmap',                  u'路线图'),
       ('ZhTracTickets',                  u'传票'),
       ('ZhTracQuery',                    u'传票查询'),
       ('ZhTracReports',                  u'报表'),
       ('ZhTracRss',                      u'RSS支持'),
       ('ZhTracNotification',             u'通知'),
       ('ZhTracInterfaceCustomization',   u'自定义'),
       ('ZhTracPlugins',                  u'插件'),
       ('ZhAbout',                        u'关于汉化版Trac')
       ]



def execute(hdf, args, env):
    html = u'<div class="wiki-toc">' \
           '<h4>Contents</h4>' \
           '<ul>'
    curpage = '%s' % hdf.getValue('wiki.page_name', '')
    lang, page = '/' in curpage and curpage.split('/', 1) or ('', curpage)
    for (ref, title) in Zh_TOC:
        if page == ref:
            cls =  ' class="active"'
        else:
            cls = ''
        html += '<li%s><a href="%s">%s</a></li>' \
                % (cls, env.href.wiki(lang+ref), title)
    return html + '</ul></div>'
