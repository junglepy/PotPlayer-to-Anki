import requests
import json
import re
import os

URL_AUTH = 'https://developers.lingvolive.com/api/v1.1/authenticate'
URL_TRANSLATE = 'https://developers.lingvolive.com/api/v1/Minicard'
KEY = 'NmE1ZDIwMmUtZDc3Ni00MjZhLTljOWItODk5NDA1Y2NiYWE4OmFmMGYyYTEzMmQ3NjQyZjBiZjZmNTBhNjk1NzFjMjQ0'


def create_tr_dict(en_list, ru_list):
    return dict(zip(en_list, ru_list))
  

def string_found(word, string1):
    if re.search(r"\b" + re.escape(word) + r"\b", string1):
        return True
    return False


def create_list(sub_name):
    flag_next_line = False
    result_list = []
    with open(sub_name, 'r', encoding='utf-8') as txt:
        for line in txt:
            if flag_next_line == True:
                line = line.rstrip()
                if line != '':
                    result_list.append(line)
                flag_next_line = False
            elif line.startswith('00:'):
                flag_next_line = True
    return result_list


def use_example(word, tr_dict):
    for row in tr_dict:
        if word in row:
            if string_found(word, row):
                return '<br><i>' + row + '<br>' + tr_dict[row] + '</i>'


def get_auth(token, url_auth):
    headers_auth = {'Authorization': 'Basic ' + token}
    auth = requests.post(url=url_auth, headers=headers_auth)
    if auth.status_code == 200:
        cur_token = auth.text
        return cur_token
    else:
        print("Not 200 code" + str(auth.status_code))


def translate(word, cur_token):
    url = 'https://developers.lingvolive.com/api/v1/Translation'
    headers = {'Authorization': 'Bearer ' + cur_token}
    params = {
        'text': word,
        'srcLang': '1033',
        'dstLang': '1049'
    }
    req = requests.get(url=url, headers=headers, params=params)
    if req.status_code == 200:
        res = req.json()
        try:
            #val = res['Body']['Markup'][2]['FullText']
            return res
        except TypeError:
            if res == 'Incoming request rate exceeded for 50000 chars per day pricing tier':
                print('Error - Incoming request rate exceeded for 50000 chars per day pricing tier')
                return res
            else:
                return 'No translation available'
    else:
        print('Error!' + str(req.status_code))


def minicard(word, url_tr, cur_token):
    headers = {'Authorization': 'Bearer ' + cur_token}
    params = {
        'text': word,
        'srcLang': '1033',
        'dstLang': '1049'
    }
    req = requests.get(url=url_tr, headers=headers, params=params)
    if req.status_code == 200:
        res = req.json()
        try:
            word_tr = res['Translation']['Translation']
            infinitive = res['Translation']['Heading']
            return word_tr, infinitive
        except TypeError:
            if res == 'Incoming request rate exceeded for 50000 chars per day pricing tier':
                print('Error - Incoming request rate exceeded for 50000 chars per day pricing tier')
                return res
            else:
                return 'No translation available'
    else:
        print('Error!' + str(req.status_code))
        return None, None


files = os.listdir()
for file in files:
    if file.endswith('en.srt'):
        en_sub = file
    if file.endswith('ru.srt'):
        ru_sub = file
en_list = create_list(en_sub)
ru_list = create_list(ru_sub)
        
tr_dict = create_tr_dict(en_list, ru_list)