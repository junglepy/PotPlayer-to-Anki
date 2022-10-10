import re
from os import listdir
import hashlib
import cambridge_pars
import bert

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
        examples[n] = bold_keyword(p, example)
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


def bold_keyword(p, example):
    for m in p.finditer(example):
        s = m.start()
        e = m.end()
        example = example[:s]+'<b>'+example[s:e]+'</b>'+example[e:]
    return example


def create_description(word, word_json, synonyms, spec_examples=None, n_spec_ex=4):
    p = re.compile(word)
    synonyms_str = '<i><sub>~ '
    for syn in synonyms[:5]:
        synonyms_str += f'{syn}; '
    synonyms_str += '</sub></i>'
    if len(synonyms) > 5:
        synonyms_str += '<i><sub><details><summary>more synonyms:</summary><ul>'
        for syn in synonyms[5:]:
            synonyms_str += f'<li>{syn}</li>'
        synonyms_str += '</ul></details></i></sub>'

    examples_str = ''
    if spec_examples:
        examples_str = '<i><sub><ul>'
        for example in spec_examples[:n_spec_ex]:
            examples_str += f'<li>{example}</li>'
        examples_str += '</ul></i></sub>'
        if len(spec_examples) > n_spec_ex:
            examples_str += '<i><sub><details><summary>more:</summary><ul>'
            for example in spec_examples[n_spec_ex:]:
                examples_str += f'<li>{example}</li>'
            examples_str += '</ul></details></i></sub><br>'
    meaning = ''
    if isinstance(word_json['meaning'], dict) and len(word_json['meaning'])>0:
        for mean, examples in word_json['meaning'].items():
            meaning += f'<div><b>{mean}</b><br></div>'
            if len(examples) > 0:
                meaning += '<i><sub><details><summary>Examples:</summary><ul>'
                for example in examples:
                    example = bold_keyword(p, example)
                    meaning += f'<li>{example}</li>'
                meaning += '</ul></details></i></sub>'
        meaning += '<br><br>'
    elif isinstance(word_json['meaning'], str):
        meaning += f'<div><b>{word_json["meaning"]}</b><br></div>'
    else:
        meaning += '~'
    audio = ''
    if word_json['us_audio'] != '-':
            audio += f"[sound:{word_json['audio_filename']}]<br>"
    search_links = word_json['search_links']
    goog = search_links['google']
    yand = search_links['yandex']
    wiki = search_links['wiki']
    camb = search_links['camb']
    links = f'<br><sub><a href="{camb}">Camb</a>|<a href="{wiki}">Wiki</a>|<a href="{goog}">G</a>|<a href="{yand}">Y</a></sub>'
    
    anki_description = synonyms_str + examples_str + meaning + audio + links
    anki_import = f'{word}\t{anki_description}'
    
    return anki_import, anki_description
    

def anki_write(word, anki_file):
    word_cont = cambridge_pars.requests2json(word)
    special_examples = examples_from_subs(word)
    word_cont = bert.dictionary_sense_sorting(word, special_examples[0], word_cont)
    synonyms = bert.get_bert_ngram_synonyms(word, special_examples[0])
    anki, description = create_description(word, word_cont, synonyms, special_examples)
    print(synonyms)
    if word not in CHECKED_WORDS:
        with open(anki_file, 'a', encoding='utf-8') as out:
            out.write(anki + '\n')
        CHECKED_WORDS.add(word)
    return description