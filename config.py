from pathlib import Path
import os

bundle_path = os.path.dirname(os.path.abspath(__file__))
RESOURCES_PATH = Path(bundle_path, 'resources')
DICTIONARY_PATH = Path(bundle_path, 'resources', 'dictionaries')
ANIME_PATH = Path(bundle_path, 'resources', 'anime')
GAMES_PATH = Path(bundle_path, 'resources', 'games')
LIVE_ACTION_PATH = Path(bundle_path, 'resources', 'live_action')
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
        'has_image': True,
        'has_sound': True,
        "has_resource_url": True
    },
     'live_action': {
        'path': LIVE_ACTION_PATH,
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

# Sentence Format
SENTENCE_FIELDS = [
    "id", 
    "category",
    "deck_name",
    "deck_name_japanese", # literature
    "author_japanese", # literature
    "sentence",
    "sentence_with_furigana",
    "word_base_list",
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
    "pretext",
    "posttext"
]

SENTENCE_KEYS_FOR_LISTS = ['pretext', 'posttext', 'word_list', 'word_base_list', 'translation_word_list', 'translation_word_base_list']

# Serving
MEDIA_FILE_HOST = 'https://immersion-kit.sfo3.digitaloceanspaces.com/media'
EXAMPLE_LIMIT = 50 # example limit per deck
RESULTS_LIMIT = 3000 # total result limit
SENTENCES_LIMIT = 999 # SQL-bound limit
NEW_WORDS_TO_USER_PER_SENTENCE = 1