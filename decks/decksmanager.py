from decks.decks import Decks 
from pathlib import Path
from search.searchFilter import SearchFilter
from search.searchOrder import SearchOrder
from config import DECK_CATEGORIES, DEFAULT_CATEGORY, DEV_MODE, EXAMPLE_LIMIT, TERM_LIMIT, SENTENCE_FIELDS, MEDIA_FILE_HOST, SENTENCE_KEYS_FOR_LISTS, RESULTS_LIMIT, SENTENCES_LIMIT
import json, ndjson
from bisect import bisect
from itertools import permutations
import re
import sqlite3

def regexp(y, x, search=re.search):
        return 1 if search(y, x) else 0

def get_any_order_regex(tokens):
    return r'|'.join(['.*?'.join(perm) for perm in list(permutations(tokens))])

class DecksManager:
    con = sqlite3.connect(":memory:", check_same_thread=False)
    con.create_function('regexp', 2, regexp)
    cur = con.cursor()
    cur.execute('CREATE TABLE decks (id INTEGER, category TEXT, name TEXT)')
    cur.execute("CREATE TABLE sentences ({})".format(','.join(SENTENCE_FIELDS)))
    cur.execute("CREATE INDEX sentences_decks_idx ON sentences (deck_id)")
    cur.execute("CREATE INDEX idx_sentences_category ON sentences (category)")
    cur.execute("""CREATE VIRTUAL TABLE sentences_idx
                 USING fts5(norms,
                            eng_norms,
                            content=sentences,
                            content_rowid=id,
                            tokenize = "unicode61 tokenchars '-_'");
    """)
    # mini table for queries with huge results
    cur.execute("""CREATE VIRTUAL TABLE mini_sentences_idx
                 USING fts5(norms,
                            eng_norms,
                            content=sentences,
                            content_rowid=id,
                            tokenize = "unicode61 tokenchars '-_'");
    """)
    for category in list(DECK_CATEGORIES.keys()):
        cur.execute("""CREATE VIRTUAL TABLE {}
                 USING fts5(norms,
                            eng_norms,
                            content=sentences,
                            content_rowid=id,
                            tokenize = "unicode61 tokenchars '-_'");
        """.format(category + "_sentences_idx"))

    def __init__(self, category=DEFAULT_CATEGORY, dictionary=None):
        self.decks = {}
        self.sentence_map = {}
        self.translation_map = {}
        self.category_range = []
        self.category = category
        self.deck_range_by_category = {}
        self.deck_names_by_category = {}
        self.dictionary = dictionary
        self.search_filter = SearchFilter()
        self.search_order = SearchOrder()
        self.example_limit = EXAMPLE_LIMIT
        self.example_offset = 0

    def get_category(self):
        return self.category

    def set_category(self, category):
        if category in self.decks:
            self.category = category

    def set_search_filter(self, search_filter):
        self.search_filter = search_filter
        
    def set_search_order(self, search_order):
        self.search_order = search_order

    def set_example_limit(self, example_limit):
        self.example_limit = example_limit

    def set_example_offset(self, example_offset):
        self.example_offset = example_offset

    def has_deck(self, category, deck_name):
        return False if category not in self.deck_names_by_category else (deck_name in self.deck_names_by_category[category])

    def load_decks(self):
        deck_counter, sentence_counter = 0, 0
        for deck_category in DECK_CATEGORIES:
            deck_counter, sentence_counter, deck_names, deck_range = Decks(
                category=deck_category, 
                path=DECK_CATEGORIES[deck_category]["path"],
                has_image=DECK_CATEGORIES[deck_category]["has_image"],
                has_sound=DECK_CATEGORIES[deck_category]["has_sound"],
                has_resource_url=DECK_CATEGORIES[deck_category]["has_resource_url"],
                dictionary=self.dictionary
            ).load_decks(deck_counter, sentence_counter, self.cur)
            self.deck_names_by_category[deck_category] = deck_names
            self.deck_range_by_category[deck_category] = deck_range
            self.category_range.append(sentence_counter)
            # if DEV_MODE:
            #     break

    def get_category_for_row_id(self, row_id):
        index = bisect(self.category_range, row_id)
        categories = list(DECK_CATEGORIES.keys())
        if len(categories) > index:
            return categories[index] 
        else:
            return None

    def get_deck_name_for_row_id(self, category, row_id):
        index = bisect(self.deck_range_by_category[category], row_id)
        deck_names = self.deck_names_by_category[category]
        if len(deck_names) > index:
            return deck_names[index] 
        else:
            return None
            
    def get_deck_by_name(self, deck_name, category):
        sentences = []
        path = DECK_CATEGORIES[category]['path']
        file = Path(path, deck_name, 'data.ndjson')
        if file.is_file():
            with open(file, encoding='utf-8') as f:
                sentences = ndjson.load(f) 
        return [self.parse_sentence(sentence, category='literature') for sentence in sentences]

    def get_sentences(self, ids):
        search_list = ids[:SENTENCES_LIMIT]
        self.cur.execute("select * from sentences where sentence_id in ({seq})".format(
            seq=','.join(['?']*len(search_list))), search_list)
        result = self.cur.fetchall()
        return self.query_result_to_sentences(result)

    def get_sentences(self, ids):
        search_list = ids[:SENTENCES_LIMIT]
        self.cur.execute("select * from sentences where sentence_id in ({seq})".format(
            seq=','.join(['?']*len(search_list))), search_list)
        result = self.cur.fetchall()
        return self.query_result_to_sentences(result)
    
    def get_results_with_count(self, result):
        sentences = []
        deck_count, category_count = {}, {}
        for sentence_tuple in result:
            sentence = {}
            for data_index, value in enumerate(sentence_tuple[:len(SENTENCE_FIELDS)]):
                key = SENTENCE_FIELDS[data_index]
                sentence[key] = '' if value == '' else json.loads(value) if key in SENTENCE_KEYS_FOR_LISTS else value
            count_for_category = sentence_tuple[-1]
            count_for_deck = sentence_tuple[-2]
            if sentence["deck_name"] not in deck_count:
                deck_count[sentence["deck_name"]] = count_for_deck
            if sentence["category"] not in category_count:
                category_count[sentence["category"]] = count_for_category
            sentence = self.parse_sentence(sentence)
            sentences.append(sentence)
        return sentences, deck_count, category_count

    def query_result_to_sentences(self, result):
        sentences = []
        for sentence_tuple in result:
            sentence = {}
            for data_index, value in enumerate(sentence_tuple[:len(SENTENCE_FIELDS)]):
                key = SENTENCE_FIELDS[data_index]
                sentence[key] = '' if value == '' else json.loads(value) if key in SENTENCE_KEYS_FOR_LISTS else value
            sentence = self.parse_sentence(sentence)
            sentences.append(sentence)
        return sentences

    def get_filter_string(self):
        return "" if not self.search_filter.has_filters() else "AND id IN ({})".format(self.search_filter.get_query_string())

    def get_category_sentences_fts(self, category, text, text_is_japanese=True):
        
        # Server constraint
        if text in ['もの', 'こと']:
            return self.get_category_sentences_exact(category if category else 'anime', text, text_is_japanese)
        # if len(text) == 1 and not category:
        #     no_kanji = is_hiragana(text) or is_katakana(text) or not is_japanese(text)
        #     if no_kanji:
        #         category = 'anime'
        
        # Construct Query
        token_column = "norms" if text_is_japanese else "eng_norms"
        sentence_table = 'sentences_idx' if not category else '{}_sentences_idx'.format(category)
        self.cur.execute("""
                WITH matching_ids AS (
                  SELECT rowid
                    FROM {sentence_table}
                    WHERE {token_column} MATCH ?
                ),
                count_for_deck AS (
                    SELECT COUNT(*) as sentences_for_deck, d.id as deck_id, d.category 
                    FROM sentences as s
                    INNER JOIN decks as d
                    ON d.id = s.deck_id
                    WHERE s.id in matching_ids
                    GROUP BY d.name
                  ),
                count_for_category AS (
                    SELECT c.deck_id, c.sentences_for_deck,
                    SUM (sentences_for_deck) OVER (PARTITION BY c.category) as sentences_for_category
                    FROM count_for_deck as c
                  ),
                ranked AS
                    (SELECT *, 
                        row_number()
                            OVER (PARTITION BY category {ordering}),
                        row_number()
                            OVER (PARTITION BY category, deck_name {ordering}) AS rn
                        FROM sentences
                        WHERE id IN matching_ids
                    )
                SELECT *
                FROM ranked r
                LEFT JOIN count_for_category cc
                ON r.deck_id = cc.deck_id
                WHERE rn <= ?
                {filtering}
                LIMIT ?
                OFFSET ?
        """.format(sentence_table=sentence_table, 
                   token_column=token_column, 
                   filtering=self.get_filter_string(), 
                   ordering=self.search_order.get_order()), 
                   (text, RESULTS_LIMIT, RESULTS_LIMIT, self.example_offset)
                   )
        result = self.cur.fetchall()
        print(result[0])
        return self.get_results_with_count(result)

    def get_category_sentences_exact(self, category, text, text_is_japanese=True):
        category_filter = '' if not category else "category = '{}' AND ".format(category)
        sentence_filter = 'sentence LIKE ?' if text_is_japanese else 'translation LIKE ?'
        sentence_expression = '%' + text + '%'
        words = text.split(' ')
        if text_is_japanese and len(words) > 1:
                sentence_filter = 'sentence REGEXP ?'
                sentence_expression = get_any_order_regex(words)
        self.cur.execute("""
                WITH matching_ids AS (
                  SELECT id
                    FROM sentences
                    WHERE {category_filter} {sentence_filter}
                ),
                count_for_deck AS (
                    SELECT COUNT(*) as sentences_for_deck, d.id as deck_id, d.category 
                    FROM sentences as s
                    INNER JOIN decks as d
                    ON d.id = s.deck_id
                    WHERE s.id in matching_ids
                    GROUP BY d.name
                  ),
                count_for_category AS (
                    SELECT c.deck_id, c.sentences_for_deck,
                    SUM (sentences_for_deck) OVER (PARTITION BY c.category) as sentences_for_category
                    FROM count_for_deck as c
                  ),
                ranked AS(
                    SELECT *, 
                        row_number()
                            OVER (PARTITION BY category {ordering}),
                        row_number()
                            OVER (PARTITION BY category, deck_name {ordering}) AS rn
                    FROM sentences
                    WHERE id IN matching_ids
                )
                SELECT *
                FROM ranked r
                LEFT JOIN count_for_category cc
                ON r.deck_id = cc.deck_id
                WHERE rn <= ?
                {filtering}
                LIMIT ?
                OFFSET ?                    
                """.format(category_filter=category_filter, 
                            sentence_filter=sentence_filter, 
                            filtering=self.get_filter_string(), 
                            ordering=self.search_order.get_order()), 
                            (sentence_expression, self.example_limit,  RESULTS_LIMIT, self.example_offset)
                            )
        result = self.cur.fetchall()
        return self.get_results_with_count(result)
    
    def get_sentence(self, id):
        self.cur.execute("select * from sentences where id = ?", (id,))
        result = self.cur.fetchall()
        if result is not None:
            sentences = self.query_result_to_sentences(result)
            if sentences:
                return sentences[0]
        return None

    def get_ranged_sentences(self, category, deck_name, episode, offset, limit):
        if episode is None or episode <= 0:
            self.cur.execute("select * from sentences where category = ? and deck_name = ? limit ? offset ?", (category, deck_name, limit, offset))
        else:
            self.cur.execute("select * from sentences where category = ? and deck_name = ? and episode = ? limit ? offset ?", (category, deck_name, episode, limit, offset))
        result = self.cur.fetchall()
        sentences = self.query_result_to_sentences(result)
        return sentences

    def count_ranged_sentences(self, deck_name, episode):
        self.cur.execute("select count(*) from sentences where category = ? and deck_name = ? and episode = ?", (self.category, deck_name, episode))
        result = self.cur.fetchone()
        return result[0]

    def parse_sentence(self, sentence, category=None):
        if sentence:
            if not category:
                category = self.category if 'category' not in sentence else sentence['category']
            needs_image_url = DECK_CATEGORIES[category]['has_image'] and not DECK_CATEGORIES[category]['has_resource_url']
            if (needs_image_url):
                image_path = '{}/{}/{}/media/{}'.format(MEDIA_FILE_HOST, category, sentence['deck_name'], sentence['image'])
                sentence['image_url'] = image_path.replace(" ", "%20")
            needs_sound_url= DECK_CATEGORIES[category]['has_sound'] and not DECK_CATEGORIES[category]['has_resource_url']
            if (needs_sound_url):
                sound_path = '{}/{}/{}/media/{}'.format(MEDIA_FILE_HOST, category, sentence['deck_name'], sentence['sound'])
                sentence['sound_url'] = sound_path.replace(" ", "%20")
        return sentence