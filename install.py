import urllib.request
from pathlib import Path

bert_base_uncased_links = [
'https://huggingface.co/bert-base-uncased/resolve/main/config.json',
'https://huggingface.co/bert-base-uncased/resolve/main/tokenizer.json',
'https://huggingface.co/bert-base-uncased/resolve/main/tokenizer_config.json',
'https://huggingface.co/bert-base-uncased/resolve/main/vocab.txt',
'https://huggingface.co/bert-base-uncased/resolve/main/pytorch_model.bin',]

folder = "./model/"


def download_file(link, folder):
    filename = link.split('/')[-1]
    filepath = folder + filename
    urllib.request.urlretrieve(link, filepath)


Path(folder).mkdir(parents=True, exist_ok=True)
for link in bert_base_uncased_links:
    download_file(link, folder)