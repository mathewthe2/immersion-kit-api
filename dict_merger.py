import json
import zipfile
from pathlib import Path
from config import DICTIONARY_PATH

def is_kanji(c):
    c = ord(c)
    return (c >= 0x4e00 and c <= 0x9faf) or (c >= 0x3400 and c <= 0x4dbf)

def has_kanji(s):
    for c in s:
       if (is_kanji(c)):
           return True
    return False

def add_tag(s, tag):
    if s == "":
        return tag
    else:
        return s + " " + tag

def load_dictionary(dictionary_name):
    dictionary_path = Path(DICTIONARY_PATH, dictionary_name + '.zip')
    if dictionary_path:
        dictionary_map = load_dictionary_by_path(str(dictionary_path))
        return dictionary_map
    else:
        print('failed to find path for dictionary')

def load_dictionary_by_path(dictionary_path):
    output_map = {}
    archive = zipfile.ZipFile(dictionary_path, 'r')

    result = list()
    for file in archive.namelist():
        if file.startswith('term'):
            with archive.open(file) as f:
                data = f.read()
                d = json.loads(data.decode("utf-8"))
                result.extend(d)

    for entry in result:
        # entry_key = entry[0] + ' | ' + entry[1]
        if (entry[0] in output_map):
            output_map[entry[0]].append(entry)
        else:
            output_map[entry[0]] = [entry] # Using headword as key for finding the dictionary entry
        if (entry[1] in output_map):
            output_map[entry[1]].append(entry)
        else:
            output_map[entry[1]] = [entry] # Using headword as key for finding the dictionary entry
    return output_map

# load_dictionary('JMdict+')
# print(dictionary_map)

dictionary_map = load_dictionary('JMdict+')
core_entries = {}
combined = {}
missed = []

# with open(Path(DICTIONARY_PATH, 'jmdict_custom.json'), 'w+', encoding='utf8') as outfile:
#     json.dump(dictionary_map, outfile, indent=4, ensure_ascii=False)

with open(Path(DICTIONARY_PATH, 'jmdict_custom.json'), encoding='utf-8') as f:
    jmdict = json.load(f)

with open(Path(DICTIONARY_PATH, 'deck.json'), encoding='utf-8') as f:
    data = json.load(f)
    notes = data['notes']
    for note in notes:
        headword = note['fields'][0]
        reading = note['fields'][2]
        glossary = note['fields'][3]
        if (note['fields'][4] != ""):
            sound = note['fields'][4].split('sound:')[1].split(']')[0]
        core_entries[headword] = {
            "reading": reading,
            "glossary": glossary,
            "sound": sound
        }
        # if headword in jmdict:
        #     has_same_reading = False
        #     for entry in jmdict[headword]:
        #         if entry[1] == reading:
        #             has_same_reading = True
        #     if (not has_same_reading and has_kanji(headword)):
        #         print('no same reading for{} {}'.format(headword, reading))


for item in jmdict:
    in_core = item in core_entries
    combined_item = jmdict[item]
    is_kana_with_multiple_kanji = len(combined_item) > 1 and not has_kanji(item)
    tag = "6K"
    if in_core and not is_kana_with_multiple_kanji:
        has_same_reading = False
        for index, entry in enumerate(combined_item):
            if entry[1] == core_entries[item]["reading"]:
                has_same_reading = True
                combined_item[index].append(core_entries[item]["sound"])
                combined_item[index][7] = add_tag(combined_item[index][7], tag)
            else:
                combined_item[index].append("")
        if not has_same_reading:
            if not has_kanji(item):
                combined_item[0][8] = core_entries[item]["sound"]
                combined_item[0][7] = add_tag(combined_item[0][7], tag)
            else:
                combined_item[0][8] = "TO UPDATE WITH CORE VOICE"
    else:
        for i in range(len(combined_item)):
            combined_item[i].append("")
    combined[item] = combined_item

with open(Path(DICTIONARY_PATH, 'jmdict_combined.json'), 'w+', encoding='utf8') as outfile:
    json.dump(combined, outfile, indent=4, ensure_ascii=False)


# with open(Path(DICTIONARY_PATH, 'data.json'), 'w+', encoding='utf8') as outfile:
#     json.dump(entries, outfile, indent=4, ensure_ascii=False)
#         partsOfSpeech = note['fields'][5]
#         print(sound)