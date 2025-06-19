#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Jul 18 00:43:07 2020

@author: Hrishikesh Terdalkar
"""

import utils.text.samskrit_text as skt

###############################################################################


def generate_mapping():
    consonants_1 = 'कखगघङचछजझञटठडढणतथदधनपफबभम'
    consonants_2 = 'यरलवशषसह'
    vowel_groups = ['अआ', 'इई', 'उऊ', 'ऋॠ', 'ऌॡ', 'ए', 'ओ', 'ऐ', 'औ']

    _pow = {}
    _num_varga = {}
    _num_avarga = {}

    for idx, consonant in enumerate(consonants_1):
        number = idx + 1
        _num_varga[consonant] = number
        _num_varga[number] = consonant

    for idx, consonant in enumerate(consonants_2):
        number = 30 + 10 * idx
        _num_avarga[consonant] = number
        _num_avarga[number] = consonant

    for idx, vowels in enumerate(vowel_groups):
        for vowel in vowels:
            _pow[vowel] = idx * 2
            if idx * 2 not in _pow:
                _pow[idx * 2] = vowel

    return _num_varga, _num_avarga, _pow


###############################################################################

NUM_VARGA, NUM_AVARGA, POW = generate_mapping()

###############################################################################


def decode_text(s):
    values = []
    details = {'split': [], 'numbers': []}
    current = 0
    chars_ignore = skt.EXTRA_MATRA + skt.SPACES
    clean_s = ''.join([c for c in s if c not in chars_ignore])
    varna = skt.split_varna_word(clean_s, False)
    for v in varna:
        if v in skt.SWARA:
            zeroes = '0' * POW[v]
            values.append(str(current) + zeroes)
            current = 0
            details['split'].append(v)
            details['numbers'].append((10, POW[v]))
        else:
            if v[0] in NUM_VARGA:
                current += NUM_VARGA[v[0]]
                details['split'].append(v[0])
                details['numbers'].append((NUM_VARGA[v[0]],))
            if v[0] in NUM_AVARGA:
                current += NUM_AVARGA[v[0]]
                details['split'].append(v[0])
                details['numbers'].append((NUM_AVARGA[v[0]],))

    number = sum(int(n) for n in values)
    return number, details


def encode_text(number):
    options = []
    number = str(number)
    groups = [number[max(0, i-2):i] for i in range(len(number), 0, -2)]

    syllables_list = []

    for idx, group in enumerate(groups):
        number = int(group)
        power = idx * 2
        syllables = []
        if number == 0:
            continue
        elif 1 <= number <= 25:
            syllables = [NUM_VARGA[number] + skt.HALANTA,
                         POW[power]]
        elif number % 10 == 0:
            syllables = [NUM_AVARGA[number] + skt.HALANTA,
                         POW[power]]
        elif 25 < number < 30:
            smaller = number - 25
            syllables = [NUM_VARGA[smaller] + skt.HALANTA,
                         NUM_VARGA[25] + skt.HALANTA,
                         POW[power]]
        elif number >= 30:
            varga = number % 10
            avarga = number // 10 * 10
            syllables = [NUM_VARGA[varga] + skt.HALANTA,
                         POW[power],
                         NUM_AVARGA[avarga] + skt.HALANTA,
                         POW[power]]

        if syllables:
            syllables_list.append(syllables)
    options.append(" ".join(
        skt.join_varna(syllables) for syllables in syllables_list
    ))
    return options


###############################################################################

s1 = 'जल घिनि झुशु झृसृ खॢ'
n1 = 299792458
