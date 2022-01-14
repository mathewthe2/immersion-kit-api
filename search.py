from wanakana import to_hiragana, is_japanese
from tokenizer.englishtokenizer import analyze_english, is_english_word
from tokenizer.japanesetokenizer import analyze_japanese, KANA_MAPPING
from config import DEFAULT_CATEGORY, DECK_CATEGORIES, EXAMPLE_LIMIT, RESULTS_LIMIT, NEW_WORDS_TO_USER_PER_SENTENCE, RESULT_EXCLUDED_FIELDS
from tagger import Tagger
from decks.decksmanager import DecksManager
from dictionary import Dictionary
from dictionarytags import word_is_within_difficulty

tagger = Tagger()
tagger.load_tags()

dictionary = Dictionary()
dictionary.load_dictionary('jmdict_combined')

decks = DecksManager()
decks.load_decks()
decks.set_category('anime')

# def close():
#     decks.con.commit()
#     decks.con.close()

def get_deck_by_id(deck_name, category=DEFAULT_CATEGORY):
    decks.set_category(category)
    return dict(data=decks.get_deck_by_name(deck_name))

def get_sentence_by_id(sentence_id, category=DEFAULT_CATEGORY):
    decks.set_category(category)
    return decks.get_sentence(sentence_id)

def deconstruct_combinatory_sentence_id(sentence_id):
    if '-' in sentence_id:
        return {
            'category': sentence_id.split('-', 1)[0],
            'example_id': sentence_id.split('-', 1)[1]
        }
    else:
        return None

def get_sentences_with_combinatory_ids(combinatory_sentence_ids):
    search_list = [sentence_id for sentence_id in combinatory_sentence_ids if deconstruct_combinatory_sentence_id(sentence_id)]
    result = decks.get_sentences(search_list)
    return dict(data=result)

def get_sentence_with_context(sentence_id, category=DEFAULT_CATEGORY):
    sentence = get_sentence_by_id(sentence_id, category)
    if not sentence:
        return None
    sentence["pretext_sentences"] = decks.get_category_sentences(sentence["pretext"])
    sentence["posttext_sentences"] = decks.get_category_sentences(sentence["posttext"])
    return sentence

def get_examples_and_category_count(text_is_japanese, words_map, text, word_bases, tags=[], user_levels={}, is_exact_match=False, min_length=None, max_length=None):
    examples = []
    category_count = {}
    for category in DECK_CATEGORIES:
        category_count[category] = 0
    # Exact match through SQL
    if is_exact_match:
        examples = decks.get_category_sentences_exact(text)
        category_count = decks.count_categories_for_exact_sentence(text)
    else:
        # Server side full text search
        results = [words_map.get(token, set()) for token in word_bases]
        if results:
            example_ids = list(set.intersection(*results))
            example_ids_for_search_category = filter_example_ids_by_category(example_ids, decks.get_category())
            examples = decks.get_sentences(example_ids_for_search_category)
            category_count = count_examples_for_category(example_ids)
    if len(examples) > 0:
        examples = filter_examples_by_length(examples, min_length, max_length)
        examples = filter_examples_by_tags(examples, tags)
        examples = filter_examples_by_level(user_levels, examples)
        examples = limit_examples(examples)
        examples = parse_examples(examples, text_is_japanese, word_bases)
    return {
        "examples": filter_fields(examples, excluded_fields=RESULT_EXCLUDED_FIELDS),
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
        example['tags'] = tagger.get_tags_by_deck(example['deck_name'])
        example['word_index'] = []
        example['translation_word_index'] = []
        if text_is_japanese:
            example['word_index'] = [index for index, word in enumerate(example['word_base_list']) if word in word_bases]
        else:
            example['translation_word_index'] = [index for index, word in enumerate(example['translation_word_base_list']) if word in word_bases]
    return examples

def look_up(text, sorting, category=DEFAULT_CATEGORY, tags=[], user_levels={}, min_length=None, max_length=None):

    is_exact_match = '「' in text and '」' in text
    if is_exact_match:
        text = text.split('「')[1].split('」')[0]
    
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
    decks.set_category(category)
    words_map = decks.get_sentence_map() if text_is_japanese else decks.get_sentence_translation_map()
    text = text.replace(" ", "") if text_is_japanese else text
    word_bases = analyze_japanese(text)['base_tokens'] if text_is_japanese else analyze_english(text)['base_tokens']
    examples_and_count = get_examples_and_category_count(text_is_japanese, words_map, text, word_bases, tags, user_levels, is_exact_match, min_length, max_length)
    examples = examples_and_count["examples"]
    if sorting:
        examples = sort_examples(examples, sorting)
    dictionary_words = [] if not text_is_japanese else [word for word in word_bases if dictionary.is_entry(word)]
    result = [{
        'dictionary': get_text_definition(text, dictionary_words),
        'exact_match': text if is_exact_match else "",
        'examples': examples,
        "category_count": examples_and_count["category_count"]
    }]
    return dict(data=result)

def sort_examples(examples, sorting):
    if sorting.lower() in ['sentence length', 'shortness']:
        return sorted(examples, key=lambda example: len(example['sentence']))
    elif sorting.lower() == 'longness':
        return sorted(examples, key=lambda example: len(example['sentence']), reverse=True)
    return examples

def get_text_definition(text, dictionary_words):
    if dictionary.is_entry(text):
        return [dictionary.get_definition(text)]
    elif dictionary_words:
        return [dictionary.get_definition(word) for word in dictionary_words]
    else:
        return []

def get_category_of_example_id(example_id):
    deconstructed = deconstruct_combinatory_sentence_id(example_id)
    return None if not deconstructed else deconstructed['category']

def count_examples_for_category(example_ids):
    # print('example ids', example_ids)
    # print('example ids', [id for id in example_ids if id.split('-')[0] == 'anime'])
    categories = [key for key in DECK_CATEGORIES]
    category_example_count = {}
    for category in categories:
        category_example_count[category] = 0
    for example_id in example_ids:
        category = get_category_of_example_id(example_id)
        if category in categories:
            category_example_count[category] += 1
    return category_example_count

def filter_example_ids_by_category(example_ids, category):
    if example_ids == []:
        return []
    else:   
        return [example_id for example_id in example_ids if get_category_of_example_id(example_id) == category]

def filter_examples_by_length(examples, min_length, max_length):
    if min_length and max_length:
        return [example for example in examples if len(example['sentence']) >= min_length and len(example['sentence']) <= max_length]
    elif min_length:
        return [example for example in examples if len(example['sentence']) >= min_length]
    elif max_length:
        return [example for example in examples if len(example['sentence']) <= max_length]
    else:
        return examples

def filter_examples_by_tags(examples, tags):
    if len(tags) <= 0:
        return examples
    deck_names = tagger.get_decks_by_tags(tags)
    return [example for example in examples if example['deck_name'] in deck_names]

def filter_examples_by_level(user_levels, examples):
    if not user_levels:
        return examples
    new_examples = []
    for example in examples:
        new_word_count = 0
        for word in example['word_base_list']:
            if dictionary.is_entry(word):
                first_entry = dictionary.get_first_entry(word)
                if not word_is_within_difficulty(user_levels, first_entry):
                    new_word_count += 1
        if new_word_count <= NEW_WORDS_TO_USER_PER_SENTENCE:
            new_examples.append(example)
    return new_examples

def filter_examples_by_exact_match(examples, text):
    return [example for example in examples if text in example['sentence']]

def limit_examples(examples):
    example_count_map = {}
    new_examples = []
    for example in examples:
        deck_name = example['deck_name']
        if deck_name not in example_count_map:
            example_count_map[deck_name] = 0
        example_count_map[deck_name] += 1
        if (example_count_map[deck_name] <= EXAMPLE_LIMIT):
            new_examples.append(example)
    return new_examples[:RESULTS_LIMIT] 