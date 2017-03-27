#!/usr/bin/python
# -*- coding: iso-8859-15 -*-
from __future__ import unicode_literals, print_function

import logging
import requests
import datetime as dt
import uritools

from scrapper import Scrapper

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

API_URLS = {
    'LOGIN': 'ajx-login_zl.html',
    'EXPLORE_EPISODES': 'audios_sa_{}_{}.html',
    'EXPLORE_PROGRAMS': 'podcasts_sc_{}_{}.html',
    'EXPLORE_LISTS': 'list_bk_list_{}_{}.html',
    'SUBSCRIPTIONS': 'gestionar-suscripciones_je_1.html?order=date',
    'SEARCH_EPISODES': '{}_sb_{}.html',
    'SEARCH_PROGRAMS': '{}_sw_1_{}.html',
    'SEARCH_CHANNELS': '{}_sw_2_{}.html',
    'URL_EPISODE': '{1}-audios-mp3_rf_{0}_1.html',
    'URL_PROGRAM': 'podcast_sq_{}_1.html',
    'URL_CHANNEL': 'escuchar_nq_{}_1.html',
#    'XML_PROGRAM': '{1}_fg_{0}_filtro_1.xml',  # To allow pagination
    'XML_PROGRAM': '{1}_fg_{0}.xml',
    'LIST_PENDING': 'mis-audios_hn_{}.html',
    'LIST_FAVORITES': 'audios-que-me-gustan_hc_recomendados_{}.html'
    'LIST_HISTORY': 'audios-que-me-gustan_hc_{}.html'
}


def _cache_results(method):
    def cached_method(self, *args, **kwargs):
        if len(args) != 0 or any(parms!=None for parms in kwargs.itervalues()):
            return method(self, *args, **kwargs)
        if not method in self._cache:
            self._cache[method] = method(self, *args, **kwargs)
            logger.debug('Caching results of %r: %s', method, self._cache[method])
        else:
            logger.debug('Getting results of %r from cache', method)
        return self._cache[method]
    return cached_method


class IVooxAPI(object):

    API_BASE = 'http://www.ivoox.com/'

    def __init__(self):
        super(IVooxAPI, self).__init__()
        self.session = None
        self._cache = {}

    @property
    def baseurl(self):
        return self.API_BASE

    def set_language(self, lang='ES'):
        if lang != 'ES':
            self.API_BASE += lang + '/'

    def login(self, user, password):
        if not (user and password):
            return False

        login_url = self._absolute_url(API_URLS['LOGIN'])
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
            scrapper = self._get_scrapper(type=type, session=self.session)
        logger.debug('Using %s to analize %s', scrapper.__class__.__name__, url)
        results = scrapper.scrap(self._absolute_url(url))
        return results

    @_cache_results
    def get_categories(self, parent=None):
        parent = parent or 'f'
        explore_url = API_URLS['EXPLORE_EPISODES'].format(parent, 1)

        return self.scrap_url(
            url=explore_url,
            scrapper=self._get_scrapper(
                type='categories',
                main=(parent == 'f'),
                session=self.session)
            )

    @_cache_results
    def get_subscriptions(self):
        return self.scrap_url(
            url=API_URLS['SUBSCRIPTIONS'],
            type='subscriptions')

    @_cache_results
    def get_home(self):
        return self.scrap_url(url='', type='episodes')

    def get_episode_list(self, code, page=1):
        if code in ['pending', 'favorites', 'history']:
            list_url = API_URLS['LIST_{}'.format(code).upper()].format(page)
        else:
            list_url = API_URLS['EXPLORE_LISTS'].format(code, page)

        return self.scrap_url(
            url=list_url,
            type='episodes')

    def explore(self, category=None, type='episodes', page=1):
        explore_url = API_URLS['EXPLORE_{}'.format(type).upper()]

        return self.scrap_url(
            url=explore_url.format(category or 'f', page),
            type=type)

    def search(self, search_item, type='episodes', page=1):
        search_string = '-'.join(search_item.split()).lower()
        search_url = API_URLS['SEARCH_{}'.format(type).upper()]

        return self.scrap_url(
            url=search_url.format(search_string, page),
            type=type)

    def clear_cache(self):
        self._cache = {}

    def _get_scrapper(self, type, **options):
        if type == 'episodes':
            scrapper = IVooxEpisodes(**options)
        elif type == 'programs':
            scrapper = IVooxPrograms(**options)
        elif type == 'subscriptions':
            scrapper = IVooxSubscriptions(**options)
        elif type == 'categories':
            scrapper = IVooxCategories(**options)
        else:
            raise KeyError('No scrapper for type %s', type)

        return scrapper

    def _absolute_url(self, relurl):
        return uritools.urijoin(self.baseurl, relurl)


class IVooxParser(object):

    @staticmethod
    def extract_code(url):
        return url.split('_')[-2]

    @staticmethod
    def guess_program_url(code):
        return API_URLS['URL_PROGRAM'].format(code)

    @staticmethod
    def guess_program_xml(url):
        if url.endswith('.xml'):
            return url

        code = IVooxParser.extract_code(url) if url.endswith('.html') else url
        # arreglar después para multiidioma
        return 'http://www.ivoox.com/' + API_URLS['XML_PROGRAM'].format(code, 'podcast')

    @staticmethod
    def extract_duration(strtime):
        return sum(int(x) * 60 ** i
                   for i, x in enumerate(reversed(strtime.split(":"))))

    @staticmethod
    def date_from_fuzzy(fuzzy_date):

        def days_ago(days):
            return '{0:%d}-{0:%m}-{0:%Y}'.format(
                dt.date.today() - dt.timedelta(days))

        def months_ago(months):
            return '{0:%m}-{0:%Y}'.format(
                dt.date.today() - dt.timedelta(months * 30))

        def years_ago(years):
            return '{0:%Y}'.format(
                dt.date.today() - dt.timedelta(years * 365))

        def parse_error(input_string):
            return input_string

        fuzzy_date = fuzzy_date.lower().strip()

        parts = fuzzy_date.split()

        # Known words
        if fuzzy_date == 'hoy':
            return days_ago(0)
        elif fuzzy_date == 'ayer':
            return days_ago(1)
        # bug in ivoox page: returns '' for 2 days ago
        elif fuzzy_date in ('anteayer', ''):
            return days_ago(2)
        elif len(parts) == 1:
            # Only one unrecognized word
            return parse_error(fuzzy_date)

        # More than 2 parts:Unknown format
        if len(parts) > 2:
            return parse_error(fuzzy_date)

        # Format should be "N {día(s)|mes(es)|año(s)}
        try:
            date_number, date_word = parts
            date_number = int(date_number)
        except:
            return parse_error(fuzzy_date)

        if date_word in ('día', 'días'):
            return days_ago(date_number)
        if date_word in ('semana', 'semanas'):
            return days_ago(date_number * 7)
        elif date_word in ('mes', 'meses'):
            return months_ago(date_number)
        elif date_word in ('año', 'años'):
            return years_ago(date_number)

        # Got here -> Parsing error
        return parse_error(fuzzy_date)


class IVooxEpisodes(Scrapper):

    def declare_fields(self):
        self.add_field('name', './/div[@itemprop="episode"]/meta[@itemprop="name"]/@content')
        self.add_field('url', './/div[@itemprop="episode"]/meta[@itemprop="url"]/@content')
        self.add_field('description', './/div[@itemprop="episode"]/meta[@itemprop="description"]/@content')        
        self.add_field('image', './/img[@class="main"]/@src')
        self.add_field('duration', './/p[@class="time"]/text()',
                       parser=IVooxParser.extract_duration)
        self.add_field('date', './/li[@class="date"]/@title')
        self.add_field('genre', './/a[@class="rounded-label"]/@title')        
        self.add_field('program', './/div[@class="wrapper"]/a/@title')
        
        self.add_field('program_url', './/div[@class="wrapper"]/a/@href')
        
        self.add_field('guid', basefield='url', parser=IVooxParser.extract_code),
        self.add_field('xml', basefield = 'program_url',
                        parser=IVooxParser.guess_program_xml),


class IVooxPrograms(Scrapper):

    def declare_fields(self):
        self.add_field('name', './/meta[@itemprop="name"]/@content')
        self.add_field('url', './/meta[@itemprop="url"]/@content')
        self.add_field('description', './/meta[@itemprop="description"]/@content')
        self.add_field('audios', './/li[@class="microphone"]/a/text()',
                       parser=int, default=0)
        self.add_field('image', './/img[@class="main"]/@src')
        self.add_field('xml', basefield='url', parser=IVooxParser.guess_program_xml)


class IVooxShare(Scrapper):

    def declare_fields(self):
        self.add_field('code', '//a[@title="Facebook"]/@href', parser=IVooxParser.extract_code)
        self.add_field('xml', '//li[@class="list-group-item"][h3[@id="rss_suscribe"]]/input/@value', default='')

    def process_output(self, output):
        if not output:
            return None

        return output[0].get('xml') \
               or IVooxParser.guess_program_xml(output[0].get('code'))


class IVooxSubscriptions(Scrapper):

    share = IVooxShare()

    def declare_fields(self):
        self.add_field('name', './/a[@class="title"]/text()')
        self.add_field('image', './/img[@class="photo hidden-xs"]/@src')
        self.add_field('date', './/span[@class="date"]/text()',
                       parser=IVooxParser.date_from_fuzzy)
        self.add_field('new_audios', './/td[@class="td-sm"]/a[@class="circle-link"]/text()',
                       parser=int, default=0)
        self.add_field('xml', './/a[@class="share"]/@href',
                       parser=self.share.scrap)


class IVooxCategories(Scrapper):

    def __init__(self, main=True, **kwargs):
        self.main = main
        super(IVooxCategories, self).__init__(**kwargs)

    def declare_fields(self):
        container = 'div[@class="pills-container"]' if self.main \
            else 'ul[@class="nav nav-pills"]'

        self.add_field('name', './/{}//li/a/@title'.format(container))
        self.add_field('url', './/{}//li/a/@href'.format(container))
        self.add_field('code', basefield='url',
                       parser=IVooxParser.extract_code)

