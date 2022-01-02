import genanki
import requests
import os
from pathlib import Path
from config import RESOURCES_PATH, DEFAULT_ANKI_MODEL
from anki.anki_models import ANKI_MODELS

DECK_ID = 2137715748
DECK_NAME = 'Immersion Kit'

# import random
# model_id = random.randrange(1 << 30, 1 << 31)

def generate_deck(sentence, model_type=DEFAULT_ANKI_MODEL):
  # deck_id = random.randrange(1 << 30, 1 << 31)
  deck_id = DECK_ID
  deck_name = DECK_NAME

  my_deck = genanki.Deck(
    deck_id,
    deck_name)

  # Download Image
  response = requests.get(sentence["image_url"])
  image_name = os.path.basename(sentence["image_url"])
  image_file_path = Path(RESOURCES_PATH, "images", image_name)
  file = open(image_file_path, "wb")
  file.write(response.content)
  file.close()

  # Download Sound
  response = requests.get(sentence["sound_url"])
  sound_name = os.path.basename(sentence["sound_url"])
  sound_file_path = Path(RESOURCES_PATH, "sound", sound_name)
  file = open(sound_file_path, "wb")
  file.write(response.content)
  file.close()

  if model_type not in ANKI_MODELS:
    model_type = DEFAULT_ANKI_MODEL

  my_note = genanki.Note(
  model=ANKI_MODELS[model_type],
  fields=[
    sentence["id"], 
    sentence["sentence"], 
    sentence["translation"], 
    sentence["sentence_with_furigana"], 
    '<img src="{}">'.format(image_name), 
    '[sound:{}]'.format(sound_name)
  ])

  my_deck.add_note(my_note)
  file_name = '{}.apkg'.format(sentence['id'])
  file_name_with_path = Path(RESOURCES_PATH, "decks", file_name)
  if not os.path.exists(file_name_with_path):
    open(file_name_with_path, 'w').close()
  if os.path.exists(file_name_with_path):
    my_package = genanki.Package(my_deck)
    my_package.media_files = [image_file_path, sound_file_path]
    my_package.write_to_file(file_name_with_path)
  os.remove(image_file_path)
  os.remove(sound_file_path)
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