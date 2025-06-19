#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Nov 22 01:27:52 2020

@author: Hrishikesh Terdalkar
"""

###############################################################################

import os
import re
import sys
import random
import itertools
import functools
from collections import defaultdict

import pandas as pd

from .settings import app
from utils.sandhi.sandhi import sandhi

###############################################################################
# Sandhi Related

from indic_transliteration.sanscript import transliterate
import tensorflow.compat.v1 as tf
tf.disable_v2_behavior()

sys.path.insert(0, app.hellwig_dir)

import configuration, helper_functions, data_loader

app.sandhi_config = configuration.config
app.sandhi_data = data_loader.DataLoader(
    os.path.join(app.hellwig_dir, '../data/input'),
    app.sandhi_config,
    load_data_into_ram=True,
    load_data=False
)
graph_pred = tf.Graph()
with graph_pred.as_default():
    app.sess = tf.Session(graph=graph_pred)
    model_dir = model_dir = os.path.normpath(
        os.path.join(app.hellwig_dir, app.sandhi_config['model_directory'])
    )
    tf.saved_model.loader.load(
        app.sess,
        [tf.saved_model.tag_constants.SERVING],
        model_dir
    )
    print('OK')

    app.x_ph = graph_pred.get_tensor_by_name('inputs:0')
    app.split_cnts_ph = graph_pred.get_tensor_by_name('split_cnts:0')
    app.dropout_ph = graph_pred.get_tensor_by_name('dropout_keep_prob:0')
    app.seqlen_ph = graph_pred.get_tensor_by_name('seqlens:0')
    app.predictions_ph = graph_pred.get_tensor_by_name('predictions:0')

###############################################################################

MAX_CACHE = 1024

###############################################################################


def sandhi_all(words):
    answer = ''
    for word in words:
        answer = sandhi(answer, word)
    return answer


@functools.lru_cache(MAX_CACHE)
def split(input_text):
    path_in = "/tmp/input_sandhied"
    path_out = "/tmp/output_unsandhied"
    with open(path_in, "w") as f:
        f.write(transliterate(input_text, 'devanagari', 'iast'))
    helper_functions.analyze_text(
        path_in,
        path_out,
        app.predictions_ph,
        app.x_ph,
        app.split_cnts_ph,
        app.seqlen_ph,
        app.dropout_ph,
        app.sandhi_data,
        app.sess,
        verbose=False
    )
    with open(path_out) as f:
        output_text = transliterate(f.read(), 'iast', 'devanagari')
    return output_text


###############################################################################


BHOOTA_MAP = pd.read_csv(
    app.list_file, na_filter=None
).to_dict(orient='list')
BHOOTA_REV = defaultdict(list)

for k, v in BHOOTA_MAP.items():
    BHOOTA_MAP[k] = [i for i in set(v) if i]
    for w in v:
        BHOOTA_REV[w].append(k)
BHOOTA_REV = dict(BHOOTA_REV)

WORD_LIST = {
    k: [_v for _v in v if _v]
    for k, v in pd.read_csv(
        app.list_file, na_filter=None
    ).to_dict(orient='list').items()
}

WORD_FORMS = pd.read_csv(
    app.forms_file, na_filter=None, index_col=0
).to_dict(orient='index')

###############################################################################

'''
# Generate Forms

from mophology_generater import generate

words = []
for word in BHOOTA_REV:
    forms = {}
    for gender in ['m', 'f', 'n']:
        try:
            _forms = generate(word, gender)
            if len(_forms) >= 2:
                forms[gender] = _forms[1][2:]
        except Exception:
            pass
    words.append((word, forms))

csv = []
for word, forms in words:
    for gender, _forms in forms.items():
        csv.append([word] + _forms + [gender])

with open('forms.csv', 'w') as f:
    f.write('\n'.join([','.join(w) for w in csv]))
'''

###############################################################################


def get_words(numbers, max_options=10):
    options = []
    for i in range(max_options):
        words = []
        for number in numbers:
            words.append(
                random.choice(BHOOTA_MAP[number])
                if number in BHOOTA_MAP
                else number
            )
        if words not in options:
            options.append(words)
    return options


def split_words(text, is_split=False):
    split_output = text if is_split else split(text)
    words = [w for w in re.split(r'[-=\s]', split_output) if w]

    final_words = []
    skip = False
    for idx, word in enumerate(words):
        if skip:
            skip = False
            continue
        try:
            next_word = words[idx + 1]
            longer_word = sandhi(word, next_word)
            if longer_word in BHOOTA_REV:
                final_words.append(longer_word)
                skip = True
                continue
        except IndexError:
            pass
        final_words.append(word)

    for root, forms in WORD_FORMS.items():
        if final_words[-1] in [forms['sg'], forms['du'], forms['pl']]:
            final_words[-1] = root
            break

    return final_words


def get_numbers(words):
    numbers = []
    for word in words:
        options = BHOOTA_REV.get(word, [word])
        numbers.append(options)
    return list(itertools.product(*numbers))

###############################################################################


def encode_text(number):
    number = str(number)
    partitions = [
        [number[0+i:2+i] for i in range(0, len(number), 2)],
        [number[0]] + [number[1:][0+i:2+i] for i in range(0, len(number), 2)]
    ]
    final_partitions = []
    min_idx = 0
    min_length = None

    current_idx = 0
    # find a partition such that all members of the group exist
    # and number of groups is minimal
    for partition in partitions:
        current_partition = []
        current_length = 0
        for group in partition:
            if not group:
                continue
            if group in BHOOTA_MAP:
                current_length += 1
                current_partition.append(group)
            else:
                # assumes that all single digits exist, which is generally true
                current_length += 2
                current_partition.append(group[0])
                current_partition.append(group[1])

        if min_length is None or current_length < min_length:
            min_length = current_length
            min_idx = current_idx

        final_partitions.append(current_partition)
        current_idx += 1

    final_partition = final_partitions[min_idx]
    options = get_words(final_partition)
    texts = []
    for words in options:
        reversed_words = words[::-1]
        target_form = 'pl'
        if len(words) == 1 and number == 1:
            target_form = 'sg'
        if len(words) == 1 and number == 2:
            target_form = 'du'
        reversed_words[-1] = WORD_FORMS[reversed_words[-1]][target_form]
        texts.append(sandhi_all(reversed_words))
    answer = {
        'number': number,
        'partition': final_partition,
        'options': options,
        'texts': texts
    }

    return answer


def decode_text(text, is_split=False):
    words = split_words(text, is_split=is_split)
    options = get_numbers(words)
    answer = {
        'text': text,
        'split': words,
        'options': options,
        'numbers': [''.join(number[::-1]) for number in options]
    }
    return answer


###############################################################################
