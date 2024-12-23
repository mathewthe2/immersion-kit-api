from glob import glob
from config import ANIME_PATH, SENTENCE_FIELDS, NEW_WORDS_TO_USER_PER_SENTENCE, DEV_MODE, MINI_DB_SIZE
import json, ndjson
import string
import bisect
from pathlib import Path
from dictionarytags import get_level

class Decks:
    def __init__(self, category="anime", path=ANIME_PATH, has_image=True, has_sound=True, has_resource_url=False, dictionary=None):
        self.category = category
        self.path = path
        self.has_image = has_image
        self.has_sound = has_sound
        self.has_resource_url = has_resource_url
        self.dictionary = dictionary

    def load_decks(self, deck_counter, sentence_counter, cur):
        deck_folders = glob(str(self.path) + '/*/')
        deck_range = []
        deck_names = []
        if DEV_MODE:
            deck_folders = deck_folders[:2]
        for deck_folder in deck_folders:
            print("adding", deck_folder)
            deck_counter += 1
            sentences = self.load_one_deck(deck_folder)
            sentence_counter = self.load_sentences_to_db(sentences, deck_counter, sentence_counter, cur)
            deck_range.append(sentence_counter)
            if sentences:
                deck_names.append(sentences[0]['deck_name'])
        return deck_counter, sentence_counter, deck_names, deck_range
    
    def load_one_deck(self, path):
        sentences = []
        file = Path(path, 'data.ndjson')
        with open(file, encoding='utf-8') as f:
            sentences = ndjson.load(f)      
        return sentences

    def load_sentences_to_db(self, sentences, deck_counter, sentence_counter, cur):
        sentence_tuple_list = []
        tokenized_sentence_list = []
        cur.execute("INSERT INTO decks (id, category, name) VALUES (?, ?, ?)", (deck_counter, self.category, sentences[0]["deck_name"]))
        for index, sentence in enumerate(sentences):
            sentence['category'] = self.category
            sentence["position"] = index + 1

            sentence["sentence_id"] = sentence["id"]
            sentence["id"] = sentence_counter
            sentence["deck_id"] = deck_counter
            sentence["norms"] = ' '.join([base for base in sentence["word_base_list"] if base != ' '])
            if "translation_word_base_list" in sentence:
                sentence["eng_norms"] = ' '.join([base for base in sentence["translation_word_base_list"] if base != ' '])
            else:
                sentence["eng_norms"] = ''
            sentence['jlpt_level'], sentence['wk_level'] = self.get_sentence_levels(sentence['word_base_list'])
            
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
        cur.executemany("INSERT INTO sentences values ({})".format(",".join(['?']*len(SENTENCE_FIELDS))), sentence_tuple_list)
        cur.executemany("INSERT INTO sentences_idx(rowid, norms, eng_norms) values (?, ?, ?)", tokenized_sentence_list)
        # cur.executemany("INSERT INTO {}_sentences_idx(rowid, norms, eng_norms) values (?, ?, ?)".format(self.category), tokenized_sentence_list)
        if sentence_counter < MINI_DB_SIZE:
            cur.executemany("insert into mini_sentences_idx(rowid, norms, eng_norms) values (?, ?, ?)".format(self.category), tokenized_sentence_list)
        # cur.execute("insert INTO sentences_idx(sentences_idx) VALUES('optimize')")
        # cur.execute("insert INTO {}_sentences_idx({}_sentences_idx) VALUES('optimize')".format(self.category, self.category))
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

    def get_sentence_levels(self, tokens):
        curriculums = {
            "JLPT": None,
            "WK": None
        }
        for curriculum in curriculums.keys():
            levels = []
            for token in tokens:
                if self.dictionary.is_entry(token):
                    level = get_level(self.dictionary.get_first_entry(token), curriculum)
                    if level:
                        if curriculum == 'JLPT':
                            bisect.insort_left(levels, level)
                        elif curriculum == 'WK':
                            bisect.insort_right(levels, level)
            if len(levels) > NEW_WORDS_TO_USER_PER_SENTENCE:
                curriculums[curriculum] =  levels[NEW_WORDS_TO_USER_PER_SENTENCE]
        return curriculums['JLPT'], curriculums['WK']
        