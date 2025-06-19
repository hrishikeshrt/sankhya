#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Aug 29 02:31:27 2019

@author: Hrishikesh Terdalkar
"""
import socket
import logging
import threading

from .settings import app
from .main import (setup, decode_text, create_corpus, process_corpus,
                   get_corpus_list, encode_text)

from flask import (Blueprint, Response, request, render_template,
                   redirect, url_for)

from flask_uploads import UploadSet, TEXT

texts = UploadSet('texts', TEXT)

###############################################################################

logging.basicConfig(format='[%(asctime)s] %(name)s %(levelname)s: %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    level=logging.INFO,
                    handlers=[logging.FileHandler(app.log_file),
                              logging.StreamHandler()])

###############################################################################

setup()

###############################################################################

webapp = Blueprint('katapayaadi', __name__, template_folder='templates',
                   static_folder='static', url_prefix='/katapayaadi')

###############################################################################

VARIANTS = {
    'variant-1': 'Sadratnamālā Variant',
    'variant-4': 'Kerala Variant'
}
DEFAULT_VARIANT = 'variant-1'

###############################################################################


def process_pending_uploads(lang=app.language):
    if app.in_progress[lang]:
        return False
    if app.pending and app.pending[lang]:
        process_corpus(list(app.pending[lang])[0], corpus_lang=lang)
        process_pending_uploads(lang)
    return True

###############################################################################


@webapp.route("/progress/", strict_slashes=False)
@webapp.route("/progress/<string:lang>/", strict_slashes=False)
def progress(lang=app.language):
    if lang not in app.languages:
        return redirect(url_for('katapayaadi.progress'))
    _progress = []
    for cid, details in app.pending[lang].items():
        percentage = (details['current'] * 100)//details['total']
        _progress.append([cid, percentage])

    return Response(f"data:{_progress}\n\n", mimetype='text/event-stream')


@webapp.route("/upload/", methods=['GET', 'POST'], strict_slashes=False)
@webapp.route("/upload/<string:lang>/", methods=['GET', 'POST'],
              strict_slashes=False)
def katapayaadi_upload(lang=app.language):
    if lang not in app.languages:
        return redirect(url_for('katapayaadi.katapayaadi_upload'))
    data = {}
    data['title'] = 'Upload Corpus'
    data['languages'] = app.languages
    data['pending'] = app.pending[lang]

    if not app.allow_uploads:
        data['warning'] = 'Upload feature is currently disabled.'
        return render_template('upload.html', data=data, lang=lang)

    if request.method == 'POST' and 'corpus_file' in request.files:
        corpus_name = request.form['corpus_name']
        corpus_desc = request.form['corpus_desc']
        corpus_id = create_corpus(corpus_name, corpus_desc, lang)
        texts.save(request.files['corpus_file'],
                   name=f'{lang}-corpus_{corpus_id}.txt')

        # webapp.logger.info(f'UPLOAD: {lang}, {corpus_name} '
        #                    f'(ID: {corpus_id}).')
        threading.Thread(target=process_pending_uploads,
                         args=(lang,)).start()

    return render_template('upload.html', data=data, lang=lang)


@webapp.route("/decode/", methods=['GET', 'POST'], strict_slashes=False)
@webapp.route("/decode/<string:lang>/", methods=['GET', 'POST'],
              strict_slashes=False)
def katapayaadi_number(lang=app.language):
    if lang not in app.languages:
        return redirect(url_for('katapayaadi.katapayaadi_number'))
    data = {}
    data['title'] = 'Decode'
    data['languages'] = app.languages
    data['variants'] = VARIANTS
    data['variant'] = DEFAULT_VARIANT
    if request.method == 'POST':
        data['text'] = request.form['input_text']
        data['variant'] = request.form['variant']
        data['reverse'] = data['variant'] in ['variant-1']
        data['number'], data['details'] = decode_text(
            data['text'],
            lang=lang,
            explain=True,
            reverse=data['reverse']
        )
        # webapp.logger.info(f"DECODE: {lang}, {data['text']} --> "
        #                    f"{data['number']}")
    return render_template('decode.html', data=data, lang=lang)


@webapp.route("/encode/", methods=['GET', 'POST'], strict_slashes=False)
@webapp.route("/encode/<string:lang>/", methods=['GET', 'POST'],
              strict_slashes=False)
def katapayaadi_text(lang=app.language):
    '''Find various word options for a given number'''
    if lang not in app.languages:
        return redirect(url_for('katapayaadi.katapayaadi_text'))
    data = {}
    data['title'] = 'Encode'
    data['languages'] = app.languages
    data['corpora'] = get_corpus_list(lang)
    data['corpus_ids'] = []
    data['variants'] = VARIANTS
    data['variant'] = DEFAULT_VARIANT
    if request.method == 'POST':
        data['number'] = request.form['input_number']
        data['variant'] = request.form['variant']
        data['reverse'] = data['variant'] in ['variant-1']

        # data['limit'] = request.form['limit']
        data['corpus_ids'] = list(map(int, request.form.getlist('corpus_ids')))
        data['parts'] = int(request.form['components'])

        if data['number']:
            # NOTE: Our default index is reverse,
            # so if reverse == False, we first invert number!
            data['options'] = encode_text(
                data['number'] if data['reverse'] else data['number'][::-1],
                lang=lang,
                corpus_ids=data['corpus_ids'],
                parts=data['parts'],
                reverse=data['reverse']
            )

            # webapp.logger.info(f"ENCODE: {lang}, {data['number']} -->\n"
            #                    f"{data['options']}")

    return render_template('encode.html', data=data, lang=lang)


@webapp.route("/help/", strict_slashes=False)
@webapp.route("/help/<string:lang>/", strict_slashes=False)
def katapayaadi_help(lang=app.language):
    if lang not in app.languages:
        return redirect(url_for('katapayaadi.katapayaadi_help'))
    data = {}
    data['title'] = 'Help'
    data['languages'] = app.languages
    return render_template('help.html', data=data, lang=lang)


@webapp.route("/examples/", strict_slashes=False)
@webapp.route("/examples/<string:lang>/", strict_slashes=False)
def katapayaadi_examples(lang=app.language):
    if lang not in app.languages:
        return redirect(url_for('katapayaadi.katapayaadi_examples'))
    data = {}
    data['title'] = 'Examples'
    data['languages'] = app.languages
    with open(app.example_file, "r") as f:
        examples = [line for line in f.read().split('\n') if line]
    data['examples'] = examples
    return render_template('examples.html', data=data, lang=lang)


@webapp.route("/", strict_slashes=False)
@webapp.route("/<string:lang>/", strict_slashes=False)
def katapayaadi_home(lang=app.language):
    if lang not in app.languages:
        return redirect(url_for('katapayaadi.katapayaadi_home'))
    data = {}
    data['title'] = 'About'
    data['languages'] = app.languages
    return render_template('about.html', data=data, lang=lang)


###############################################################################
