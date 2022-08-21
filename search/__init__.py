import string
from wanakana import to_hiragana, is_japanese
from search.searchFilter import SearchFilter
from search.searchOrder import SearchOrder
from tokenizer.englishtokenizer import analyze_english, is_english_word
from tokenizer.japanesetokenizer import analyze_japanese, KANA_MAPPING
from config import DEFAULT_CATEGORY, EXAMPLE_LIMIT, RESULT_EXCLUDED_FIELDS, CONTEXT_RANGE, MINI_QUERY_KEYWORDS
from tagger import Tagger
from data.deckData import DECK_LIST
from decks.decksmanager import DecksManager
from dictionary import Dictionary

tagger = Tagger()
tagger.load_tags()

dictionary = Dictionary()
dictionary.load_dictionary('JMdict+')

decks = DecksManager(category=DEFAULT_CATEGORY, dictionary=dictionary)
decks.load_decks()

# def close():
#     decks.con.commit()
#     decks.con.close()

def get_deck_by_id(deck_name, category=DEFAULT_CATEGORY):
    return dict(data=decks.get_deck_by_name(deck_name, category=category))

def get_sentences_for_reader(deck_name, episode, offset, limit):
    deck_data = next((deck for deck in DECK_LIST if deck["id"].lower() == deck_name.lower()), None)
    if deck_data is None:
        return dict(data=[], error="Deck not ready yet")
    else:
        decks.set_category(deck_data["category"])
        if "deck_name" in deck_data:
            deck_name = deck_data["deck_name"]
        total = deck_data["sentences"]
        if deck_data["episodes"] > 1:
            total = decks.count_ranged_sentences(deck_name, episode)
        else:
            episode = -1 # only one episode or chapter
        return dict(data=decks.get_ranged_sentences(deck_name, episode, offset, limit), episodes=deck_data["episodes"], total=total)   

def get_sentence_by_id(id):
    return decks.get_sentence(id)

def deconstruct_combinatory_sentence_id(sentence_id):
    if '-' in sentence_id:
        return {
            'category': sentence_id.split('-', 1)[0],
            'sentence_id': sentence_id.split('-', 1)[1]
        }
    else:
        return None

def get_sentences_with_combinatory_ids(combinatory_sentence_ids):
    search_list = [deconstruct_combinatory_sentence_id(sentence_id)['sentence_id'] for sentence_id in combinatory_sentence_ids if deconstruct_combinatory_sentence_id(sentence_id)]
    result = decks.get_sentences(search_list)
    return dict(data=result)

def get_sentence_with_context(id):
    sentence = get_sentence_by_id(id)
    if not sentence:
        return {}
    context_sentences = decks.get_ranged_sentences(sentence["category"], sentence["deck_name"], episode=None, offset=max(1, sentence["position"]-CONTEXT_RANGE), limit=CONTEXT_RANGE*2)
    ## Improvement: Refactor filtering with better mathematical formula
    sentence["pretext_sentences"] = [s for s in context_sentences if s["position"] < sentence["position"]]
    sentence["posttext_sentences"] = [s for s in context_sentences if s["position"] > sentence["position"]]
    return sentence

def get_examples_and_category_count(category, text_is_japanese, text, word_bases, tags=[], is_exact_match=False):
    examples = []
    category_count = {}
    deck_count = {}
    
    # Server constraint
    if text in MINI_QUERY_KEYWORDS:
        category = 'mini'

    if is_exact_match:
        examples, deck_count, category_count = decks.get_category_sentences_exact(
            category, 
            text
        )
    else:
        examples, deck_count, category_count = decks.get_category_sentences_fts(
            category=category, 
            text=' '.join(word_bases), 
            text_is_japanese=text_is_japanese
        )
    if len(examples) > 0:
        examples = parse_examples(examples, text_is_japanese, word_bases)
    return {
        "examples": filter_fields(examples, excluded_fields=RESULT_EXCLUDED_FIELDS),
        "deck_count": deck_count,
        "category_count": category_count
    }

def filter_fields(examples, excluded_fields):
    if examples == []:
        return []
    filtered_examples =[]
    for example in examples:
        filtered_example= {}
        for key in example:
            if key not in excluded_fields:
                filtered_example[key] = example[key]
        filtered_examples.append(filtered_example)
    return filtered_examples

def parse_examples(examples, text_is_japanese, word_bases):
    for example in examples:
        if 'deck_name' in example:
            example['tags'] = tagger.get_tags_by_deck(example['deck_name'])
        example['word_index'] = []
        example['translation_word_index'] = []
        if text_is_japanese:
            example['word_index'] = [index for index, word in enumerate(example['word_base_list']) if word in word_bases]
        else:
            example['translation_word_index'] = [index for index, word in enumerate(example['translation_word_base_list']) if word in word_bases]
    return examples

def look_up(text, sorting, category, tags=[], user_levels={}, min_length=None, max_length=None, selected_decks=[], offset=0, limit=EXAMPLE_LIMIT):

    is_exact_match = '「' in text and '」' in text
    if is_exact_match:
        text = text.split('「')[1].split('」')[0]
    else:
        text = text.translate({ord(c): None for c in string.punctuation + "〜！？。、（）：「」『』"})

    if len(text.strip()) == 0:
        return {}
    
    text_is_japanese = is_japanese(text) 
    if not text_is_japanese:
        if '"' in text: # force English search
            text = text.split('"')[1]
        else:  
            hiragana_text = to_hiragana(text, custom_kana_mapping=KANA_MAPPING)
            hiragana_text = hiragana_text.replace(" ", "") 
            if is_japanese(hiragana_text):
                text_is_english_word = " " not in text and is_english_word(text)  
                if not text_is_english_word:
                    text_is_japanese = True
                    text = hiragana_text
                else:
                    word_bases = analyze_japanese(hiragana_text)['base_tokens']
                    if len(word_bases) > 1:
                        text_is_japanese = False
                    else:
                        text_is_japanese = True
                        text = hiragana_text
                        # TODO: suggest english word in return query here
    
    # if not is_exact_match:
    #     is_exact_match = text_is_japanese and dictionary.is_uninflectable_entry(text)
    if category:
        decks.set_category(category)
    tagged_decks = None if not tags else tagger.get_decks_by_tags(tags)
    filter_decks = None if not category else get_filtered_decks(category, selected_decks, tagged_decks)
    decks.set_search_filter(SearchFilter(min_length, max_length, user_levels, filter_decks))
    decks.set_search_order(SearchOrder(sorting))
    decks.set_example_limit(limit)
    decks.set_example_offset(offset)
    text = text.replace(" ", "") if text_is_japanese else text
    word_bases = analyze_japanese(text)['base_tokens'] if text_is_japanese else analyze_english(text)['base_tokens']
    examples_and_count = get_examples_and_category_count(category, text_is_japanese, text, word_bases, tags, is_exact_match)
    examples = examples_and_count["examples"]
    deck_count = examples_and_count["deck_count"] if not tagged_decks else get_filtered_deck_count(examples_and_count["deck_count"], tagged_decks)
    dictionary_words = [] if not text_is_japanese else [word for word in word_bases if dictionary.is_entry(word)]
    result = [{
        'dictionary': get_text_definition(text, dictionary_words),
        'exact_match': text if is_exact_match else "",
        'examples': examples,
        "deck_count": deck_count,
        "category_count": examples_and_count["category_count"]
    }]
    return dict(data=result)

def get_filtered_deck_count(deck_count, tagged_decks):
    result_count = {}
    for category_name in deck_count:
        for deck_name in deck_count[category_name]:
            if deck_name in tagged_decks:
                if category_name not in result_count:
                    result_count[category_name] = {}
                result_count[category_name][deck_name] = deck_count[category_name][deck_name]
    return result_count

def get_filtered_decks(category, selected_decks, tagged_decks):
    if selected_decks and tagged_decks:
        return list(set(selected_decks) & set(tagged_decks)) # intersection
    elif selected_decks:
        return [deck for deck in selected_decks if decks.has_deck(category, deck)]
    elif tagged_decks:
        return tagged_decks
    else:
        return None

def get_text_definition(text, dictionary_words):
    if dictionary.is_entry(text):
        return [dictionary.get_definition(text)]
    elif dictionary_words:
        return [dictionary.get_definition(word) for word in dictionary_words]
    else:
        return []