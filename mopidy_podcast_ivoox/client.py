#!/usr/bin/python
# -*- coding: utf8 -*-
from __future__ import unicode_literals, print_function

import logging
import requests
import uritools

from api import IVooxAPI
from scrapper import Scrapper


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def _cache(method):
    def cached_method(self, *args, **kwargs):
        if len(args) != 0 or any(parms is not None for parms in kwargs.itervalues()):
            return method(self, *args, **kwargs)
        if method not in self._cache:
            self._cache[method] = method(self, *args, **kwargs)
            logger.debug('Caching results of %r: %s', method, self._cache[method])
        else:
            logger.debug('Getting results of %r from cache', method)
        return self._cache[method]
    return cached_method

        
class IVooxClient(object):

    def __init__(self, lang='ES', country='ES'):
        super(IVooxClient, self).__init__()
        self.session = None
        self._cache = {}
        self.lang = lang
        self.country = country
        
    @property
    def baseurl(self):
        return IVooxAPI.get_baseurl(lang=self.lang,
                                    country=self.country)

    def login(self, user, password):
        if not (user and password):
            return False

        login_url = self._absolute_url(IVooxAPI.format_url('LOGIN'))
        self.session = requests.session()

        try:
            self.session.get(login_url)
            self.session.post(login_url,
                              data={'at-user': user,
                                    'at-pw': password,
                                    'redir': self.baseurl})

            # TODO: Check login is OK
            return True

        except Exception as ex:
            logger.error('Login error on %s: %s', self.baseurl, ex)
            return False

    def scrap_url(self, url, type=None, scrapper=None):
        if not scrapper:
            scrapper = IVooxAPI.get_scrapper(type=type, session=self.session)
        logger.debug('Using %s to analize %s', scrapper.__class__.__name__, url)
        results = scrapper.scrap(self._absolute_url(url))
        return results

    @_cache
    def get_categories(self, parent=None):
        parent = parent or 'f'
        explore_url = IVooxAPI.format_url('EXPLORE_EPISODES', parent, 1)

        return self.scrap_url(
            url=explore_url,
            scrapper=IVooxAPI.get_scrapper(
                type='categories',
                main=(parent == 'f'),
                session=self.session)
            )

    #@_cache
    def get_user_lists(self):
        lists = self.scrap_url(
            url=IVooxAPI.format_url('LIST_INDEX'),
            scrapper=IVooxAPI.get_scrapper(
                type='lists',
                session=self.session)
            )
        return lists[2:]

    #@_cache
    def get_subscriptions(self):
        return self.scrap_url(
            url=IVooxAPI.format_url('SUBSCRIPTIONS'),
            type='subscriptions')

    def explore_list(self, code, page=1):
        if code in ['pending', 'favorites', 'history', 'home']:
            list_url = IVooxAPI.format_url('LIST_{}'.format(code).upper(), page)
        else:
            list_url = IVooxAPI.format_url('EXPLORE_LISTS', code, page)

        return self.scrap_url(
            url=list_url,
            type='episodes')

    def explore(self, category=None, type='episodes', page=1):
        explore_url = IVooxAPI.format_url(
            'EXPLORE_{}'.format(type.upper()),
            category or 'f', 
            page)
        return self.scrap_url(
            url=explore_url, 
            type=type)

    def search(self, search_item, type='episodes', page=1):
        search_string = '-'.join(search_item.split()).lower()
        search_url = IVooxAPI.format_url(
            'SEARCH_{}'.format(type.upper()),
            search_string,
            page)
        return self.scrap_url(url=search_url, type=type)

    def clear_cache(self):
        self._cache = {}    

    def _absolute_url(self, relurl):
        return uritools.urijoin(self.baseurl, relurl)
