import unittest

from trac.core import TracError
from trac.perm import PermissionCache, PermissionSystem, PermissionError
from trac.resource import Resource
from trac.test import MockRequest
from trac.util.html import Markup
from trac.web.api import HTTPNotFound, RequestDone
from trac.web.href import Href

from tracfullblog.model import BlogPost, get_blog_posts
from tracfullblog.web_ui import FullBlogModule

from tracfullblog.tests import FullBlogTestCaseTemplate


class FullBlogListtingsTestCase(FullBlogTestCaseTemplate):

    def test_no_permission(self):
        req = MockRequest(self.env,
                method='GET', path_info='/blog', authname='user')
        module = FullBlogModule(self.env)
        self.assertTrue(module.match_request(req))
        self.assertRaises(PermissionError, module.process_request, req)

    def test_no_posts(self):
        PermissionSystem(self.env).grant_permission('user', 'BLOG_VIEW')
        req = MockRequest(self.env,
                method='GET', path_info='/blog', authname='user')

        module = FullBlogModule(self.env)
        self.assertTrue(module.match_request(req))
        template, data, _ = module.process_request(req)

        self.assertEquals('fullblog_view.html', template)
        self.assertEqual([], data['blog_post_list'])

    def test_single_post(self):
        PermissionSystem(self.env).grant_permission('user', 'BLOG_VIEW')
        bp = BlogPost(self.env, 'first_post')
        bp.update_fields(fields={'title': 'First Post', 'author': 'user',
            'body': 'First body'})
        self.assertEquals([], bp.save('user'))
        req = MockRequest(self.env,
                method='GET', path_info='/blog', authname='user')

        module = FullBlogModule(self.env)
        self.assertTrue(module.match_request(req))
        template, data, _ = module.process_request(req)

        self.assertEqual(1, data['blog_total'])
        self.assertEqual(1, len(data['blog_post_list']))
        self.assertEqual('First Post', data['blog_post_list'][0].title)


class FullBlogRssTestCase(FullBlogTestCaseTemplate):

    def test_rss_no_posts(self):
        PermissionSystem(self.env).grant_permission('user', 'BLOG_VIEW')
        req = MockRequest(self.env,
                method='GET', path_info='/blog', authname='user',
                args={'format': 'rss'})

        module = FullBlogModule(self.env)
        self.assertTrue(module.match_request(req))
        template, data, _ = module.process_request(req)

        self.assertEquals('fullblog.rss', template)


class FullBlogPostTestCase(FullBlogTestCaseTemplate):

    def test_new_blog_post(self):
        PermissionSystem(self.env).grant_permission('user', 'BLOG_ADMIN')
        req = MockRequest(self.env,
                method='POST', path_info='/blog/create', authname='user',
                args={'name': 'new_post', 'title': 'New post',
                     'author': 'user', 'body': 'The body',
                     'action': 'new', 'blog-save': ''})

        module = FullBlogModule(self.env)
        self.assertTrue(module.match_request(req))
        self.assertRaises(RequestDone, module.process_request, req)
        self.assertEquals('http://example.org/trac.cgi/blog/new_post',
                          req.headers_sent['Location'])
        self.assertEquals([], req.chrome['warnings'])

        posts = get_blog_posts(self.env)
        self.assertEquals(1, len(posts))
        self.assertEquals('New post', posts[0][4])


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(FullBlogListtingsTestCase))
    suite.addTest(unittest.makeSuite(FullBlogRssTestCase))
    suite.addTest(unittest.makeSuite(FullBlogPostTestCase))
    return suite
