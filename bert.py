from transformers import pipeline
from transformers import AutoTokenizer, AutoModel
import numpy as np
import torch
import itertools
from collections import OrderedDict
from fuzzywuzzy import process
import re
import config

tokenizer = AutoTokenizer.from_pretrained('./model/')
model = AutoModel.from_pretrained('./model/', output_hidden_states=True).eval()
unmasker = pipeline('fill-mask', model='./model/', device=0)

device = "cuda:0" if torch.cuda.is_available() else "cpu"
model = model.to(device)


def bert_tokenize(phrase, sentence):
    sent_indxs, tok = get_indexes(phrase, sentence)
    
    with torch.no_grad():
        out = model(**tok)

    states = out.hidden_states[-1].squeeze()

    embs = states[sent_indxs]
    avg = embs.mean(axis=0)
    sen_vec = states[0]
    return avg, sen_vec


def get_indexes(phrase, sentence):
    # TODO "pick up" , "I picked a movie and then picked up my credit card from the table and bought a ticket."
    # return [2,8] but must [7,8]
    tok =  tokenizer(sentence, return_tensors='pt').to(device)
    ids = tok.input_ids
    tokens = tokenizer.convert_ids_to_tokens(ids[0].tolist())
    
    try:
        words = phrase.split()
        sent_indxs = [tokens.index(word) for word in words]
    except ValueError:
        sent_indxs = fuzzyfinder(phrase, sentence, tokens)
        
    return sent_indxs, tok


def fuzzyfinder(phrase, sentence, tokens):
    words = re.sub(r'[^a-zA-Z]',' ', phrase).split(' ')
    ids = []
    for word in words:
        sim_word = process.extractOne(word, tokens)[0]
        ids.append(tokens.index(sim_word))
    return ids


def normalize(arr):
    a = torch.tensor(arr)
    min_v = torch.min(a)
    max_v = torch.max(a)
    a = (a - min_v) /(max_v-min_v)
    return np.array(a.cpu())


def cos_sim(v1, v2):
    similarity = torch.dot(v1,v2)/(torch.linalg.norm(v1)*torch.linalg.norm(v2))
    return similarity.cpu()


def get_total_score(synonyms, words_score, sen_score, p_score):
    total_score = []
    total_score.append(normalize(words_score))
    total_score.append(normalize(sen_score))

    total_score = np.array(total_score)
    total_score = total_score.mean(axis=0)
    
    s_score = np.array(sen_score)
    w_score = np.array(words_score)
    syn_values = np.stack((total_score, p_score, w_score, s_score), axis=1)
    ids = syn_values[:,0].argsort()[::-1]
    synonyms = np.array(synonyms)[ids]
    syn_score = syn_values[ids]
    syn_score_names = ['total', 'position', 'word', 'sentence']
    return synonyms, syn_score, syn_score_names


def get_bert_ngram_synonyms(phrase, sentence):
    words = phrase.split()
    sequence = sentence
    for word in words:
        sequence = re.sub(word, '[MASK]', sequence)
    
    synonyms = ['']
    sequences = [sequence]
    predict_scores = [0]
    for i in range(len(words)):
        top_k = config.TOP_K if i==0 else 2
        curr_syns = []
        curr_sequences = []
        curr_scores = []
        for n, sequence in enumerate(sequences):
            answers = unmasker(sequence, top_k=top_k)
            answers = answers[0] if isinstance(answers[0],list) else answers
            predicts = [el['token_str'] for el in answers]
            curr_scores += [predict_scores[n] + el['score'] for el in answers]
            curr_syns += [synonyms[n]+' '+predict if len(synonyms[n])>0 else predict for predict in predicts]
            curr_sequences += [el['sequence'] for el in answers]
        sequences = curr_sequences
        synonyms = curr_syns
        predict_scores = curr_scores
    predict_scores = np.array(predict_scores)/len(words)
    
    # Monograms
    prepared_sentence = re.sub(phrase, '[MASK]', sentence)
    answers = unmasker(prepared_sentence, top_k=config.TOP_K//3*2)
    monogram_syn = np.array([el['token_str'] for el in answers])
    monogram_scores = np.array([el['score'] for el in answers])
    monogram_sequences = np.array([el['sequence'] for el in answers])
    
    sequences = np.concatenate((np.array(sequences), monogram_sequences))
    synonyms = np.concatenate((np.array(synonyms), monogram_syn))
    predict_scores = np.concatenate((predict_scores, monogram_scores))
    
    words_score = []
    sen_score = []
    word_vec1, sen_vec1 = bert_tokenize(phrase, sentence)
    for i, seq in enumerate(sequences):
        word_vec2, sen_vec2 = bert_tokenize(synonyms[i], seq)
        
        w_similarity = cos_sim(word_vec1, word_vec2)
        s_similarity = cos_sim(sen_vec1, sen_vec2)
        words_score.append(w_similarity)
        sen_score.append(s_similarity)
    
    
    synonyms, syn_scores, syn_score_names = get_total_score(synonyms, words_score, sen_score, predict_scores)
    synonyms = synonyms[syn_scores[:,0]>0.1]
    syn_scores = syn_scores[syn_scores[:,0]>0.1]

    return synonyms[:config.N_SYNONYMS]
    

def dictionary_sense_sorting(word, sentence, word_json):
    v1, _ = bert_tokenize(word,sentence)

    sorted_meaning = []
    score = []

    if isinstance(word_json['meaning'], dict) and len(word_json['meaning'])>0:
        word_meanings = word_json['meaning']
    else:
        return word_json
    for mean, examples in word_meanings.items():
        if len(examples) > 0:
            score_mean = []
            for example in examples:
                v2, _ = bert_tokenize(word,example)
                score_mean.append(cos_sim(v1, v2))
            score_mean = np.mean(np.array(score_mean), axis=0)
            score.append(score_mean) 
    indxs = np.argsort(score)[::-1]
    wm = list(word_meanings.items())
    for ind in indxs:
        sorted_meaning.append(wm[ind])
    sorted_meaning = sorted_meaning[:config.N_MEANINGS]
    sorted_meaning = OrderedDict(sorted_meaning)
    word_json['meaning'] = sorted_meaning
    return word_json