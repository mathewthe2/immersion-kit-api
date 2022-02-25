
from decks.decks import Decks 
from config import DECK_CATEGORIES, DEFAULT_CATEGORY, SENTENCE_FIELDS, MEDIA_FILE_HOST, SENTENCE_KEYS_FOR_LISTS, RESULTS_LIMIT, SENTENCES_LIMIT
import json
import sqlite3

class DecksManager:

    con = sqlite3.connect(":memory:", check_same_thread=False)
    cur = con.cursor()
    cur.execute("create table sentences ({})".format(','.join(SENTENCE_FIELDS)))

    def __init__(self, category=DEFAULT_CATEGORY):
        self.decks = {}
        self.sentence_map = {}
        self.translation_map = {}
        self.category = category

    def get_category(self):
        return self.category

    def set_category(self, category):
        if category in self.decks:
            self.category = category
    
    def load_decks(self):
        for deck_category in DECK_CATEGORIES:
            self.decks[deck_category] = Decks(
                category=deck_category, 
                path=DECK_CATEGORIES[deck_category]["path"],
                has_image=DECK_CATEGORIES[deck_category]["has_image"],
                has_sound=DECK_CATEGORIES[deck_category]["has_sound"],
                has_resource_url=DECK_CATEGORIES[deck_category]["has_resource_url"])
            self.decks[deck_category].load_decks(self.cur, self.sentence_map, self.translation_map)

    def get_deck_by_name(self, deck_name):
        return [self.parse_sentence(sentence) for sentence in self.decks[self.category].get_deck_by_name(deck_name)]

    def get_sentences(self, combinatory_sentence_ids):
        search_list = combinatory_sentence_ids[:SENTENCES_LIMIT]
        self.cur.execute("select * from sentences where id in ({seq})".format(
            seq=','.join(['?']*len(search_list))), search_list)
        result = self.cur.fetchall()
        return self.query_result_to_sentences(result)

    def query_result_to_sentences(self, result):
        sentences = []
        for sentence_tuple in result:
            sentence = {}
            for data_index, value in enumerate(sentence_tuple):
                key = SENTENCE_FIELDS[data_index]
                sentence[SENTENCE_FIELDS[data_index]] = value
                if value == '':
                    sentence[key] = ''
                else:
                    sentence[key] = json.loads(value) if key in SENTENCE_KEYS_FOR_LISTS else value
            sentence["category"] = sentence["id"].split('-', 1)[0] # isolate category into different field
            sentence["id"] = sentence["id"].split('-', 1)[1] # remove category from id
            sentences.append(self.parse_sentence(sentence))
        return sentences
    
    def get_category_sentences(self, sentence_ids):
        combinatory_sentence_ids = [self.category + '-' + sentence_id for sentence_id in sentence_ids]
        return self.get_sentences(combinatory_sentence_ids)

    def get_category_sentences_exact(self, text):
        self.cur.execute("select * from sentences where category = ? and sentence like ? limit ?", (self.category, '%' + text + '%', RESULTS_LIMIT))
        result = self.cur.fetchall()
        sentences = self.query_result_to_sentences(result)
        return sentences

    def count_categories_for_exact_sentence(self, text):
        self.cur.execute("select category, count(case when sentence like ? then 1 else null end) as `number_of_examples` from sentences group by category", ('%' + text + '%',))
        result = self.cur.fetchall()
        category_count = {}
        for category, count in result:
            if category in DECK_CATEGORIES:
                category_count[category] = count
        return category_count

    def get_sentence(self, sentence_id):
        sentences = self.get_category_sentences([sentence_id])
        if len(sentences) > 0:
            return sentences[0]
        else:
            return None

    def get_ranged_sentences(self, deck_name, episode, offset, limit):
        if episode is None or episode <= 0:
            self.cur.execute("select * from sentences where category = ? and deck_name = ? limit ? offset ?", (self.category, deck_name, limit, offset))
        else:
            self.cur.execute("select * from sentences where category = ? and deck_name = ? and episode = ? limit ? offset ?", (self.category, deck_name, episode, limit, offset))
        result = self.cur.fetchall()
        sentences = self.query_result_to_sentences(result)
        return sentences

    def count_ranged_sentences(self, deck_name, episode):
        self.cur.execute("select count(*) from sentences where category = ? and deck_name = ? and episode = ?", (self.category, deck_name, episode))
        result = self.cur.fetchone()
        return result[0]

    def parse_sentence(self, sentence):
        if sentence:
            category = self.category if 'category' not in sentence else sentence['category']
            if (self.decks[category].needs_image_url()):
                image_path = '{}/{}/{}/media/{}'.format(MEDIA_FILE_HOST, category, sentence['deck_name'], sentence['image'])
                sentence['image_url'] = image_path.replace(" ", "%20")
            
            if (self.decks[category].needs_sound_url()):
                sound_path = '{}/{}/{}/media/{}'.format(MEDIA_FILE_HOST, category, sentence['deck_name'], sentence['sound'])
                sentence['sound_url'] = sound_path.replace(" ", "%20")
        return sentence

    def get_sentence_map(self):
        return self.sentence_map

    def get_sentence_translation_map(self):
        return self.translation_map