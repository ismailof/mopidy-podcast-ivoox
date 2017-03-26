****************************
Mopidy-Podcast-IVoox
****************************

.. image:: https://img.shields.io/pypi/v/Mopidy-Podcast-IVoox.svg?style=flat
    :target: https://pypi.python.org/pypi/Mopidy-Podcast-IVoox/
    :alt: Latest PyPI version

.. image:: https://img.shields.io/travis/ismailof/mopidy-podcast-ivoox/master.svg?style=flat
    :target: https://travis-ci.org/ismailof/mopidy-podcast-ivoox
    :alt: Travis CI build status

.. image:: https://img.shields.io/coveralls/ismailof/mopidy-podcast-ivoox/master.svg?style=flat
   :target: https://coveralls.io/r/ismailof/mopidy-podcast-ivoox
   :alt: Test coverage

Mopidy extension for accessing IVoox podcasting platform.

It provides access to the following capabilities:
   - explore iVoox podcasts directory
   - user subscribed podcasts (*requieres iVoox account*)
   - iVoox personal suggestions (*requires iVoox account*)
   - podcast search (*NOT YET IMPLEMENTED*) 

DISCLAIMER: This extension has no authorization from www.ivoox.com and is not meant for production use. 
It aims to help IVoox users to access their account favorite podcasts and subscriptions on those platforms 
where there is no official client, such as Raspberry PI devices.


Installation
============

Install by running::

    pip install https://github.com/ismailof/mopidy-podcast-ivoox/archive/master.zip



Configuration
=============

Before starting Mopidy, you must add configuration for
Mopidy-Podcast-IVoox to your Mopidy configuration file::

    [podcast-ivoox]
    lang = ES  #options: ES/EN
    country = ES  #options: ES/DE/US/UK/...
    username = user@email.com
    password = ivooxpassword

You can provide no user and password for an ivoox account, having only access to Explore and Search capabilities.

Default values for lang and country are ES/ES.


Project resources
=================

- `Source code <https://github.com/ismailof/mopidy-podcast-ivoox>`_
- `Issue tracker <https://github.com/ismailof/mopidy-podcast-ivoox/issues>`_


Credits
=======

- Original author: `Ismael Asensio <https://github.com/ismailof`__
- Current maintainer: `Ismael Asensio <https://github.com/ismailof`__
- `Contributors <https://github.com/ismailof/mopidy-podcast-ivoox/graphs/contributors>`_


Changelog
=========

v0.1.0 (UNRELEASED)
----------------------------------------
- Initial release.
