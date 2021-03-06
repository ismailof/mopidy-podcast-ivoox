# -*- coding: utf8 -*-
from __future__ import unicode_literals, print_function

import datetime as dt

from scrapper import Scrapper


LANGUAGES = ['ES', 'EN']
COUNTRIES = ['ES', 'DE', 'AR', 'BR', 'CL', 'CO',
             'US', 'FR', 'IT', 'MX', 'PE', 'PT']

API_URLS = {
    'LOGIN': 'ajx-login_zl.html',
    'EXPLORE_EPISODES': 'audios_sa_{}_{}.html',
    'EXPLORE_PROGRAMS': 'podcasts_sc_{}_{}.html',
    'EXPLORE_LISTS': 'list_bk_list_{}_{}.html',
    'EXPLORE_CHANNELS': 'escuchar_nq_{}_{}.html',
    'SUBSCRIPTIONS': 'gestionar-suscripciones_je_1.html?order=date',
    'SEARCH_EPISODES': '{}_sb_{}.html',
    'SEARCH_PROGRAMS': '{}_sw_1_{}.html',
    'SEARCH_CHANNELS': '{}_sw_2_{}.html',
    'URL_EPISODE': '{1}-audios-mp3_rf_{0}_1.html',
    'URL_PROGRAM': 'podcast_sq_{}_1.html',
    'URL_CHANNEL': 'escuchar_nq_{}_1.html',
    'URL_AUDIO': 'listen_mn_{0}_1.mp3',
    'XML_PROGRAM': '{1}_fg_{0}.xml',  # '{1}_fg_{0}_filtro_1.xml' to allow pagination
    'LIST_INDEX': 'mis-listas_hk.html',
    'LIST_HOME': '',
    'LIST_PENDING': 'mis-audios_hn_{}.html',
    'LIST_FAVORITES': 'audios-que-me-gustan_hc_recomendados_{}.html',
    'LIST_HISTORY': 'audios-que-me-gustan_hc_{}.html'
}


def get_baseurl(lang='ES', country='ES'):
    assert lang in LANGUAGES, \
        "Language not supported: '{}'".format(lang)
    assert country in COUNTRIES, \
        "Country not supported: '{}'".format(country)

    prefix = 'www' if country == 'ES' else country.lower()
    suffix = '' if (lang, country) == ('ES', 'ES') else lang.lower() + '/'

    return 'http://{}.ivoox.com/{}'.format(prefix, suffix)


def format_url(item, *args):
    return API_URLS[item].format(*args)


def get_scrapper(type, **options):
    if type == 'episodes':
        scrapper = IVooxEpisodes(**options)
    elif type == 'programs':
        scrapper = IVooxPrograms(**options)
    elif type == 'subscriptions':
        scrapper = IVooxSubscriptions(**options)
    elif type == 'categories':
        scrapper = IVooxCategories(**options)
    elif type in ('lists', 'channels'):
        scrapper = IVooxSimpleItems(**options)
    else:
        raise KeyError('No scrapper for type %s', type)

    return scrapper


def parse_url_code(url):
    return url.split('_')[-2] if url else None


def parse_feed_xml(info, feed_name='podcast'):
    if info.endswith('.xml'):
        return info
    elif info.endswith('.html'):
        code = parse_url_code(info)
    else:
        code = info

    # subscription urls lack the first part of the code
    if not code.startswith('f1'):
        code = 'f1{}'.format(code)

    return format_url('XML_PROGRAM', code, feed_name)


def parse_duration(strtime):
    return sum(int(x) * 60 ** i
               for i, x in enumerate(reversed(strtime.split(":"))))


def parse_fuzzy_date(fuzzy_date):

    days_ago = lambda x: '{0:%d}-{0:%m}-{0:%Y}'.format(
        dt.date.today() - dt.timedelta(x))
    months_ago = lambda x: '{0:%m}-{0:%Y}'.format(
        dt.date.today() - dt.timedelta(x * 30))
    years_ago = lambda x: '{0:%Y}'.format(
        dt.date.today() - dt.timedelta(x * 365))
    parse_error = lambda x: x

    if not fuzzy_date:
        return None

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

    if date_word in ('día', 'días', 'day', 'days'):
        return days_ago(date_number)
    if date_word in ('semana', 'semanas', 'week', 'weeks'):
        return days_ago(date_number * 7)
    elif date_word in ('mes', 'meses', 'month', 'months'):
        return months_ago(date_number)
    elif date_word in ('año', 'años', 'year', 'years'):
        return years_ago(date_number)

    # Got here -> Parsing error
    return parse_error(fuzzy_date)


class IVooxEpisodes(Scrapper):

    def declare_fields(self):
        self.item_selector = './/div[@itemprop="episode"]'

        self.add_field('name', '/meta[@itemprop="name"]/@content')
        self.add_field('url', '/meta[@itemprop="url"]/@content')
        self.add_field('description', '/meta[@itemprop="description"]/@content')
        self.add_field('image', '//img[@class="main"]/@src')
        self.add_field('duration', '//p[@class="time"]/text()',
                       parser=parse_duration)
        self.add_field('date', '//li[@class="date"]/@title')
        self.add_field('genre', '//a[@class="rounded-label"]/@title')
        self.add_field('program', '//div[@class="wrapper"]/a/@title')
        self.add_field('program_url', '//div[@class="wrapper"]/a/@href')

        self.add_field('guid', basefield='url', parser=parse_url_code)
        self.add_field('xml', basefield = 'program_url',
                        parser=parse_feed_xml)
        self.add_field('mp3', basefield='guid',
                       parser=API_URLS['URL_AUDIO'].format)

class IVooxPrograms(Scrapper):

    def declare_fields(self):
        self.item_selector = './/div[@itemtype="http://schema.org/RadioSeries"]'

        self.add_field('name', '/meta[@itemprop="name"]/@content')
        self.add_field('url', '/meta[@itemprop="url"]/@content')
        self.add_field('description', '/meta[@itemprop="description"]/@content')
        self.add_field('audios', '//li[@class="microphone"]/a/text()',
                       parser=int, default=0)
        self.add_field('image', '//img[@class="main"]/@src')
        self.add_field('xml', basefield='url', parser=parse_feed_xml)


class IVooxSubscriptions(Scrapper):

    def declare_fields(self):
        self.item_selector = './/tr'

        self.add_field('name', '//a[@class="title"]/text()')
        self.add_field('image', '//img[@class="photo hidden-xs"]/@src')
        self.add_field('date', '//span[@class="date"]/text()',
                       parser=parse_fuzzy_date)
        self.add_field('new_audios', '//td[@class="td-sm"]/a[@class="circle-link"]/text()',
                       parser=int, default=0)
        self.add_field('xml', '//a[@class="share"]/@href',
                       parser=parse_feed_xml)


class IVooxCategories(Scrapper):

    def __init__(self, main=True, **kwargs):
        self.is_main = main
        super(IVooxCategories, self).__init__(**kwargs)

    def declare_fields(self):
        self.item_selector = './/div[@class="pills-container"]//li' if self.is_main \
            else './/ul[@class="nav nav-pills"]//li'

        self.add_field('name', '/a/@title')
        self.add_field('url', '/a/@href')
        self.add_field('code', basefield='url',
                       parser=parse_url_code)


class IVooxSimpleItems(Scrapper):

    def declare_fields(self):
        self.item_selector = './/div[@class="flip-container"]//div[@class="content"]'
        self.add_field('name', '//a/@title')
        self.add_field('url', '//a/@href')
        self.add_field('code', basefield='url',
                       parser=parse_url_code)


class CheckLogin(Scrapper):

    def declare_fields(self):
        self.item_selector = './/div[@id="main-navbar"]'
        self.add_field('user', '//a[@class="hidden-xs user dropdown-toggle text-ellipsis"]/span/text()')
