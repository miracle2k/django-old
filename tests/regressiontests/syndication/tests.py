# -*- coding: utf-8 -*-

from django.test import TestCase
from django.test.client import Client
from models import Article

class SyndicationFeedTest(TestCase):
    def test_complex_base_url(self):
        """
        Tests that that the base url for a complex feed doesn't raise a 500
        exception.
        """
        c = Client()
        response = c.get('/syndication/feeds/complex/')
        self.assertEquals(response.status_code, 404)

    def test_escaping(self):
        """
        Tests that titles and descriptions are double-escaped correctly.
        http://www.intertwingly.net/blog/2006/05/06/Keeping-Keith-Richards-Company
        """
        a1 = Article.objects.create(title='Article 1')
        a2 = Article.objects.create(title='Cool: 1 > 2!')
        a3 = Article.objects.create(title='M & M')
        c = Client()
        response = c.get('/syndication/feeds/articles/')
        self.assertContains(response, "Cool: 1 &gt; 2")
        self.assertContains(response, "M &amp; M")
