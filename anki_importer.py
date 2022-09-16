import re
from os import listdir
import hashlib
import cambridge_pars

HASH_SUB = [0]
CHECKED_WORDS = set()

def clear_subs(text):
    if text.startswith('WEBVTT'):
        text = text[6:]
    text = re.sub('(^\d+\n\d{2}:\d{2}:[\d\s\.\->:,]+)|(^\n)', '', text, flags=re.MULTILINE)
    text = re.sub('\n', ' ', text)
    text = re.sub('(\s)+', ' ', text)
    return text


def examples_from_text(word, raw_text):
    # return re.findall(f'(?<=[\.!?])[^/.!?]+{word}[^/.!?]*',raw_text)
    return re.findall(f'[^/.!?]+{word}[^/.!?]*',raw_text)


def bold_spec_examples(word, examples):
    p = re.compile(word)
    for n, example in enumerate(examples):
        examples[n] = cambridge_pars.bold_keyword(p, example)
    return examples


def return_examples(word, text, n_e=8):
    delt = 200000
    if len(text) <= delt:
        examples = examples_from_text(word, text)
    else:
        examples = []
        s = 0
        e = len(text)
        slice_list = [curr for curr in range(s,e,delt)]
        slice_list[-1] = e

        for i, n in enumerate(slice_list[1:]):
            l = slice_list[i]
            r = n + 400
            examples += examples_from_text(word, text[l:r])
            if len(examples) >= n_e:
                break
    examples = list(set(examples))
    if len(examples) > n_e:
        examples = examples[:n_e]
    examples = bold_spec_examples(word, examples)
    
    return examples
    

def open_subs_file():
    files = listdir()
    for file in files:
        if file.endswith('en.srt') or file.endswith('en.vtt'):
            en_sub = file
    with open(en_sub, 'r', encoding='utf-8-sig') as txt:
        text = txt.read()
    return text
    
    
def examples_from_subs(word):
    subs = open_subs_file()
    if HASH_SUB[0] == hashlib.sha1(subs.encode('utf-8')).hexdigest():
    # if hashlib.sha1(subs).hexdigest() == HASH_SUB[0]:
        with open('text_from_subs.txt', 'r', encoding='utf-8') as txt:
            text = txt.read()
    else:
        text = clear_subs(subs)
        with open('text_from_subs.txt', 'w', encoding='utf-8') as txt:
            txt.write(text)
        HASH_SUB[0] = hashlib.sha1(subs.encode('utf-8')).hexdigest()
    
    examples = return_examples(word, text)
    return examples


def anki_write(word, anki_file):
    word_cont = cambridge_pars.requests2json(word)
    special_examples = examples_from_subs(word)
    anki, description = cambridge_pars.create_description(word, word_cont, special_examples)
    if word not in CHECKED_WORDS:
        with open(anki_file, 'a', encoding='utf-8') as out:
            out.write(anki + '\n')
        CHECKED_WORDS.add(word)
    return description