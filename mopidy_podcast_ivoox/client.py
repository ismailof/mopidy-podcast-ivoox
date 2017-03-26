#!/usr/bin/python
# -*- coding: iso-8859-15 -*-
from __future__ import unicode_literals, print_function

import logging
import requests
import datetime as dt

from scrapper import Scrapper

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

API_URLS = {
    'LOGIN': 'ajx-login_zl.html',    
    'EXPLORE_EPISODES': 'audios_sa_{}_{}.html',
    'EXPLORE_PROGRAMS': 'podcasts_sc_{}_{}.html',
    'SUBSCRIPTIONS': 'gestionar-suscripciones_je_1.html?order=date',
    'SEARCH_EPISODES': '{}_sb.html',
    'SEARCH_PROGRAMS': '{}_sw_1_{}.html',
    'SEARCH_CHANNELS': '{}_sw_2_{}.html',
    'URL_EPISODE': '{1}-audios-mp3_rf_{0}_1.html',
    'URL_PROGRAM': 'podcast_sq_{}_1.html',
    'URL_CHANNEL': 'escuchar_nq_{}_1.html',
    'XML_PROGRAM': '{1}_fg_{0}_filtro_1.xml',
}

            
class IVooxAPI(object):
    
    API_BASE = 'http://www.ivoox.com/'
    
    def __init__(self):
        super(IVooxAPI, self).__init__()
        self.session = None

    def set_language(self, lang='ES'):
        if lang != 'ES':
            self.API_BASE += lang + '/'
        
    def login(self, user, password):        
        if not (user and password):
            return False
        
        self.session = requests.session()        
        
        try:
            self.session.get(self.API_BASE + API_URLS['LOGIN'])            
            self.session.post(
                self.API_BASE + API_URLS['LOGIN'], 
                data={
                    'at-user': user,
                    'at-pw': password,
                    'redir': self.API_BASE
                }
            )
            # TODO: Check login is OK
            return True
            
        except Exception as ex:
            logger.error('Login error on %s: %s', self.API_BASE, ex)
            return False

    def get_categories(self, parent=None):
        parent = parent or 'f'
        explore_url = API_URLS['EXPLORE_EPISODES'].format(parent, 1)
        
        return self.scrap_url(
            url=explore_url,
            scrapper = IVooxCategories(
                main=(parent == 'f'), 
                session=self.session)
            )

    def get_subscriptions(self):
        return self.scrap_url(
            url=API_URLS['SUBSCRIPTIONS'],
            type='subscriptions'
            )
            
    def get_suggestions(self):
        return self.scrap_url(url='', type='episodes')              
    
    def explore(self, category=None, type='episodes', page=1):
        explore_url = API_URLS['EXPLORE_{}'.format(type).upper()]        
        
        return self.scrap_url(
            url=explore_url.format(category or 'f', page),
            type=type
            )
            
    def search(self, search_item, type='episodes', page=1):
        search_string = '-'.join(search_item.split()).lower()
        search_url = API_URLS['SEARCH_{}'.format(type).upper()]        
    
        return self.scrap_url(
            url=search_url.format(search_string, page),
            type=type
            )


    def scrap_url(self, url, type=None, scrapper=None):

        if not url.startswith('http://'):
            url = self.API_BASE + url
    
        if scrapper is None:
            if type == 'episodes':
                scrapper = IVooxEpisodes(session=self.session)
            elif type == 'programs':
                scrapper = IVooxPrograms(session=self.session)
            elif type == 'subscriptions':
                scrapper = IVooxSubscriptions(session=self.session)
                
        logger.debug('Using %s to analize %s', scrapper.__class__.__name__, url)

        scrapper.scrap(url)
        
        return scrapper
        
        
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

        if not url.endswith('.html'):
            # Code is first parameter
            code = url
            name = 'podcast'
        else:
            code = IVooxParser.extract_code(url)
            name = 'podcast'

        # arreglar después para multiidioma
        return 'http://www.ivoox.com/' + API_URLS['XML_PROGRAM'].format(code, name)
      
    @staticmethod
    def compose_podcast_uri(program_info, ep_guid=None):
        
        podcast_uri = 'podcast+{program_xml}'
        if ep_guid:
            podcast_uri += '#{baseurl}{ep_guid}'
        
        return podcast_uri.format(
            #baseurl=API_BASE,
            baseurl='http://www.ivoox.com/', # arreglar después para multiidioma
            program_xml=IVooxParser.guess_program_xml(program_info),
            ep_guid=ep_guid
        )

    @staticmethod
    def extract_duration(strtime):
        return sum(int(x) * 60 ** i \
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
        self.add_field('name', './/meta[@itemprop="name"]/@content')
        self.add_field('url', './/meta[@itemprop="url"]/@content')
        self.add_field('guid', basefield='url', parser=IVooxParser.extract_code),        
        self.add_field('image', './/img[@class="main"]/@src')
        self.add_field('duration', './/p[@class="time"]/text()', 
                       parser=IVooxParser.extract_duration)
        self.add_field('date', './/li[@class="date"]/@title')
        self.add_field('genre', './/a[@class="rounded-label"]/@title')
        self.add_field('description', './/meta[@itemprop="description"]/@content') 
        self.add_field('program', './/div[@class="wrapper"]/a/@title')
        self.add_field('program_url', './/div[@class="wrapper"]/a/@href')                
        # self.add_field('program_xml', basefield = 'program_url',
                       # parser=IVooxParser.guess_program_xml),
        self.add_field('uri', basefield=['program_url', 'guid'],
                       parser=IVooxParser.compose_podcast_uri)
                        
class IVooxPrograms(Scrapper):

    def declare_fields(self):
        self.add_field('name', './/meta[@itemprop="name"]/@content')
        self.add_field('url', './/meta[@itemprop="url"]/@content')
        self.add_field('description', './/meta[@itemprop="description"]/@content')
        self.add_field('audios', './/li[@class="microphone"]/a/text()',
                       parser=int, default=0)
        self.add_field('image', './/img[@class="main"]/@src')
        #self.add_field('code', basefield='url', parser=IVooxParser.extract_code)
        #self.add_field('xml', basefield='url', parser=IVooxParser.guess_program_xml)
        self.add_field('uri', basefield='url',
                       parser=IVooxParser.compose_podcast_uri)
        
class IVooxShare(Scrapper):

    def declare_fields(self): 
        self.add_field('code', '//a[@title="Facebook"]/@href', parser=IVooxParser.extract_code)
        self.add_field('xml', '//li[@class="list-group-item"][h3[@id="rss_suscribe"]]/input/@value', default='')        
            
    def process_output(self, output):
        if not output:
            return None
            
        return (output[0].get('xml')
                or IVooxParser.guess_program_xml(output[0].get('code')))


class IVooxSubscriptions(Scrapper):

    share = IVooxShare()

    def declare_fields(self):
        self.add_field('name', './/a[@class="title"]/text()')
        self.add_field('image', './/img[@class="photo hidden-xs"]/@src')        
        self.add_field('date', './/span[@class="date"]/text()',
                       parser=IVooxParser.date_from_fuzzy)
        self.add_field('new_audios', './/td[@class="td-sm"]/a[@class="circle-link"]/text()',
                       parser = int, default = 0)
        self.add_field('xml', './/a[@class="share"]/@href',
                       parser=self.share.scrap)

        self.add_field('uri', basefield='xml',
                       parser=IVooxParser.compose_podcast_uri)
  

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
