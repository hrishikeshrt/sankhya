#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Nov 22 01:41:14 2020

@author: Hrishikesh Terdalkar
"""

###############################################################################

import os

from utils.configuration import Configuration
from settings import application_settings

###############################################################################
# DO NOT EDIT

APP_DIR = application_settings['bhoota'].data_path

HOME_DIR = os.path.expanduser('~')
HELLWIG_DIR = os.path.join(
    HOME_DIR, 'git', 'oliverhellwig', 'papers', '2018emnlp', 'code'
)

###############################################################################

app = Configuration()

# Paths
app.dir = APP_DIR
app.hellwig_dir = HELLWIG_DIR
app.log_file = application_settings['bhoota'].log_path
app.list_file = os.path.join(APP_DIR, 'word_list.csv')
app.forms_file = os.path.join(APP_DIR, 'word_forms.csv')
app.example_file = os.path.join(APP_DIR, 'examples.txt')

###############################################################################
