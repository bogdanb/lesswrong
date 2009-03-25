# -*- coding: utf-8 -*-
import nose

from r2.tests import ModelTest

from r2.lib.db.thing import NotFound

import r2.lib.importer
from r2.lib.importer import Importer

import re
import datetime

class ImporterFixture(object):

    def __init__(self):
        self.ids = {}
        self.data = []
        self.posts_by_id = {}

    def add_post(self,
                 author='Anonymous',
                 author_email='anon@nowhere.org',
                 category='Category',
                 title='Title',
                 description='',
                 mt_text_more='',
                 mt_keywords='',
                 status='Publish',
                 date_created=None,
                 permalink=None):
        post_id = self.post_id
        if not date_created:
            date_created = datetime.datetime.now().strftime('%m/%d/%Y %r')
        if not permalink:
            permalink = 'http://www.overcomingbias.com/%s.html' % post_id
        post = { 'postid': post_id,
                 'author': author,
                 'authorEmail': author_email,
                 'category': category,
                 'title': title,
                 'description': description,
                 'mt_text_more': mt_text_more,
                 'mt_keywords': mt_keywords,
                 'status': status,
                 'dateCreated': date_created,
                 'permaLink': permalink }
        self.data.append(post)
        self.posts_by_id[post_id] = post
        return post_id

    def add_comment(self,
                    post_id,
                    author='Anonymous',
                    author_email='anon@nowhere.org',
                    author_url='',
                    body='',
                    date_created=None):
      if not date_created:
          date_created = datetime.datetime.now().strftime('%m/%d/%Y %r')

          comment = { 'author': author,
                      'authorEmail': author_email,
                      'authorUrl': author_url,
                      'body': body,
                      'dateCreated': date_created }

          self.posts_by_id[post_id].setdefault('comments', []).append(comment)

          return comment

    def __getattr__(self, attr):
        if attr.endswith('_id'):
            self.ids[attr] = self.ids.get(attr, 0) + 1
            return "%s-%d" % (attr[:-3], self.ids[attr])
        else:
            raise AttributeError, '%s not found' % attr

    def get_data(self):
        return self.data

class TestImporter(object):
    url_content = (
        ('Some text', 'Some text'),
        ('Blah <a href="http://www.overcomingbias.com/2007/11/passionately-wr.html">Link</a> more',
            'Blah <a href="http://www.overcomingbias-rewritten.com/2007/11/passionately-wr.html">Link</a> more'),
        ('Multiple urls: http://www.overcomingbias.com/ and http://overcomingbias.com and http://google.com/?q=test',
            'Multiple urls: http://www.overcomingbias-rewritten.com/ and http://overcomingbias-rewritten.com and http://google.com/?q=test'),
        ('Query string: http://www.google.com/search?rls=en-us&q=overcomingbias&ie=UTF-8&oe=UTF-8',
            'Query string: http://www.google.com/search?rls=en-us&q=overcomingbias-rewritten&ie=UTF-8&oe=UTF-8'),
        ('IP Address: http://72.14.235.104/?q=overcomingbias',
            'IP Address: http://72.14.235.104/?q=overcomingbias-rewritten'),
        ('Google cache: http://72.14.235.132/search?client=safari&rls=en-us&q=cache:http://www.overcomingbias.com/2007/11/passionately-wr.html&ie=UTF-8&oe=UTF-8',
            'Google cache: http://72.14.235.132/search?client=safari&rls=en-us&q=cache:http://www.overcomingbias-rewritten.com/2007/11/passionately-wr.html&ie=UTF-8&oe=UTF-8'),
        ("""Overcoming Bias links: http://www.overcomingbias.com
            http://www.overcomingbias.com/
            http://www.overcomingbias.com/2006/11/beware_heritabl.html
            http://www.overcomingbias.com/2006/11/beware_heritabl.html#comment-25685746""",
        """Overcoming Bias links: http://www.overcomingbias-rewritten.com
            http://www.overcomingbias-rewritten.com/
            http://www.overcomingbias-rewritten.com/2006/11/beware_heritabl.html
            http://www.overcomingbias-rewritten.com/2006/11/beware_heritabl.html#comment-25685746"""),
        ('Unicode: (http://www.overcomingbias.com/ÜnîCöde¡っ)', 'Unicode: (http://www.overcomingbias-rewritten.com/ÜnîCöde¡っ)'),
    )

    @staticmethod
    def url_rewriter(match):
        # This replacement will deliberately match again if the importer
        # processes the same url twice
        return match.group().replace('overcomingbias', 'overcomingbias-rewritten')

    @staticmethod
    def check_text(text, expected_text):
        assert text == expected_text

    def test_generate_password(self):
        pw_re = re.compile(r'[1-9a-hjkmnp-uwxzA-HJKMNP-UWXZ@#$%^&*]{8}')

        # This test is a bit questionable given the random generation
        # but its better than no test
        for i in range(10):
            password = r2.lib.importer.generate_password()
            # print password
            assert pw_re.match(password)

    def test_filter_html_in_titles(self):
        pass

    def test_set_comment_is_html(self):
        pass

    def test_auto_account_creation(self):
        pass

    def test_cleaning_of_content(self):
        # There are a lot of ^M's in the comments
        pass

from mocktest import *
from r2.models import Account
from r2.models.account import AccountExists
class TestImporterMocktest(TestCase):

    @property
    def importer(self):
        return Importer()

    def test_get_or_create_account_exists(self):
        fixture = ImporterFixture()
        post = fixture.add_post(author='Test User', author_email='user@host.com')

        sr = mock_wrapper()
        account_anchor = mock_on(Account)
        account = mock_wrapper().with_methods(_safe_load=None)
        account_anchor._query.returning([account.mock]).is_expected

        mock_on(r2.lib.importer).register.is_expected.no_times()

        self.importer.import_into_subreddit(sr.mock, fixture.get_data())

    def test_get_or_create_account_exists2(self):
        fixture = ImporterFixture()
        post = fixture.add_post(author='Test User', author_email='user@host.com')

        def query_action(name_match, email_match):
            return [account.mock] if name_match and email_match else []

        sr = mock_wrapper()
        account_anchor = mock_on(Account)
        account = mock_wrapper().with_methods(_safe_load=None)
        query = account_anchor._query
        query.action = query_action
        query.is_expected.twice() # Second attempt should succeed
        account_anchor.c.with_children(name='TestUser', email='user@host.com')

        mock_on(r2.lib.importer).register.is_expected.no_times()

        self.importer.import_into_subreddit(sr.mock, fixture.get_data())

    def test_get_or_create_account_exists3(self):
        fixture = ImporterFixture()
        post = fixture.add_post(author='Test User', author_email='user@host.com')

        def query_action(name_match, email_match):
            return [account.mock] if name_match and email_match else []

        sr = mock_wrapper()
        account_anchor = mock_on(Account)
        account = mock_wrapper().with_methods(_safe_load=None)
        query = account_anchor._query
        query.action = query_action
        query.is_expected.thrice() # Third attempt should succeed
        account_anchor.c.with_children(name='Test_User', email='user@host.com')

        mock_on(r2.lib.importer).register.is_expected.no_times()

        self.importer.import_into_subreddit(sr.mock, fixture.get_data())

    def test_get_or_create_account_not_exists(self):
        """Should create the account if it doesn't exist"""
        fixture = ImporterFixture()
        post = fixture.add_post(author='Test User', author_email='user@host.com')

        sr = mock_wrapper()
        account_anchor = mock_on(Account)
        query = account_anchor._query
        query.return_value = []
        query.is_expected.thrice()

        test_user5 = mock_wrapper().with_methods(_safe_load=None)
        test_user5.name = 'Test_User5'

        def register_action(name, password, email):
            if name != test_user5.name:
                raise AccountExists
            else:
                return test_user5.mock

        # Mocking on importer because it imported register
        account_module_anchor = mock_on(r2.lib.importer)
        register = account_module_anchor.register
        register.is_expected.exactly(4).times
        register.action = register_action

        self.importer.import_into_subreddit(sr.mock, fixture.get_data())

    def test_get_or_create_account_max_retries(self):
        """Should raise an error after 10 tries"""
        fixture = ImporterFixture()
        post = fixture.add_post(author='Test User', author_email='user@host.com')

        sr = mock_wrapper()
        account_anchor = mock_on(Account)
        query = account_anchor._query.returning([]).is_expected.thrice()
        account_module_anchor = mock_on(r2.lib.importer)
        register = account_module_anchor.register.raising(AccountExists).is_expected.exactly(10).times

        self.importer.import_into_subreddit(sr.mock, fixture.get_data())

    @ignore
    def test_failing_post(self):
        self.assertRaises(
            StandardError, lambda: self.importer._get_or_create_account('Test User', 'user@host.com'),
            message='Unable to generate account after 10 retries')

    @ignore
    def test_import_into_subreddit(self):
        sr = mock_wrapper()

        fixture = ImporterFixture()
        post = fixture.add_post()
        fixture.add_comment(post_id=post)

        importer = Importer()
        importer.import_into_subreddit(sr, fixture.get_data())

    @pending
    def test_set_sort_order(self):
        fixture = ImporterFixture()
        post = fixture.add_post()
        fixture.add_comment(post)
        importer = Importer()
        sr = mock_wrapper()
        link = mock_wrapper()
        mock_link = mock_on(Link)
        mock_link.create.returning(link.mock).with_args().is_expected
        importer.import_into_subreddit(sr.mock, fixture.get_data())