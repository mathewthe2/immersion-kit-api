from decks.decks import Decks 
from search.searchFilter import SearchFilter
from search.searchOrder import SearchOrder
from config import DECK_CATEGORIES, DEFAULT_CATEGORY, DEV_MODE, EXAMPLE_LIMIT, SENTENCE_FIELDS, MEDIA_FILE_HOST, SENTENCE_KEYS_FOR_LISTS, RESULTS_LIMIT, SENTENCES_LIMIT
import json
from bisect import bisect
import sqlite3

class DecksManager:

    con = sqlite3.connect(":memory:", check_same_thread=False)
    cur = con.cursor()
    cur.execute("create table sentences ({})".format(','.join(SENTENCE_FIELDS)))
    cur.execute("""CREATE VIRTUAL TABLE sentences_idx
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
    cur.execute("CREATE VIRTUAL TABLE sentence_idx_row USING fts5vocab('sentences_idx', 'instance');")

    def __init__(self, category=DEFAULT_CATEGORY, dictionary=None):
        self.decks = {}
        self.sentence_map = {}
        self.translation_map = {}
        self.category_range = []
        self.category = category
        self.dictionary = dictionary
        self.search_filter = SearchFilter()
        self.search_order = SearchOrder()

    def get_category(self):
        return self.category

    def set_category(self, category):
        if category in self.decks:
            self.category = category

    def set_search_filter(self, search_filter):
        self.search_filter = search_filter
        
    def set_search_order(self, search_order):
        self.search_order = search_order

    def load_decks(self):
        sentence_counter = 0
        for deck_category in DECK_CATEGORIES:
            sentence_counter = Decks(
                category=deck_category, 
                path=DECK_CATEGORIES[deck_category]["path"],
                has_image=DECK_CATEGORIES[deck_category]["has_image"],
                has_sound=DECK_CATEGORIES[deck_category]["has_sound"],
                has_resource_url=DECK_CATEGORIES[deck_category]["has_resource_url"],
                dictionary=self.dictionary
            ).load_decks(sentence_counter, self.cur)
            self.category_range.append(sentence_counter)
            if DEV_MODE:
                break

    def get_category_for_row_id(self, row_id):
        index = bisect(self.category_range, row_id)
        categories = list(DECK_CATEGORIES.keys())
        if len(categories) > index:
            return categories[index] 
        else:
            return None

    def get_deck_for_row_id(self, row_id):
        for index, id in enumerate(self.category_range):
            if row_id <= id:
                return list(DECK_CATEGORIES.keys())[index]
        return None
            
    def get_deck_by_name(self, deck_name):
        return [self.parse_sentence(sentence) for sentence in self.decks[self.category].get_deck_by_name(deck_name)]

    def get_sentences(self, ids):
        search_list = ids[:SENTENCES_LIMIT]
        self.cur.execute("select * from sentences where sentence_id in ({seq})".format(
            seq=','.join(['?']*len(search_list))), search_list)
        result = self.cur.fetchall()
        return self.query_result_to_sentences(result)

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
        token_column = "norms" if text_is_japanese else "eng_norms"
        self.cur.execute("""WITH ranked AS
                            (SELECT *, row_number() 
                                OVER (PARTITION BY deck_name ORDER BY id ASC) AS rn
                            FROM sentences
                            WHERE id IN (SELECT rowid
                                        FROM {category}_sentences_idx
                                        WHERE {token_column} MATCH ?
                            ))
                            SELECT * 
                            FROM ranked
                            WHERE rn <= ?
                            {filtering}
                            {ordering}
                            LIMIT ?
        """.format(category=category, token_column=token_column, filtering=self.get_filter_string(), ordering=self.search_order.get_order()), (text, EXAMPLE_LIMIT, RESULTS_LIMIT))
        result = self.cur.fetchall()

        sentences = self.query_result_to_sentences(result)
        category_count = self.count_categories_for_ffs(text)
        return sentences, category_count

    def get_category_sentences_exact(self, category, text):
        self.cur.execute("""WITH ranked AS
                            (SELECT *, row_number() 
                                OVER (PARTITION BY deck_name ORDER BY id ASC) AS rn
                            FROM sentences
                            WHERE category = ?
                            AND sentence LIKE ?
                            )
                            SELECT *
                            FROM ranked
                            WHERE rn <= ?
                            {filtering}
                            {ordering}
                            LIMIT ?                            
                        """.format(filtering=self.get_filter_string(), ordering=self.search_order.get_order()), (category, '%' + text + '%',EXAMPLE_LIMIT,  RESULTS_LIMIT))
        result = self.cur.fetchall()
        sentences = self.query_result_to_sentences(result)
        category_count = self.count_categories_for_exact_sentence(text)
        return sentences, category_count

    def get_row_ids_ffs(self, text):
        self.cur.row_factory = lambda cursor, row: row[0]
        TERM_LIMIT = 20
        terms = [term for term in text.split(" ") if len(term) > 0][:TERM_LIMIT]
        if not terms:
            return self.zero_category_count()
        row_ids = []
        self.cur.execute("""SELECT doc
                            FROM sentence_idx_row
                            WHERE term = ?
                            {}
        """.format(" ".join(["INTERSECT SELECT doc FROM sentence_idx_row WHERE term = ?"]*(len(terms)-1))), (*terms,))
        row_ids = self.cur.fetchall()
        self.cur.row_factory = None
        deck_count_map = {}
        filtered_row_ids = []
        for row_id in row_ids:
            category = self.get_category_for_row_id(row_id)
            deck_name = bisect(self.deck_range_by_category[category], row_id)
            if deck_name in deck_count_map:
                deck_count_map[deck_name] += 1
                if deck_count_map[deck_name] <= EXAMPLE_LIMIT:
                    filtered_row_ids.append(row_id)
            else:
                deck_count_map[deck_name] = 1
                filtered_row_ids.append(row_id)

    def count_categories_for_ffs(self, text):
        self.cur.row_factory = lambda cursor, row: row[0]
        TERM_LIMIT = 20
        terms = [term for term in text.split(" ") if len(term) > 0][:TERM_LIMIT]
        if not terms:
            return self.zero_category_count()
        row_ids = []
        self.cur.execute("""SELECT doc
                            FROM sentence_idx_row
                            WHERE term = ?
                            {}
        """.format(" ".join(["INTERSECT SELECT doc FROM sentence_idx_row WHERE term = ?"]*(len(terms)-1))), (*terms,))
        row_ids = self.cur.fetchall()
        self.cur.row_factory = None
        category_count = {}
        for category in DECK_CATEGORIES:
            category_count[category] = 0
        for row_id in row_ids:
            category = self.get_category_for_row_id(row_id)
            if category in DECK_CATEGORIES:
                category_count[category] += 1
        return category_count

    def zero_category_count(self):
        category_count = {}
        for category in DECK_CATEGORIES:
            category_count[category] = 0
        return category_count

    def count_categories_for_exact_sentence(self, text):
        self.cur.execute("select category, count(case when sentence like ? then 1 else null end) as `number_of_examples` from sentences group by category", ('%' + text + '%',))
        result = self.cur.fetchall()
        category_count = self.zero_category_count()
        for category, count in result:
            if category in DECK_CATEGORIES:
                category_count[category] = count
        return category_count

    def get_sentence(self, id):
        self.cur.execute("select * from sentences where id = ?", (id,))
        result = self.cur.fetchall()
        if result is not None:
            sentences = self.query_result_to_sentences(result)
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

    def parse_sentence(self, sentence):
        if sentence:
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