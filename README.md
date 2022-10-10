When you click on a word, potplayer brings the meaning of the word from the explanatory dictionary to your browser, and adds the word to the anki cards.

There are two versions:
## Lite:
- Word meanings from cambridge dictionary, wikipedia
- Examples of use from subtitles

## Bert:
Same as lite, plus the following features:
- Sorting cambridge dictionary word meanings given the context of the sentence. Those meanings that are closer to the phrase will be higher. Sorting goes by cosine similarity of Bert's embedding vectors.

- Output synonyms for the word. The [Mask] is used in the Bert model. The predicted variants are further compared by cosine similarity to the original phrase.

## Install:
Run install.py