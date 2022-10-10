#the folder where Anki media (audio) files are located 
media_folder = '/home/junglepy/snap/anki-ppd/common/anki/User 1/collection.media/' # Linux
media_folder = r"C:/Users/Eduard/AppData/Roaming/Anki2/User 1/collection.media/" #W10

#adding examples of word usage from subs, arxiv, article or other processed text
EXAMPLES_FROM_TEXT = True
#number of word meanings from the cambridge dictionary
N_MEANINGS = 4
#the number of examples of word usage in different contexts
N_EXAMPLES = 4
N_SYNONYMS = 15

#http://login:pass@255.255.255.255:port proxy pattern. Not necessarily
proxy_list = []

# Model parameters
#How many words Bert predicts by [MASK]. A higher value increases accuracy but slows processing.
TOP_K = 10g