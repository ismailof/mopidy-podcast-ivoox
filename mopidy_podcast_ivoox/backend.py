from __future__ import unicode_literals

import logging
import pykka
from mopidy import backend, models

from .client import IVooxAPI

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

URI_SCHEME = 'podcast+ivoox'
URI_EXPLORE = {'uri': URI_SCHEME + ':explore',
               'ES': 'Explorar',
               'EN': 'Explore'}
URI_HOME = {'uri': URI_SCHEME + ':home',
            'ES': 'Recomendado',
            'EN': 'Recommended'}


class IVooxBackend(pykka.ThreadingActor, backend.Backend):

    uri_schemes = [URI_SCHEME]

    def __init__(self, config, audio):
        super(IVooxBackend, self).__init__()

        self.library = IVooxLibraryProvider(config, self)


class IVooxLibraryProvider(backend.LibraryProvider):

    def __init__(self, config, backend):
        super(IVooxLibraryProvider, self).__init__(backend)

        self.ivoox = IVooxAPI()

        ivoox_config = config['podcast-ivoox']

        self.lang = ivoox_config['lang']
        self.ivoox.set_language(self.lang)

        self.user_logged = self.ivoox.login(
            user=ivoox_config['username'],
            password=ivoox_config['password']
        )
        logger.info('User authorization in ivoox.com : %s',
                    'OK' if self.user_logged else 'NOT LOGGED')

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
            if self.user_logged:
                # User is logged. Show custom menus and subscriptions
                return [models.Ref.directory(name=item[self.lang],
                                             uri=item['uri'])
                           for item in (URI_EXPLORE, URI_HOME)
                        ] + self.subscriptions
            else:
                # User not logged. Root URI shows explore categories
                uri = URI_EXPLORE['uri']

        subgenres, episodes, programs = (None, None, None)

        if uri == URI_HOME['uri']:
            episodes = self.ivoox.get_home()

        elif uri.startswith(URI_EXPLORE['uri']):
            uri_parts = uri.split(':')
            genre = uri_parts[2] if len(uri_parts) > 2 else None

            subgenres = self.ivoox.get_categories(parent=genre) \
                if not genre or not genre.startswith('f4') else None
            episodes = self.ivoox.explore(category=genre, type='episodes')
            programs = self.ivoox.explore(category=genre, type='programs')

        else:
            logger.error('Invalid browse URI: %s', uri)
            return []

        return self._translate_categories(subgenres) \
            + self._translate_programs(programs) \
            + self._translate_episodes(episodes)

    def refresh(self, uri=None):
        results = self.ivoox.get_subscriptions()
        self.subscriptions = self._translate_programs(results)

    def search(self, query=None, uris=None, exact=False):
        pass

    @staticmethod
    def _translate_episodes(results):
        return [models.Ref.track(name=item['name'], uri=item['uri'])
                    for item in results.itemlist
                ] if results else []

    @staticmethod
    def _translate_programs(results):
        return [models.Ref.album(name=item['name'], uri=item['uri'])
                    for item in results.itemlist
                ] if results else []

    @staticmethod
    def _translate_categories(results):
        return [models.Ref.directory(
                    name=item['name'],
                    uri=URI_EXPLORE['uri'] + ':' + item['code']
                    ) for item in results.itemlist
                ] if results else []
