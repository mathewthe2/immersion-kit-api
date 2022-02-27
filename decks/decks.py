from glob import glob
from typing import MappingView
from config import ANIME_PATH, CONTEXT_RANGE, SENTENCE_FIELDS
import json
import string
from pathlib import Path

class Decks:
    def __init__(self, category="anime", path=ANIME_PATH, has_image=True, has_sound=True, has_resource_url=False):
        self.category = category
        self.path = path
        self.has_image = has_image
        self.has_sound = has_sound
        self.has_resource_url = has_resource_url

    def get_deck_by_name(self, deck_name):
        sentences = []
        file = Path(self.path, deck_name, 'data.json')
        if file.is_file():
            with open(file, encoding='utf-8') as f:
                sentences = json.load(f)
        return sentences

    def load_decks(self, sentence_counter, cur):
        deck_folders = glob(str(self.path) + '/*/')
        # if True: # Testing
        #     deck_folders = deck_folders[:1]
        for deck_folder in deck_folders:
            print("adding", deck_folder)
            sentences = self.load_one_deck(deck_folder)
            sentence_counter = self.load_sentences_to_db(sentences, sentence_counter, cur)
        return sentence_counter
    
    def load_one_deck(self, path):
        sentences = []
        file = Path(path, 'data.json')
        with open(file, encoding='utf-8') as f:
            sentences = json.load(f)      
        # for sentence in sentences:
            # if 'word_base_list' in sentence:
            #     sentence_map = self.map_sentence(sentence['word_base_list'], sentence['id'], sentence_map)
            # if 'translation_word_base_list' in sentence:
            #     translation_map = self.map_sentence(sentence['translation_word_base_list'], sentence['id'], translation_map)
        return sentences

    def load_sentences_to_db(self, sentences, sentence_counter, cur):
        sentence_tuple_list = []
        tokenized_sentence_list = []
        for index, sentence in enumerate(sentences):
            sentence['category'] = self.category
            sentence["position"] = index + 1

            sentence["sentence_id"] = sentence["id"]
            sentence["id"] = sentence_counter
            sentence["norms"] = ' '.join([base for base in sentence["word_base_list"] if base != ' '])
            if "translation_word_base_list" in sentence:
                sentence["eng_norms"] = ' '.join([base for base in sentence["translation_word_base_list"] if base != ' '])
            else:
                sentence["eng_norms"] = ''

            sentence_data = [sentence["id"]]
            for key in SENTENCE_FIELDS[1:]:
                if key in sentence:
                    value = sentence[key]
                    if type(value) == list:
                        value = json.dumps(value, ensure_ascii=False)
                    sentence_data.append(value)
                else:
                    sentence_data.append('')
            sentence_tuple_list.append(tuple(sentence_data))
             # indexing table
            tokenized_card = (sentence["id"], sentence["norms"],  sentence["eng_norms"])
            tokenized_sentence_list.append(tokenized_card)
            sentence_counter += 1
        cur.executemany("insert into sentences values ({})".format(",".join(['?']*len(SENTENCE_FIELDS))), sentence_tuple_list)
        cur.executemany("insert into sentences_idx(rowid, norms, eng_norms) values (?, ?, ?)", tokenized_sentence_list)
        cur.executemany("insert into {}_sentences_idx(rowid, norms, eng_norms) values (?, ?, ?)".format(self.category), tokenized_sentence_list)

        return sentence_counter

    def filter_fields(self, sentence, excluded_fields):
        filtered_sentence = {}
        for key in sentence:
            if key not in excluded_fields:
                filtered_sentence[key] = sentence[key]
        return filtered_sentence

    def format_sentence_key(self, example_id):
        return "{}-{}".format(self.category, example_id)
    
    def map_sentence(self, words, example_id, output_map):
        for (index, word) in enumerate(words):
            is_repeat = words.index(word) != index
            if is_repeat:
                continue
            if word in string.punctuation or word in '！？。、（）':
                continue
            if word not in output_map:
                output_map[word] = set()
            output_map[word].add(self.format_sentence_key(example_id))
        return output_map
