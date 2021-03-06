from __future__ import unicode_literals

import logging
import pykka
import uritools
from mopidy import backend, models

from .client import IVooxClient
import ivooxapi


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

URI_SCHEME = 'podcast+ivoox'
URI_EXPLORE = {'uri': URI_SCHEME + ':explore', 'ES': 'Explorar', 'EN': 'Explore'}
URI_SUBS = {'uri': URI_SCHEME + ':subs', 'ES': 'Subscripciones', 'EN': 'Subscriptions'}
URI_LIST = {'uri': URI_SCHEME + ':list', 'ES': 'Listas', 'EN': 'Lists'}
URI_LIST_ITEMS = [
    {'uri': URI_LIST['uri'] + ':favorites', 'ES': 'Favoritos', 'EN': 'Starred'},
    {'uri': URI_LIST['uri'] + ':pending', 'ES': 'Escuchar mas tarde', 'EN': 'Listen later'},
    {'uri': URI_LIST['uri'] + ':home', 'ES': 'Recomendado', 'EN': 'Recommended'},
    {'uri': URI_LIST['uri'] + ':history', 'ES': 'Historial', 'EN': 'History'}
]


class IVooxBackend(pykka.ThreadingActor, backend.Backend):

    uri_schemes = [URI_SCHEME]

    def __init__(self, config, audio):
        super(IVooxBackend, self).__init__()
        self.library = IVooxLibraryProvider(config, self)


class IVooxLibraryProvider(backend.LibraryProvider):

    def __init__(self, config, backend):
        super(IVooxLibraryProvider, self).__init__(backend)

        self.config = config['podcast-ivoox']

        self.ivoox = IVooxClient(lang=self.config['lang'],
                                 country=self.config['country'])

        self.ivoox.login(
            user=self.config['username'],
            password=self.config['password']
        )
        logger.info('Logging in to %s : %s',
                    self.ivoox.baseurl,
                    'OK' if self.ivoox.user_logged() else 'NOT LOGGED')

        self.refresh()

    @property
    def root_directory(self):
        return models.Ref.directory(
            name='iVoox Podcasts',
            uri=URI_SCHEME + ':'
        )

    def browse(self, uri):
        logger.debug('Browsing URI: %s', uri)

        # Browsing Root Directory
        if uri == self.root_directory.uri:
            if self.ivoox.user_logged():
                # User is logged. Show custom menus and subscriptions
                menu = self._translate_menu(URI_EXPLORE, URI_LIST)
                subs = self._translate_programs(self.ivoox.get_subscriptions(),
                                                info_field='new_audios')
                return menu + subs
            else:
                # User not logged. Root URI shows explore categories
                uri = URI_EXPLORE['uri']

        subgenres, episodes, programs = ([], [], [])

        if uri.startswith(URI_LIST['uri']):
            try:
                _, _, code = uri.split(':', 3)
            except ValueError:
                # Lists menu
                menu = self._translate_menu(*URI_LIST_ITEMS)
                lists = self._translate_lists(self.ivoox.get_user_lists())
                return menu + lists

            episodes = self.ivoox.explore_list(code)

        elif uri.startswith(URI_EXPLORE['uri']):
            try:
                _, _, genre = uri.split(':', 3)
            except ValueError:
                genre = None

            subgenres = self.ivoox.get_categories(parent=genre) \
                if not genre or not genre.startswith('f4') else []
            episodes = self.ivoox.explore(category=genre, type='episodes')
            programs = self.ivoox.explore(category=genre, type='programs')

        else:
            logger.error('Invalid browse URI: %s', uri)
            return []

        return self._translate_categories(subgenres) \
            + self._translate_programs(programs) \
            + self._translate_episodes(episodes)

    def refresh(self, uri=None):
        self.ivoox.clear_cache()

    def lookup(self, uris):
        return []

    def search(self, query=None, uris=None, exact=False):
        return None

    def _make_podcast_uri(self, xml, ep_guid=None):
        if not xml:
            return None
        # Feeds use main URL, not localized
        baseurl = ivooxapi.get_baseurl()
        program = uritools.urijoin(baseurl, xml)
        episode = '#' + uritools.urijoin(baseurl, ep_guid) if ep_guid else ''
        return 'podcast+{}{}'.format(program, episode)

    def _translate_menu(self, *items):
        return [models.Ref.directory(
                    name=item[self.config['lang']],
                    uri=item['uri'])
                for item in items
        ]

    def _translate_episodes(self, items):
        return [models.Ref.track(
                    name=item['name'],
                    uri=self._make_podcast_uri(item['xml'], item['guid'])
                ) for item in items[0:self.config['max_episodes']]
        ]

    def _translate_programs(self, items, info_field=None):
        return [models.Ref.album(
                    name=item['name'] + (' ({})'.format(item[info_field])
                        if info_field and item.get(info_field) else ''),
                    uri=self._make_podcast_uri(item['xml'])
                ) for item in items[0:self.config['max_programs']]
        ]

    def _translate_categories(self, items):
        return [models.Ref.directory(
                    name=item['name'],
                    uri=URI_EXPLORE['uri'] + ':' + item['code']
                ) for item in items
        ]

    def _translate_lists(self, items):
        return [models.Ref.playlist(
                    name=item['name'],
                    uri=URI_LIST['uri'] + ':' + item['code']
                ) for item in items
        ]
