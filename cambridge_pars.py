import requests
import json
import random
import re
from time import sleep
from lxml import html, etree
import wikipedia as wiki
from wikipedia import PageError,DisambiguationError
from collections import OrderedDict
media_folder = '/home/junglepy/snap/anki-ppd/common/anki/User 1/collection.media/' # Linux
media_folder = r"C:/Users/Eduard/AppData/Roaming/Anki2/User 1/collection.media2/" #W10 TODO!!!

#adding examples of word usage from subs, arxiv, article or other processed text
EXAMPLES_FROM_TEXT = True
#number of word meanings from the cambridge dictionary
N_MEANINGS = 2
#the number of examples of word usage in different contexts
N_EXAMPLES = 2

#http://login:pass@255.255.255.255:port proxy pattern
proxy_list = []


headers_list = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.69 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:93.0) Gecko/20100101 Firefox/93.0',
    
]

DOMAIN = 'https://dictionary.cambridge.org'
URL_S = 'https://dictionary.cambridge.org/dictionary/english/'
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:93.0) Gecko/20100101 Firefox/93.0'}
s = requests.Session()
s.headers.update(HEADERS)


def change_headers():
    useragent = random.choice(headers_list)
    header = {'User-Agent': useragent}
    s.headers.update(header)
    proxy = random.choice(proxy_list)
    proxies = {'https': proxy}
    s.proxies.update(proxies)

    
def get_html(url, params=None, n_try=0):
    try:
        resp = s.get(url, params=params)
    except:
        sleep(2)
        n_try += 1
        change_headers()
        if n_try > 5:
            print('req_get, resp.status_code =', resp.status_code)
            print(resp.content)
            return None
        return get_html(url, params, n_try)
    if resp.status_code != 200:
        sleep(2)
        n_try += 1
        change_headers()
        if n_try > 5:
            print('req_get, resp.status_code =', resp.status_code)
            print(resp.content)
            return None
        return get_html(url, params, n_try)
    return resp


def html_data(word):
    data = get_html(URL_S + word)
    tree = html.fromstring(data.content)
    tree = html.fromstring(html.tostring(tree, encoding='unicode'))
    return tree

# Download from CambridgeDictionary

# Get Words from Anki's export


def get_content(word):
    return html_data(word)


def download(url, file_name):
    if url == '-':
        return
    # open in binary mode
    file_name = media_folder + file_name
    with open(file_name, "wb") as file:
        # get request
        response = s.get(url)
        # write to file
        file.write(response.content)

        
def get_meanings(content):
    word_meanings = OrderedDict()
    big_blocks = content.xpath('//div[@class="def-block ddef_block "]')
    for i, block in enumerate(big_blocks):
        if i >= N_MEANINGS:
            break
        block = html.fromstring(html.tostring(block, encoding='unicode'))
        # Add meaning
        meaning_raw = block.xpath('//div[@class="ddef_h"]//div[@class="def ddef_d db"]')
        meaning = ''.join(meaning_raw[0].itertext()).removesuffix(': ')
        # Add examples
        examples = []
        for n_examp in range(N_EXAMPLES):
            try:
                examples_raw = block.xpath('//div[@class="def-body ddef_b"]//div[@class="examp dexamp"]')
                cur_example = ''.join(examples_raw[n_examp].itertext()).strip()
                examples.append(cur_example)
            except IndexError:
                break
        # Add pair to main dict
        word_meanings[meaning] = examples
    return word_meanings


def get_audio(content):
    try:
        us_audio = DOMAIN + content.xpath('.//span[@class="us dpron-i "]//source[@type="audio/mpeg"]/@src')[0]
        gb_audio = DOMAIN + content.xpath('//span[@class="uk dpron-i "]//source[@type="audio/mpeg"]/@src')[0]
    except IndexError:
        us_audio, gb_audio = "-", "-"
    return us_audio, gb_audio


def cambridge_word(word):
    print(word)
    word_result = dict()
    content = html_data('-'.join(word.split(' ')))
    word_meanings = get_meanings(content)
    us_audio, gb_audio = get_audio(content)
    audio_filename = f"camb_us_{'_'.join(word.split(' '))}.mp3"
    if us_audio != DOMAIN:
        download(us_audio, audio_filename)
        word_result['audio_filename'] = audio_filename
    word_result['meaning'] = word_meanings
    word_result['us_audio'] = us_audio
    word_result['gb_audio'] = gb_audio
    return word_result


def requests2json(word):
    mean_json = cambridge_word(word)
    search_links = create_search_links(word)
    if len(mean_json['meaning']) == 0:
        wiki_mean = wiki_summary(word)
        if wiki_mean != None:
            mean_json['meaning'] =  wiki_mean[0]
            search_links['wiki'] = wiki_mean[1]
    else:
        search_links['camb'] = URL_S + '-'.join(word.split(' '))
    mean_json['search_links'] = search_links
    return mean_json


def bold_keyword(p, example):
    for m in p.finditer(example):
        s = m.start()
        e = m.end()
        example = example[:s]+'<b>'+example[s:e]+'</b>'+example[e:]
    return example


def create_description(word, word_json, spec_examples=None, n_spec_ex=4):
    p = re.compile(word)
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
            examples_str += '</ul></details></i></sub><br><br>'
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
    
    anki_description = examples_str + meaning + audio + links
    anki_import = f'{word}\t{anki_description}'
    
    return anki_import, anki_description
    

def wiki_summary(word, auto_suggest=False):
    try:
        page = wiki.page(word, auto_suggest=auto_suggest)
        return ('~ ' if auto_suggest==True else '') + page.summary, page.url
    except (PageError, DisambiguationError) as e:
        if auto_suggest == False:
            return wiki_summary(word, auto_suggest=True)
        return None


def create_search_links(word):
    request = '+'.join(word.split())
    # change the query language https://www.google.com/preferences?hl=en&fg=1#languages
    google = 'https://www.google.com/search?q='+request
    yandex = 'https://yandex.ru/search/?text='+request+'&lang=en'
    wiki = 'https://en.wikipedia.org/w/index.php?search='+request
    camb = 'https://dictionary.cambridge.org/spellcheck/english/?q='+request
    return {'google':google, 'yandex':yandex, 'wiki':wiki, 'camb':camb}