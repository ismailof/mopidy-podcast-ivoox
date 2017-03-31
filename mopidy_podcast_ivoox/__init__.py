from __future__ import unicode_literals

import logging
import os

from mopidy import config, ext
from .client import IVooxAPI

__version__ = '0.2.0'

logger = logging.getLogger(__name__)


class Extension(ext.Extension):

    dist_name = 'Mopidy-Podcast-IVoox'
    ext_name = 'podcast-ivoox'
    version = __version__

    def get_default_config(self):
        conf_file = os.path.join(os.path.dirname(__file__), 'ext.conf')
        return config.read(conf_file)

    def get_config_schema(self):
        schema = super(Extension, self).get_config_schema()
        # TODO: Comment in and edit, or remove entirely
        schema.update(
            username=config.String(optional=True),
            password=config.Secret(optional=True),
            lang=config.String(choices=IVooxAPI.LANGUAGES),
            country=config.String(choices=IVooxAPI.COUNTRIES),
            max_episodes=config.Integer(minimum=1, maximum=100),
            max_programs=config.Integer(minimum=1, maximum=100)
            )
        return schema

    def setup(self, registry):
        # TODO: Edit or remove entirely
        from .backend import IVooxBackend
        registry.add('backend', IVooxBackend)
