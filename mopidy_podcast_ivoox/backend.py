from __future__ import unicode_literals

import logging
import pykka
import uritools
from mopidy import backend, models

from .client import IVooxAPI

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

URI_SCHEME = 'podcast+ivoox'
URI_EXPLORE = {'uri': URI_SCHEME + ':explore', 'ES': 'Explorar', 'EN': 'Explore'}
URI_HOME = {'uri': URI_SCHEME + ':home', 'ES': 'Recomendado', 'EN': 'Recommended'}
URI_LISTS = {'uri': URI_SCHEME + ':list', 'ES': 'Listas', 'EN': 'Lists'}
URI_FAVORITES = {'uri': URI_LISTS['uri'] + ':favorites', 'ES': 'Favoritos', 'EN': 'Starred'}
URI_PENDING = {'uri': URI_LISTS['uri'] + ':pending', 'ES': 'Escuchar mas tarde', 'EN': 'Listen later'}


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
                menu = [models.Ref.directory(
                            name=item[self.lang],
                            uri=item['uri'])
                        for item in (URI_EXPLORE,
                                     URI_HOME,
                                     URI_FAVORITES,
                                     URI_PENDING)]
                subs = self._translate_programs(self.ivoox.get_subscriptions(),
                                                info_field='new_audios')
                return menu + subs
            else:
                # User not logged. Root URI shows explore categories
                uri = URI_EXPLORE['uri']

        subgenres, episodes, programs = ([], [], [])

        if uri == URI_HOME['uri']:
            episodes = self.ivoox.get_home()

        elif uri.startswith(URI_LISTS['uri']):
            _, _, listname = uri.split(':')
            episodes = self.ivoox.get_episode_list(listname)

        elif uri.startswith(URI_EXPLORE['uri']):
            try:
                _, _, genre = uri.split(':')
            except ValueError:
                genre = None

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
        self.ivoox.clear_cache()

    def lookup(self, uris):
        pass

    def search(self, query=None, uris=None, exact=False):
        pass

    def _translate_podcast_uri(self, xml, ep_guid=None):
        if not xml:
            return None
        baseurl = self.ivoox.baseurl
        program = uritools.urijoin(baseurl, xml)
        episode = '#' + uritools.urijoin(baseurl, ep_guid) if ep_guid else ''
        return 'podcast+{}{}'.format(program, episode)

    def _translate_episodes(self, results):
        return [models.Ref.track(
                    name=item['name'],
                    uri=self._translate_podcast_uri(item['xml'], item['guid'])
                ) for item in results]

    def _translate_programs(self, results, info_field=None):
        return [models.Ref.album(
                    name=item['name'] + (' ({})'.format(item[info_field])
                        if info_field and item.get(info_field) else ''),
                    uri=self._translate_podcast_uri(item['xml'])
                ) for item in results]

    def _translate_categories(self, results):
        return [models.Ref.directory(
                    name=item['name'],
                    uri=URI_EXPLORE['uri'] + ':' + item['code']
                ) for item in results]
