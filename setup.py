from __future__ import unicode_literals

import re

from setuptools import find_packages, setup


def get_version(filename):
    with open(filename) as fh:
        metadata = dict(re.findall("__([a-z]+)__ = '([^']+)'", fh.read()))
        return metadata['version']


setup(
    name='Mopidy-Podcast-IVoox',
    version=get_version('mopidy_podcast_ivoox/__init__.py'),
    url='https://github.com/ismailof/mopidy-podcast-ivoox',
    license='Apache License, Version 2.0',
    author='Ismael Asensio',
    author_email='ismailof@github.com',
    description='Mopidy extension for accessing IVoox podcasting platform',
    long_description=open('README.rst').read(),
    packages=find_packages(exclude=['tests', 'tests.*']),
    zip_safe=False,
    include_package_data=True,
    install_requires=[
        'setuptools',
        'Mopidy >= 1.0',
        'Mopidy-Podcast >= 2.0',
        'Pykka >= 1.1',
        'requests >= 2.0'
    ],
    entry_points={
        'mopidy.ext': [
            'podcast-ivoox = mopidy_podcast_ivoox:Extension',
        ],
    },
    classifiers=[
        'Environment :: No Input/Output (Daemon)',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2',
        'Topic :: Multimedia :: Sound/Audio :: Players',
    ],
)
