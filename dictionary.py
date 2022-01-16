import json
import zipfile
from pathlib import Path
from config import DICTIONARY_PATH, DICTIONARY_MEDIA_HOST

CUSTOM_MAPPER = {
    '食える': '食えない'
}

class Dictionary:
    def __init__(self):
        self.dictionary_map = {}  

    def is_entry(self, word):
        return word in self.dictionary_map

    def get_first_entry(self, word):
        return self.dictionary_map[word][0]

    def is_uninflectable_entry(self, word):
        if not self.is_entry(word):
            return False
        else:
            entry = self.get_first_entry(word)
            is_verb = 'vt' in entry[2]
            is_i_adjective = 'adj-i' in entry[2] 
            return not is_verb and not is_i_adjective 
            
    def load_dictionary_by_path(self, dictionary_path):
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
            if (entry[0] in output_map):
                output_map[entry[0]].append(entry)
            else:
                output_map[entry[0]] = [entry] # Using headword as key for finding the dictionary entry
        return output_map

    def load_dictionary(self, dictionary_name):
        dictionary_path = Path(DICTIONARY_PATH, dictionary_name + '.zip')
        if dictionary_path:
            self.dictionary_map = self.load_dictionary_by_path(str(dictionary_path))
        else:
            print('failed to find path for dictionary')

        dictionary_path = Path(DICTIONARY_PATH, dictionary_name + '.zip')
        archive = zipfile.ZipFile(dictionary_path, 'r')

        for file in archive.namelist():
            if file.endswith('.json'):
                with archive.open(file) as f:
                    data = f.read()
                    self.dictionary_map = json.loads(data.decode("utf-8"))

    def load_unpacked_dictionary(self, dictionary_name):
        dictionary_path = Path(DICTIONARY_PATH, dictionary_name + '.json')
        if dictionary_path:
            with open(dictionary_path, encoding='utf-8') as f:
                self.dictionary_map = json.load(f)
        else:
            print('failed to find path for dictionary')

    def get_definition(self, word):
        return self.parse_dictionary_entries(self.dictionary_map[word])

    def lookup_vocabulary(self, vocabulary):
        if self.is_entry(vocabulary):
            entry = self.get_first_entry(vocabulary)
            return self.parse_dictionary_entries([entry])[0]
        elif vocabulary in CUSTOM_MAPPER:
            return self.lookup_vocabulary(CUSTOM_MAPPER[vocabulary])
        else:
            return None

    def parse_dictionary_entries(self, entries):
        return  [{
            'headword': entry[0],
            'reading': entry[1] if entry[1] != "" else entry[0],
            'tags': entry[2],
            'glossary_list': entry[5],
            # 'sequence': entry[6],
            'sound': '{}/{}'.format(DICTIONARY_MEDIA_HOST, entry[8]) if len(entry[8]) > 0 else "" 
        } for entry in entries]