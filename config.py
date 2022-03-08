from pathlib import Path
import os

bundle_path = os.path.dirname(os.path.abspath(__file__))
RESOURCES_PATH = Path(bundle_path, 'resources')
DICTIONARY_PATH = Path(bundle_path, 'resources', 'dictionaries')
ANIME_PATH = Path(bundle_path, 'resources', 'anime')
GAMES_PATH = Path(bundle_path, 'resources', 'games')
DRAMA_PATH = Path(bundle_path, 'resources', 'drama')
NEWS_PATH = Path(bundle_path, 'resources', 'news')
GAMEGENGO_PATH = Path(bundle_path, 'resources', 'gamegengo')
LITERATURE_PATH = Path(bundle_path, 'resources', 'literature')

# Parsing
CONTEXT_RANGE = 10

# Decks
DEFAULT_CATEGORY = 'anime'
DECK_CATEGORIES = {
    'anime': {
        'path': ANIME_PATH,
        'has_image': True,
        'has_sound': True,
        "has_resource_url": False
    },
    'games': {
        'path': GAMES_PATH,
        'has_image': False,
        'has_sound': True,
        "has_resource_url": False
    },
     'drama': {
        'path': DRAMA_PATH,
        'has_image': True,
        'has_sound': True,
        "has_resource_url": False
    },
    'news': {
        'path': NEWS_PATH,
        'has_image': True,
        'has_sound': True,
        "has_resource_url": False
    },
    'literature': {
        'path': LITERATURE_PATH,
        'has_image': False,
        'has_sound': True,
        "has_resource_url": False
    }
} 

EXTENSION_MIMETYPE_MAP = {
    'mp3': 'audio/mpeg',
    'jpg': 'image/jpeg',
    'jpeg': 'image/jpeg'
}

SENTENCE_CATEGORY_INDEX = 3 # 3rd item in sentence fields

# Sentence Format
SENTENCE_FIELDS = [
    "id", 
    "sentence_id",
    "position",
    "category",
    "episode", # for reader
    "channel", # news
    "timestamp", # news
    "deck_name",
    "deck_name_japanese", # literature, news
    "author_japanese", # literature
    "sentence",
    "sentence_with_furigana",
    "norms",
    'eng_norms',
    "wk_level",
    "jlpt_level",
    "word_base_list",
    "word_dictionary_list",
    "word_list",
    "translation_word_list",
    "translation_word_base_list",
    "translation",
    "image",
    "image_url", # games
    "sound",
    "sound_begin", # literature
    "sound_end", # literature
    "sound_url", # games
]

SENTENCE_KEYS_FOR_LISTS = ['word_list', 'word_dictionary_list', 'word_base_list', 'translation_word_list', 'translation_word_base_list']

# Anki
DEFAULT_ANKI_MODEL = 'sentence'

# Serving
MEDIA_FILE_HOST = 'https://immersion-kit.sfo3.digitaloceanspaces.com/media'
DICTIONARY_MEDIA_HOST = 'https://immersion-kit.sfo3.digitaloceanspaces.com/dictionary/media'
EXAMPLE_LIMIT = 50 # example limit per deck
RESULTS_LIMIT = 3000 # total result limit
SENTENCES_LIMIT = 999 # SQL-bound limit
NEW_WORDS_TO_USER_PER_SENTENCE = 1
RESULT_EXCLUDED_FIELDS = ["image", "sound", "norms", "eng_norms", "wk_level", "jlpt_level", "translation_word_base_list", "word_base_list", "pretext", "posttext"]