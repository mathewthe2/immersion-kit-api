import json
import re
from pathlib import Path
from glob import glob
from tokenizer.englishtokenizer import analyze_english
from tokenizer.japanesetokenizer import add_furigana
from sudachipy import tokenizer
from sudachipy import dictionary
from config import ANIME_PATH, DECK_CATEGORIES, DRAMA_PATH, NEWS_PATH, LITERATURE_PATH, GAMEGENGO_PATH, GAMES_PATH
# from db_scripts import get_data

tokenizer_obj = dictionary.Dictionary(dict_type="core").create()
mode = tokenizer.Tokenizer.SplitMode.A

def get_deck_structure(path, filename):
    file = Path(path, filename, 'deck-structure.json')
    with open(file, encoding='utf-8') as f:
        data = json.load(f)
        return data
    
def remove_class_from_string(s):
    if '>' in s:
        return s.split('>')[1].split('<')[0]
    else:
        return s

def parse_grammar_deck(filename):
    deck_structure = get_deck_structure(GAMEGENGO_PATH, filename)
    file = Path(GAMEGENGO_PATH, filename, 'deck.json')
    examples = []
    with open(file, encoding='utf-8') as f:
        data = json.load(f)
        notes = data['notes']
        deck_name = data['name']
        for note in notes:
            # segmentation
            text = note['fields'][deck_structure['text-column']]
            translation = note['fields'][deck_structure['translation-column']]
            print(note['fields'][deck_structure['grammar-column']])
            grammar = remove_class_from_string(note['fields'][deck_structure['grammar-column']])
            id = note['fields'][deck_structure['id-column']]
            print('parsing note', id)
            example = {
                'id': id,
                'deck_name': deck_name,
                'sentence': text,
                'grammar': grammar,
                'grammar_meaning': note['fields'][deck_structure['grammar-meaning-column']],
                'sentence_with_furigana': note['fields'][deck_structure['text-with-furigana-column']],
                'translation': translation,
                'timestamp': note['fields'][deck_structure['timestamp-column']],
                'image': note['fields'][deck_structure['image-column']].split('src="')[1].split('">')[0],
                'sound': note['fields'][deck_structure['sound-column']].split('sound:')[1].split(']')[0]
            }
            examples.append(example)

    with open(Path(GAMEGENGO_PATH, filename, 'data.json'), 'w+', encoding='utf8') as outfile:
        json.dump(examples, outfile, indent=4, ensure_ascii=False)

def get_timestamp_url(url, sound_string):
    sound = sound_string.split('sound:')[1].split(']')[0]
    raw_time = sound.split('-')[1].split('_')[-1]
    print('raw_time', raw_time)
    hours, minutes, seconds, milliseconds = raw_time.split('.')
    total_seconds = int(hours) * 3600 + int(minutes) * 60 + int(seconds)
    return '{}?t={}'.format(url, total_seconds)

def parse_news_deck(filename):
    meta_data_file = Path(NEWS_PATH, filename, 'metadata.json')
    deck_structure = get_deck_structure(NEWS_PATH, filename)
    metadata = {}
    with open(meta_data_file, encoding='utf-8') as f:
        metadata = json.load(f)
    file = Path(NEWS_PATH, filename, 'deck.json')
    examples = []
    repeat_ids = []
    ids = set()
    with open(file, encoding='utf-8') as f:
        data = json.load(f)
        notes = data['notes']
        deck_name = metadata['title_english']
        for note in notes:
            # segmentation
            text = note['fields'][deck_structure['text-column']]
            text = normalizeSentence(text)
            has_furigana = 'text-with-furigana-column' in deck_structure
            furigana = ''
            if has_furigana:
                furigana = note['fields'][deck_structure['text-with-furigana-column']]
                furigana = normalizeSentence(furigana) 
            else:
                furigana = add_furigana(text)
            word_base_list = [m.normalized_form() for m in tokenizer_obj.tokenize(text, mode)]
            word_dictionary_list = [m.dictionary_form() for m in tokenizer_obj.tokenize(text, mode)]
            word_list = [m.surface() for m in tokenizer_obj.tokenize(text, mode)]
            # translation = note['fields'][deck_structure['translation-column']]
            # translation_tokens = analyze_english(translation)
            # translation_word_list = translation_tokens['tokens']
            # translation_word_base_list = translation_tokens['base_tokens']
            id = note['fields'][deck_structure['id-column']]
            print('parsing note', id)
            if id in ids:
                repeat_ids.append(id)
            else:
                ids.add(id)
            example = {
                'id': note['fields'][deck_structure['id-column']],
                'timestamp': get_timestamp_url(metadata['url'], note['fields'][deck_structure['sound-column']]),
                'deck_name': deck_name,
                'deck_name_japanese': metadata["title"],
                'channel': metadata["channel"],
                'sentence': text,
                'sentence_with_furigana': furigana,
                'word_base_list': word_base_list,
                'word_dictionary_list': word_dictionary_list,
                'word_list': word_list,
                # 'translation_word_list': translation_word_list,
                # 'translation_word_base_list': translation_word_base_list,
                # 'translation': translation,
                'image': note['fields'][deck_structure['image-column']].split('src="')[1].split('">')[0],
                'sound': note['fields'][deck_structure['sound-column']].split('sound:')[1].split(']')[0]
            }
            examples.append(example)

    with open(Path(NEWS_PATH, filename, 'data.json'), 'w+', encoding='utf8') as outfile:
        json.dump(examples, outfile, indent=4, ensure_ascii=False)

    print('No repeat ids') if repeat_ids == [] else print('repeat ids', repeat_ids)

def parse_literature_deck(filename, skip_author=True):
    meta_data_file = Path(LITERATURE_PATH, filename, 'metadata.json')
    metadata = {}
    with open(meta_data_file, encoding='utf-8') as f:
        metadata = json.load(f)
    file = Path(LITERATURE_PATH, filename, 'deck.json')
    examples = []
    with open(file, encoding='utf-8') as f:
        data = json.load(f)
        for index, entry in enumerate(data):
            if (skip_author and index == 0) or (skip_author and index == 1 and '訳' in entry['sentence']):
                continue
            text = entry["sentence"]
            word_base_list = [m.normalized_form() for m in tokenizer_obj.tokenize(text, mode)]
            word_dictionary_list = [m.dictionary_form() for m in tokenizer_obj.tokenize(text, mode)]
            word_list = [m.surface() for m in tokenizer_obj.tokenize(text, mode)]
            print('name', filename)
            print('parsing note', entry["id"])
            example = {
                'id': filename + "-" + entry["id"],
                # 'author': metadata["author_english"],
                'author_japanese': metadata["author"],
                'deck_name': filename,
                'deck_name_japanese': metadata["title"],
                'sentence': text,
                'sentence_with_furigana': entry["sentence_with_furigana"],
                'word_base_list': word_base_list,
                'word_dictionary_list': word_dictionary_list,
                'word_list': word_list,
                'sound': entry["id"] + '.mp3',
                'sound_begin':  entry["audio_begin"],
                'sound_end':  entry["audio_end"]
            }
            examples.append(example)

    with open(Path(LITERATURE_PATH, filename, 'data.json'), 'w+', encoding='utf8') as outfile:
        json.dump(examples, outfile, indent=4, ensure_ascii=False)

def check_empty_sentences(filename, path=ANIME_PATH):
    deck_structure = get_deck_structure(path, filename)
    file = Path(path, filename, 'deck.json')
    with open(file, encoding='utf-8') as f:
        data = json.load(f)
        notes = data['notes']
        for note in notes:
            # segmentation
            text = note['fields'][deck_structure['translation-column']]
            if len(text) == 0:
                print(note['fields'][deck_structure['id-column']])
    print("done")
    return

def normalizeSentence(text):
    if "~" in text:
        text = text.replace("~", "～")
    return text

def parse_deck(filename, path=ANIME_PATH, ignore_untranslated=True, add_episode=False):
    deck_structure = get_deck_structure(path, filename)
    file = Path(path, filename, 'deck.json')
    examples = []
    repeat_ids = []
    ids = set()
    with open(file, encoding='utf-8') as f:
        data = json.load(f)
        is_single_deck = True if "children" not in data else len(data["children"]) == 0 
        notes = []
        episode_numbers = []
        if is_single_deck:
            notes = data['notes']
            if (ignore_untranslated):
                notes = [note for note in notes if len(note['fields'][deck_structure['translation-column']]) > 0]
        else:
            for subdeck_index, child in enumerate(data['children']):
                for note in child['notes']:
                    if (not ignore_untranslated or len(note['fields'][deck_structure['translation-column']]) > 0):
                        notes.append(note)
                        episode_numbers.append(subdeck_index+1)
        deck_name = data['name']
        for noteIndex, note in enumerate(notes):
            # segmentation
            text = note['fields'][deck_structure['text-column']]
            text = normalizeSentence(text)
            has_furigana = 'text-with-furigana-column' in deck_structure
            furigana = ''
            if has_furigana:
                furigana = note['fields'][deck_structure['text-with-furigana-column']]
                furigana = normalizeSentence(furigana) 
            else:
                furigana = add_furigana(text)
            word_base_list = [m.normalized_form() for m in tokenizer_obj.tokenize(text, mode)]
            word_dictionary_list = [m.dictionary_form() for m in tokenizer_obj.tokenize(text, mode)]
            word_list = [m.surface() for m in tokenizer_obj.tokenize(text, mode)]
            translation = note['fields'][deck_structure['translation-column']]
            translation_tokens = analyze_english(translation)
            translation_word_list = translation_tokens['tokens']
            translation_word_base_list = translation_tokens['base_tokens']
            id = note['fields'][deck_structure['id-column']]
            print('parsing note', id)
            if id in ids:
                repeat_ids.append(id)
            else:
                ids.add(id)
            example = {
                'id': note['fields'][deck_structure['id-column']],
                'deck_name': deck_name,
                'sentence': text,
                'sentence_with_furigana': furigana,
                'word_base_list': word_base_list,
                'word_dictionary_list': word_dictionary_list,
                'word_list': word_list,
                'translation_word_list': translation_word_list,
                'translation_word_base_list': translation_word_base_list,
                'translation': translation,
                'image': note['fields'][deck_structure['image-column']].split('src="')[1].split('">')[0],
                'sound': note['fields'][deck_structure['sound-column']].split('sound:')[1].split(']')[0]
            }
            if not is_single_deck:
                example['episode'] = episode_numbers[noteIndex]
            if add_episode:
                episode = int(note['fields'][deck_structure['image-column']].split(".")[0].split("_")[-2])
                example['episode'] = episode
            examples.append(example)

    with open(Path(path, filename, 'data.json'), 'w+', encoding='utf8') as outfile:
        json.dump(examples, outfile, indent=4, ensure_ascii=False)

    print('No repeat ids') if repeat_ids == [] else print('repeat ids', repeat_ids)

# def parse_all_literature_decks():
#     deck_folders = glob(str(LITERATURE_PATH) + '/*/')
#     for deck_folder in deck_folders:
#         parse_literature_deck(Path(deck_folder).name, skip_author=True)

def parse_generic(PATH, deck_folder):
    if PATH == ANIME_PATH:
         parse_deck(Path(deck_folder).name)
    elif PATH == LITERATURE_PATH:
        parse_literature_deck(Path(deck_folder).name, skip_author=True)
    # elif PATH == GAMES_PATH:
    #     parse_game_deck(Path(deck_folder).name)
    elif PATH == NEWS_PATH:
        parse_news_deck(Path(deck_folder).name)

def add_id(filename, prefix_name, path=ANIME_PATH):
    file = Path(path, filename, 'deck.json')
    deck_structure = get_deck_structure(path, filename)
    with open(file, encoding='utf-8') as f:
        data = json.load(f)
        for i, note in enumerate(data['notes']):
            raw_id = data['notes'][i]['fields'][deck_structure["id-column"]]
            if len(raw_id) == 0:
                image_string = data['notes'][i]['fields'][deck_structure["image-column"]]
                raw_id = image_string.split('src="')[1].split('.jpg')[0]
            else:
                raw_id = prefix_name + '_' + raw_id
            data['notes'][i]['fields'][deck_structure["id-column"]] = raw_id
    with open(Path(path, filename, 'out.json'), 'w+', encoding='utf8') as outfile:
        json.dump(data, outfile, indent=4, ensure_ascii=False)


def add_furigana_to_deck(filename, path=ANIME_PATH):
    file = Path(path, filename, 'deck.json')
    deck_structure = get_deck_structure(path, filename)
    with open(file, encoding='utf-8') as f:
        data = json.load(f)
        for i, note in enumerate(data['notes']):
            furigana = add_furigana(data['notes'][i]['fields'][deck_structure["text-column"]])
            print(furigana)
            data['notes'][i]['fields'][deck_structure['text-with-furigana-column']] = furigana
    with open(Path(path, filename, 'out.json'), 'w+', encoding='utf8') as outfile:
        json.dump(data, outfile, indent=4, ensure_ascii=False)

def parse_all_decks(PATH=ANIME_PATH):
    deck_folders = glob(str(PATH) + '/*/')
    for deck_folder in deck_folders:
        parse_generic(PATH, deck_folder)
    
def export_deck_statistics(path=LITERATURE_PATH, contributor="Mathew Chan"):
    deck_folders = glob(str(path) + '/*/')
    result = []
    for deck_folder in sorted(deck_folders):
        file = Path(deck_folder, 'data.json')
        with open(file, encoding='utf-8') as f:
            data = json.load(f)
            print('{}: {}'.format(Path(deck_folder).name, len(data)))
            temp_result = {
                "name": Path(deck_folder).name,
                "sentences": len(data),
                "contributor": contributor
            }
            sorting = None
            if Path(deck_folder, 'metadata.json').is_file():
                with open(Path(deck_folder, 'metadata.json'), encoding='utf-8') as f_meta:
                    meta_data = json.load(f_meta)
                    if ('title' in meta_data):
                        temp_result["name"] = meta_data['title']
                    if ('author' in meta_data):
                        temp_result['author'] = meta_data['author']
                        if sorting is None:
                            sorting = 'author'
                    if ('channel' in meta_data):
                        temp_result['channel'] = meta_data['channel']
                        if sorting is None:
                            sorting = 'channel'
            result.append(temp_result)

    if sorting == 'author':
        result = sorted(result, key=lambda deck_meta: deck_meta['author'])
    elif sorting == 'channel':
        result = sorted(result, key=lambda deck_meta: deck_meta['channel'])

    with open('statistics.json', 'w+', encoding='utf8') as outfile:
        json.dump(result, outfile, indent=4, ensure_ascii=False)


def print_deck_statistics(path=ANIME_PATH):
    deck_folders = glob(str(path) + '/*/')
    total_notes = 0
    for deck_folder in sorted(deck_folders):
        file = Path(deck_folder, 'data.json')
        with open(file, encoding='utf-8') as f:
            data = json.load(f)
            print('{}: {}'.format(Path(deck_folder).name, len(data)))
            total_notes += len(data)
    print("Total {} decks with {} notes".format(len(deck_folders), total_notes))

# Add data from one column in data.json to grammar.json and output to new.json
# grammar.json is a manually patched version of data.json  
def add_column_to_gamegengo(filename, column):
    file = Path(GAMEGENGO_PATH, filename, 'data.json')
    newdata = []
    with open(file, encoding='utf-8') as f:
        data = json.load(f)
        file_to_write = Path(GAMEGENGO_PATH, filename, 'grammar.json')
        with open(file_to_write, encoding='utf-8') as f2:
            old_data = json.load(f2)
            for index, item in enumerate(old_data):
                d = item
                d[column] = data[index][column]
                newdata.append(d)

    with open(Path(GAMEGENGO_PATH, filename, 'new.json'), 'w+', encoding='utf8') as outfile:
        json.dump(newdata, outfile, indent=4, ensure_ascii=False)

def combine_deck(filename, filename2, out, path=ANIME_PATH):
    # Assuming no sub-decks for either deck
    file = Path(path, filename, 'deck.json')
    file_structure = Path(path, filename, 'deck-structure.json')
    file2 = Path(path, filename2, 'deck.json')
    file2_structure = Path(path, filename2, 'deck-structure.json')
    with open(file, encoding='utf-8') as f:
        data = json.load(f)
    with open(file2, encoding='utf-8') as f2:
        data2 = json.load(f2)
    data["media_files"] += data2["media_files"]
    with open(file_structure, encoding='utf-8') as f:
        deck_structure = json.load(f)
    with open(file2_structure, encoding='utf-8') as f:
        deck2_structure = json.load(f)
    same_deck_structure = True
    for field in deck_structure:
        if deck_structure[field] != deck2_structure[field]:
            same_deck_structure = False
    if same_deck_structure:
        data["notes"] += data2["notes"]
    else:
        data2_notes = data2["notes"]
        for noteIndex, note in enumerate(data2["notes"]):
            new_field = [""] * (1+max(deck_structure.values()))
            for field in deck_structure:
                new_field[deck_structure[field]] = note["fields"][deck2_structure[field]]
            data2_notes[noteIndex]["fields"] = new_field
        data["notes"] += data2_notes
    with open(Path(path, out, 'deck.json'), 'w+', encoding='utf8') as outfile:
        json.dump(data, outfile, indent=4, ensure_ascii=False)

def remove_artifcats_in_translation(filename, path=ANIME_PATH):
    file = Path(path, filename, 'deck.json')
    file_structure = Path(path, filename, 'deck-structure.json')
    with open(file_structure, encoding='utf-8') as f:
        deck_structure = json.load(f)
    with open(file, encoding='utf-8') as f:
        data = json.load(f)
        total = 0
        for note in data['notes']:
            translation = note['fields'][deck_structure['translation-column']]
            if '{' in translation  and '}' in translation:
                print(translation)
                total += 1

        print(total)
                # print(re.sub("[\(\[].*?[\)\]]", "", translation))

def add_chapter_to_game(filename):
    file = Path(GAMES_PATH, filename, 'data.json')
    sentences = []
    with open(file, encoding='utf-8') as f:
        data = json.load(f)
        for sentence in data:
            chapter = sentence["id"].split('-')[1]
            sentence["episode"] = int(chapter)
            sentences.append(sentence)

    with open(Path(GAMES_PATH, filename, 'out.json'), 'w+', encoding='utf8') as outfile:
        json.dump(sentences, outfile, indent=4, ensure_ascii=False)

def add_chapter_to_game(filename):
    file = Path(GAMES_PATH, filename, 'data.json')
    sentences = []
    with open(file, encoding='utf-8') as f:
        data = json.load(f)
        for sentence in data:
            chapter = sentence["id"].split('-')[1]
            sentence["episode"] = int(chapter)
            sentences.append(sentence)

    with open(Path(GAMES_PATH, filename, 'out.json'), 'w+', encoding='utf8') as outfile:
        json.dump(sentences, outfile, indent=4, ensure_ascii=False)

# def parse_game_deck(filename):
#     meta_data_file = Path(GAMES_PATH, filename, 'metadata.json')
#     metadata = {}
#     with open(meta_data_file, encoding='utf-8') as f:
#         metadata = json.load(f)
#     data = get_data(metadata['deck_name'], metadata['chapters'])
#     examples = []
#     for note in data:
#         print('note', note)
#         text = note['sentence']
#         word_base_list = [m.normalized_form() for m in tokenizer_obj.tokenize(text, mode)]
#         word_dictionary_list = [m.dictionary_form() for m in tokenizer_obj.tokenize(text, mode)]
#         word_list = [m.surface() for m in tokenizer_obj.tokenize(text, mode)]
#         translation = note['translation']
#         translation_tokens = analyze_english(translation)
#         translation_word_list = translation_tokens['tokens']
#         translation_word_base_list = translation_tokens['base_tokens']
#         item = {
#             'id': note['id'],
#             'deck_name': note['deck_name'],
#             'sentence': text,
#             'sentence_with_furigana': note['sentence_with_furigana'],
#             'word_base_list': word_base_list,
#             'word_dictionary_list': word_dictionary_list,
#             'word_list': word_list,
#             'translation_word_list': translation_word_list,
#             'translation_word_base_list': translation_word_base_list,
#             'translation': translation,
#             'image_url': note['image_url'],
#             'sound_url': note['sound_url'],
#         }
#         examples.append(item)

#     with open(Path(GAMES_PATH, filename, 'data.json'), 'w+', encoding='utf8') as outfile:
#         json.dump(examples, outfile, indent=4, ensure_ascii=False)

# remove_artifcats_in_translation("Clannad After Story")
# combine_deck("k1", "k2", "God's Blessing on this Wonderful World!")
# add_furigana_to_deck("Chobits")
# add_id("New Game!", 'New_Game!')
# parse_game_deck("NieR Reincarnation")
# parse_deck("Angel Beats!")
# parse_all_decks(NEWS_PATH)
# check_empty_sentences("Steins Gate")
# check_empty_sentences("I am Mita, Your Housekeeper", path=DRAMA_PATH)
# parse_all_decks(NEWS_PATH)
# print_deck_statistics(ANIME_PATH)
# parse_game_deck('Nier Reincarnation')
# parse_game_deck('Zelda Breath of the Wild')

# parse_grammar_deck('Game Gengo Grammar N4')
# add_column_to_gamegengo('Game Gengo Grammar N4', 'timestamp')
# parse_all_decks(ANIME_PATH)
# parse_deck("Princess Mononoke", ANIME_PATH)
