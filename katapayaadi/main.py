#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Aug 29 00:14:10 2019

@author: Hrishikesh Terdalkar
"""

import os
import json
import random
import logging
import progressbar

from collections import defaultdict
from aksharamukha import transliterate

from .settings import app
from .db import load_index, save_index

from utils.functions import find_ngrams, find_partitions, flatten
import utils.text.samskrit_text as samskrit
from utils.logger import setup_logger

setup_logger('main', log_file=app.log_file, append=True)
setup_logger('process_corpus', log_file=app.log_file, append=True)

log = logging.getLogger('main')

###############################################################################


def generate_mapping():
    groups = ['कखगघङचछजझञ', 'टठडढणतथदधन', 'पफबभम', 'यरलवशषसहळ']
    vowels = 'अआइईउऊऋॠऌॡएऐओऔ'

    _char = defaultdict(list)
    _num = {}

    for idx in range(10):
        number = str((idx + 1) % 10)
        for group in groups:
            try:
                _char[number].append(group[idx])
                _num[group[idx]] = number
            except IndexError:
                pass

    for vowel in vowels:
        _char['0'].append(vowel)
        _num[vowel] = '0'

    return _char, _num

###############################################################################


def setup():
    for required_dir in [app.dir, app.db_dir, app.data_dir]:
        if required_dir and not os.path.isdir(required_dir):
            os.makedirs(required_dir)

    load_index()

    try:
        with open(app.map_file, 'r') as f:
            app.chr, app.num = json.load(f)
    except Exception:
        app.chr, app.num = generate_mapping()
        with open(app.map_file, 'w') as f:
            json.dump((app.chr, app.num), f, ensure_ascii=False)
        log.info(f"Mapping file generated and saved to: {app.map_file}.")


###############################################################################
# Decode Functions


def decode_text(text, lang=app.language, explain=False, reverse=True):
    # reverse == True => Apply "अङ्कानाम् वामतो गतिः"
    script = app.languages[lang].script

    def to_deva(s):
        if script != 'Devanagari':
            s = transliterate.process(script, 'Devanagari', s)
        return s

    def from_deva(s):
        if script != 'Devanagari':
            s = transliterate.process('Devanagari', script, s)
        return s

    output = [
        decode_word(w, explain, reverse) for w in to_deva(text).split()
    ]
    if explain:
        if reverse:
            number = ''.join([x['katapayaadi'] for x in output[::-1]])
        else:
            number = ''.join([x['katapayaadi'] for x in output])

        for word in output:
            word['word'] = from_deva(word['word'])
            word['split'] = [from_deva(x) for x in word['split']]
            word['letters'] = [from_deva(x) for x in word['letters']]

        return number, output

    return ''.join(output[::-1]) if reverse else ''.join(output)


def decode_word(word, explain=False, reverse=True):
    # reverse == True => Apply "अङ्कानाम् वामतो गतिः"
    word = samskrit.clean(word)
    syllables = list(flatten(samskrit.get_syllables(word, True)))
    raw_letters = [s[0] if s[-1] != samskrit.HALANTA
                   and s[0] in samskrit.VYANJANA + samskrit.SWARA else ''
                   for s in syllables]
    raw_numbers = [app.num[c] if c else '' for c in raw_letters]

    if reverse:
        number = ''.join([str(n) for n in reversed(raw_numbers)])
    else:
        number = ''.join([str(n) for n in raw_numbers])

    if explain:
        return {
            'word': word,
            'split': syllables,
            'letters': raw_letters,
            'numbers': raw_numbers,
            'katapayaadi': number
        }

    return number

###############################################################################


def create_corpus(corpus_name, corpus_desc, corpus_lang=app.language):
    log.debug(f'create_corpus({corpus_name, corpus_desc, corpus_lang})')
    corpus_id = len(app.dictionary[corpus_lang]['corpus']) + 1
    app.dictionary[corpus_lang]['latest'] = False
    app.dictionary[corpus_lang]['corpus'][corpus_id] = [corpus_name,
                                                        corpus_desc]

    app.pending[corpus_lang][corpus_id] = {}
    app.pending[corpus_lang][corpus_id]['name'] = corpus_name
    app.pending[corpus_lang][corpus_id]['desc'] = corpus_desc
    app.pending[corpus_lang][corpus_id]['total'] = 100
    app.pending[corpus_lang][corpus_id]['current'] = 0

    return corpus_id


def process_corpus(corpus_id, corpus_lang=app.language):
    # CAUTION: The default is using reverse == True of decode_text
    # Figure out if that is an issue!
    # Mostly shouldn't be! We just need to reverse the number first!
    local_log = logging.getLogger('process_corpus')
    log.debug(f'process_corpus({corpus_lang}, {corpus_id})')

    app.in_progress[corpus_lang] = True
    file = os.path.join(app.data_dir, f'{corpus_lang}-corpus_{corpus_id}.txt')
    with open(file, 'r', encoding='utf-8-sig') as f:
        # content = samskrit.clean(f.read())
        content = f.read()

    terms = set()
    for line in content.split('\n'):
        for n in [1, 2, 3]:
            for term in find_ngrams(line, n, True):
                if term:
                    terms.add(term)

    max_value = len(terms)
    local_log.info(f'Terms: {max_value}')

    app.pending[corpus_lang][corpus_id]['total'] = max_value
    bar = progressbar.ProgressBar(max_value=max_value)

    for idx, term in enumerate(terms):
        number = decode_text(term, lang=corpus_lang)
        if number not in app.dictionary[corpus_lang]['encode']:
            app.dictionary[corpus_lang]['encode'][number] = defaultdict(set)
        app.dictionary[corpus_lang]['encode'][number][corpus_id].add(term)
        bar.update(idx)
        app.pending[corpus_lang][corpus_id]['current'] = idx

    local_log.info(f'Processed terms from corpus {corpus_lang}-{corpus_id}.')

    save_index(language=corpus_lang)
    del app.pending[corpus_lang][corpus_id]
    app.in_progress[corpus_lang] = False


def bulk_add(corpora):
    '''
    Bulk Process Corpora

    @params:
        corpora: [(corpus_name1, corpus_desc1, corpus_lang1, filepath), ..]
    '''
    for corpus_name, corpus_desc, corpus_lang, filepath in corpora:
        log.debug(f'BULK: {corpus_name}, {corpus_desc}, {corpus_lang}')
        corpus_id = create_corpus(corpus_name, corpus_desc, corpus_lang)
        process_corpus(corpus_id, corpus_lang)

###############################################################################


def get_terms(number, lang=app.language, corpus_ids=[]):
    if number not in app.dictionary[lang]['encode']:
        return []

    if corpus_ids:
        return [term for corpus_id in app.dictionary[lang]['encode'][number]
                for term in app.dictionary[lang]['encode'][number][corpus_id]
                if corpus_id in corpus_ids]
    else:
        return [term for corpus_id in app.dictionary[lang]['encode'][number]
                for term in app.dictionary[lang]['encode'][number][corpus_id]]


def get_corpus_list(lang=app.language):
    return [(corpus, detail[0], detail[1])
            for corpus, detail in app.dictionary[lang]['corpus'].items()]

###############################################################################
# Encode Functions


def encode_text(number, lang=app.language, corpus_ids=[], parts=0,
                minlength=1, limit=10, reverse=True):
    # reverse == True => Apply "अङ्कानाम् वामतो गतिः"
    log.debug(f'encode_text({number}, {lang}, {corpus_ids}, {parts}, '
              f'{minlength}, {limit})')

    number = str(number)
    length = len(number)

    max_parts = 7 if length < 14 else length/2

    options = []
    _boundaries = [1, 4, max_parts]
    _ranges = [range(_boundaries[x], _boundaries[x+1])
               for x in range(len(_boundaries) - 1)]
    _ranges = _ranges[parts:] + _ranges[:parts]
    parts_range = (idx for _range in _ranges for idx in _range)
    for num_parts in parts_range:
        splits = find_partitions(number, num_parts)
        for split in splits:
            if any([len(x) < 1 for x in split]):
                continue

            if all([get_terms(x, lang, corpus_ids) for x in split]):
                option = [random.sample(get_terms(x, lang, corpus_ids), 1)[0]
                          for x in split]
                if reverse:
                    options.append([' '.join(reversed(option)), split, option])
                else:
                    options.append([' '.join(option), split, option])
                if len(options) == limit:
                    return options
    return options

###############################################################################
