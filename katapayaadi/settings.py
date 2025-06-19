#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Aug 29 00:10:26 2019

@author: Hrishikesh Terdalkar
"""

import os
from collections import namedtuple

from utils.configuration import Configuration
from settings import application_settings

Language = namedtuple('Language', ['code', 'name', 'script'])

###############################################################################
# DO NOT EDIT

APP_DIR = application_settings['katapayaadi'].data_path
DB_DIR = os.path.join(APP_DIR, 'db')

LANGUAGES = {
    'sa': Language('sa', 'Sanskrit', 'Devanagari'),
    'hi': Language('hi', 'Hindi', 'Devanagari'),
    'mr': Language('mr', 'Marathi', 'Devanagari'),
    'bn': Language('bn', 'Bangla', 'Bengali'),
    'ta': Language('ta', 'Tamil', 'Tamil'),
    'kn': Language('kn', 'Kannada', 'Kannada'),
    'te': Language('te', 'Telugu', 'Telugu'),
    'ml': Language('ml', 'Malayalam', 'Malayalam'),
    'gu': Language('gu', 'Gujarati', 'Gujarati')
}

DEFAULT_LANGUAGE = 'sa'

ALLOW_UPLOADS = False

###############################################################################

app = Configuration()

# Languages
app.languages = LANGUAGES
app.language = DEFAULT_LANGUAGE

# Paths
app.dir = APP_DIR
app.log_file = application_settings['katapayaadi'].log_path
app.map_file = os.path.join(APP_DIR, 'map.json')
app.example_file = os.path.join(APP_DIR, 'examples.txt')

#  Language dependant paths
app.db_dir = DB_DIR
app.index_file = lambda x: os.path.join(DB_DIR, f'{x}.pickle')
app.data_dir = os.path.join(APP_DIR, 'data')

# Uploads
app.allow_uploads = ALLOW_UPLOADS

# Track progress
app.pending = {x: {} for x in LANGUAGES}
app.in_progress = {x: False for x in LANGUAGES}


###############################################################################
