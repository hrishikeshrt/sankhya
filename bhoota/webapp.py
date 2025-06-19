#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Oct 24 23:56:49 2020

@author: Hrishikesh Terdalkar
"""
###############################################################################

import os
import logging

from .settings import app
from .main import encode_text, decode_text, WORD_LIST
from flask import Blueprint, request, render_template

from settings import application_settings

###############################################################################

# logging.basicConfig(format='[%(asctime)s] %(name)s %(levelname)s: %(message)s',
#                     datefmt='%Y-%m-%d %H:%M:%S',
#                     level=logging.INFO,
#                     handlers=[logging.FileHandler(app.log_file),
#                               logging.StreamHandler()])

###############################################################################

webapp = Blueprint('bhoota', __name__, template_folder='templates',
                   static_folder='static', url_prefix='/bhoota')

template_prefix = 'bhoota_'

###############################################################################


@webapp.route("/decode/", methods=['GET', 'POST'], strict_slashes=False)
def bhoota_number():
    data = {}
    data['title'] = 'Decode'
    if request.method == 'POST':
        data['text'] = request.form['input_text']
        data['answer'] = decode_text(data['text'])
    return render_template(template_prefix + 'decode.html', data=data)


@webapp.route("/encode/", methods=['GET', 'POST'], strict_slashes=False)
def bhoota_text():
    '''Find various word options for a given number'''
    data = {}
    data['title'] = 'Encode'
    if request.method == 'POST':
        data['number'] = request.form['input_number']

        if data['number']:
            data['answer'] = encode_text(data['number'])
    return render_template(template_prefix + 'encode.html', data=data)


@webapp.route("/help/", strict_slashes=False)
def bhoota_help():
    data = {}
    data['title'] = 'Help'
    return render_template(template_prefix + 'help.html', data=data)


@webapp.route("/examples", strict_slashes=False)
def bhoota_examples():
    data = {}
    data['title'] = 'Examples'
    example_file = os.path.join(
        application_settings['bhoota'].data_path, 'examples.txt'
    )
    with open(example_file, "r") as f:
        examples = [line for line in f.read().split('\n') if line]
    data['examples'] = examples
    return render_template(template_prefix + 'examples.html', data=data)


@webapp.route("/list", strict_slashes=False)
def bhoota_list():
    data = {}
    data['title'] = 'List'
    data['wordlist'] = WORD_LIST
    return render_template(template_prefix + 'list.html', data=data)


@webapp.route("/", strict_slashes=False)
def bhoota_home():
    data = {}
    data['title'] = 'About'
    return render_template(template_prefix + 'about.html', data=data)

###############################################################################
