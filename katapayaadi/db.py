#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Aug 28 23:39:16 2019

@author: Hrishikesh Terdalkar
"""

import os
import pickle

from .settings import app

import logging
from utils.logger import setup_logger

setup_logger('index', log_file=app.log_file, append=True)
log = logging.getLogger('index')

###############################################################################


def load_index(language=None):
    if 'dictionary' not in app:
        app.dictionary = {}

    languages = app.languages if language is None else [language]
    for lang in languages:
        if os.path.isfile(app.index_file(lang)):
            with open(app.index_file(lang), 'rb') as f:
                lang_dict = pickle.load(f)
                app.dictionary[lang] = lang_dict
            if 'latest' not in app.dictionary[lang]:
                app.dictionary[lang]['latest'] = False
                save_index(language=lang)
            log.info(f"Loaded '{lang}'")
        else:
            app.dictionary[lang] = {}
            app.dictionary[lang]['corpus'] = {}
            app.dictionary[lang]['encode'] = {}
            app.dictionary[lang]['latest'] = False
            log.info(f"Initiated '{lang}'")


def save_index(language=None):
    if 'dictionary' not in app:
        log.error('No dictionary to save.')
        return
    else:
        languages = app.languages if language is None else [language]
        for lang in languages:
            if lang not in app.dictionary:
                log.warning(f'No dictionary to save for language: {lang}.')
                continue
            if not app.dictionary[lang]['latest']:
                # mark as latest and save
                app.dictionary[lang]['latest'] = True
                with open(app.index_file(lang), 'wb') as f:
                    pickle.dump(app.dictionary[lang], f)

###############################################################################
