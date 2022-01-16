import genanki
import requests
import os
from pathlib import Path
from config import RESOURCES_PATH, DEFAULT_ANKI_MODEL, DICTIONARY_MEDIA_HOST
from search import dictionary
from anki.anki_models import ANKI_MODELS
from anki.audio import get_jpod_audio_url

DECK_ID = 2137715748
DECK_NAME = 'Immersion Kit'

# import random
# model_id = random.randrange(1 << 30, 1 << 31)

def generate_deck(sentence, vocabulary_position=None, model_type=DEFAULT_ANKI_MODEL):
  # deck_id = random.randrange(1 << 30, 1 << 31)
  deck_id = DECK_ID
  deck_name = DECK_NAME

  my_deck = genanki.Deck(
    deck_id,
    deck_name)

  asset_file_paths = []

  # Download Image
  response = requests.get(sentence["image_url"])
  image_name = os.path.basename(sentence["image_url"])
  image_file_path = Path(RESOURCES_PATH, "images", image_name)
  file = open(image_file_path, "wb")
  file.write(response.content)
  file.close()
  asset_file_paths.append(image_file_path)

  # Download Sentence Sound
  response = requests.get(sentence["sound_url"])
  sound_name = os.path.basename(sentence["sound_url"])
  sound_file_path = Path(RESOURCES_PATH, "sound", sound_name)
  file = open(sound_file_path, "wb")
  file.write(response.content)
  file.close()
  asset_file_paths.append(sound_file_path)

  if model_type not in ANKI_MODELS:
    model_type = DEFAULT_ANKI_MODEL

  fields = []
  if model_type in ['audio', 'sentence']:
    fields = [
    sentence["sentence"], 
    sentence["translation"], 
    sentence["sentence_with_furigana"], 
    '<img src="{}">'.format(image_name), 
    '[sound:{}]'.format(sound_name),
    sentence["id"]
  ]
  elif model_type == 'vocabulary' and vocabulary_position is not None:
    dictionary_list = sentence["word_dictionary_list"]
    if len(dictionary_list) < vocabulary_position:
      dictionary_list = sentence["word_base_list"]
    vocabulary = dictionary_list[vocabulary_position]
    vocabulary_entry = dictionary.lookup_vocabulary(vocabulary)

    vocabulary_sound_url = vocabulary_entry['sound']
    vocabulary_sound_file_name = ""
    vocabulary_sound_name = ""
    
    if vocabulary_sound_url:
      # audio from core 6k deck
      vocabulary_sound_name = os.path.basename(vocabulary_sound_url)
    else:
      # audio from jpod 101
      vocabulary_sound_url = get_jpod_audio_url(kanji=vocabulary_entry['headword'], kana=vocabulary_entry['reading'])
      if vocabulary_sound_url:
        vocabulary_sound_name = '{}_{}.mp3'.format(vocabulary_entry['headword'], vocabulary_entry['reading'])
    
    # Download Vocab Sound
    if vocabulary_sound_url:
      response = requests.get(vocabulary_sound_url)
      vocabulary_sound_file_path = Path(RESOURCES_PATH, "sound", vocabulary_sound_name)
      vocabulary_sound_file_name = '[sound:{}]'.format(vocabulary_sound_name)
      file = open(vocabulary_sound_file_path, "wb")
      file.write(response.content)
      file.close()
      asset_file_paths.append(vocabulary_sound_file_path)

      fields = [
        vocabulary, # vocab-kanji
        vocabulary_entry['reading'], # vocab-reading
        ', '.join(vocabulary_entry["glossary_list"]), # vocab-english
        vocabulary_sound_file_name, # vocab-audio,
        sentence["sentence"], 
        sentence["sentence_with_furigana"], 
        sentence["translation"], 
        '<img src="{}">'.format(image_name), 
        '[sound:{}]'.format(sound_name),
        sentence["id"], 
      ]

  my_note = genanki.Note(
  model=ANKI_MODELS[model_type],
  fields=fields)

  my_deck.add_note(my_note)
  file_name = '{}.apkg'.format(sentence['id'])
  file_name_with_path = Path(RESOURCES_PATH, "decks", file_name)
  if not os.path.exists(file_name_with_path):
    open(file_name_with_path, 'w').close()
  if os.path.exists(file_name_with_path):
    my_package = genanki.Package(my_deck)
    my_package.media_files = asset_file_paths
    my_package.write_to_file(file_name_with_path)
  for file_path in asset_file_paths:
    os.remove(file_path)
  return file_name


# def generate_list_deck(deck_name, sentences):
#   deck_id = random.randrange(1 << 30, 1 << 31)

#   list_deck = genanki.Deck(
#     deck_id,
#     deck_name)

#   media_paths = []

#   for sentence in sentences:
#     image_name = os.path.basename(sentence["image_url"])
#     sound_name = os.path.basename(sentence["sound_url"])
#     note = genanki.Note(
#       model=anime_model,
#       fields=[
#         sentence["id"], 
#         sentence["sentence"], 
#         sentence["translation"], 
#         sentence["sentence_with_furigana"], 
#         '<img src="{}">'.format(image_name), 
#         '[sound:{}]'.format(sound_name)
#       ])
    
#     list_deck.add_note(note)
#     media_paths.append(Path(RESOURCES_PATH, "images", sound_name))
#     media_paths.append(Path(RESOURCES_PATH, "sound", sound_name))

#   file_name = '{}.apkg'.format(deck_name)
#   file_name_with_path = Path(RESOURCES_PATH, "decks", file_name)
#   if not os.path.exists(file_name_with_path):
#     open(file_name_with_path, 'w').close()
#   if os.path.exists(file_name_with_path):
#     my_package = genanki.Package(list_deck)
#     my_package.media_files = media_paths
#     my_package.write_to_file(file_name_with_path)
#   return file_name