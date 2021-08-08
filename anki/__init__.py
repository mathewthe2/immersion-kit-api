import pathlib
import genanki
import random
import requests
import os
from pathlib import Path
from config import RESOURCES_PATH

DECK_ID = 2137715748
DECK_NAME = 'Immersion Kit'

# model_id = random.randrange(1 << 30, 1 << 31)

anime_model = genanki.Model(
     1239585222,
    'Immersion Kit Default',
  fields=[
    {'name': 'ID'},
    {'name': 'Expression'},
    {'name': 'English'},
    {'name': 'Reading'},
    {'name': 'Screenshot'},
    {'name': 'Audio Sentence'},
  ],
  templates=[
    {
      'name': 'Sentence',
      'qfmt': '<h1>{{Expression}}</h1>{{Screenshot}}',
      'afmt': '{{FrontSide}}<hr id="answer"><div style="font-size: 20px">{{Audio Sentence}} {{furigana:Reading}}</div ><br/><div style="font-size: 20px">{{English}}</div>',
    },
  ])

def generate_deck(sentence):
  # deck_id = random.randrange(1 << 30, 1 << 31)
  deck_id = DECK_ID
  deck_name = DECK_NAME

  my_deck = genanki.Deck(
    deck_id,
    deck_name)

  # Download Image
  response = requests.get(sentence["image_url"])
  image_file_name = Path(RESOURCES_PATH, "images", sentence["image"])
  file = open(image_file_name, "wb")
  file.write(response.content)
  file.close()

  # Download Sound
  response = requests.get(sentence["sound_url"])
  sound_file_name = Path(RESOURCES_PATH, "sound", sentence["sound"])
  file = open(sound_file_name, "wb")
  file.write(response.content)
  file.close()

  my_note = genanki.Note(
  model=anime_model,
  fields=[
    sentence["id"], 
    sentence["sentence"], 
    sentence["translation"], 
    sentence["sentence_with_furigana"], 
    '<img src="{}">'.format(sentence["image"]), 
    '[sound:{}]'.format(sentence["sound"])
  ])

  my_deck.add_note(my_note)
  file_name = '{}.apkg'.format(sentence['id'])
  file_name_with_path = Path(RESOURCES_PATH, "decks", file_name)
  if not os.path.exists(file_name_with_path):
    open(file_name_with_path, 'w').close()
  if os.path.exists(file_name_with_path):
    my_package = genanki.Package(my_deck)
    my_package.media_files = [image_file_name, sound_file_name]
    my_package.write_to_file(file_name_with_path)
  os.remove(image_file_name)
  os.remove(sound_file_name)
  return file_name


def generate_list_deck(deck_name, sentences):
  deck_id = random.randrange(1 << 30, 1 << 31)

  list_deck = genanki.Deck(
    deck_id,
    deck_name)

  media_paths = []

  for sentence in sentences:
    note = genanki.Note(
      model=anime_model,
      fields=[
        sentence["id"], 
        sentence["sentence"], 
        sentence["translation"], 
        sentence["sentence_with_furigana"], 
        '<img src="{}">'.format(sentence["image"]), 
        '[sound:{}]'.format(sentence["sound"])
      ])
    
    list_deck.add_note(note)
    media_paths.append(Path(RESOURCES_PATH, "images", sentence["sound"]))
    media_paths.append(Path(RESOURCES_PATH, "sound", sentence["sound"]))

  file_name = '{}.apkg'.format(deck_name)
  file_name_with_path = Path(RESOURCES_PATH, "decks", file_name)
  if not os.path.exists(file_name_with_path):
    open(file_name_with_path, 'w').close()
  if os.path.exists(file_name_with_path):
    my_package = genanki.Package(list_deck)
    my_package.media_files = media_paths
    my_package.write_to_file(file_name_with_path)
  return file_name