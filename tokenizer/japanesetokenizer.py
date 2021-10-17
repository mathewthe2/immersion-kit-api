from sudachipy import tokenizer
from sudachipy import dictionary
from wanakana import to_hiragana, is_japanese, is_katakana, is_hiragana
import string

tokenizer_obj = dictionary.Dictionary(dict_type="core").create()
mode = tokenizer.Tokenizer.SplitMode.A

KANA_MAPPING = {
    'ca': 'ca',
    'ci': 'ci',
    'cu': 'cu',
    'ce': 'ce',
    'co': 'co',
    'la': 'la',
    'li': 'li',
    'lu': 'lu',
    'le': 'le',
    'lo': 'lo'
}

KANA_TO_KANJI_MAPPING = {
    'じょせい': '女性'
}

KANJI_READING_MAPPING = {
    '私': '私[わたし]',
    # '檻': '檻[ケージ]',
    '貴女': '貴女[あなた]',
    '父様': '父様[とうさま]',
    '一度': '一度[いちど]',
    '許さん': '許[ゆる]さん',
    '目覚め': '目覚[めざ]め',
    '目覚める': '目覚[めざ]める',
    '何が': '何[なに]が',
    '剣': '剣[つるぎ]',
    '何を': '何[なに]を',
    '何も': '何[なに]も',
    '我国': '我国[わがくに]',
    '行き来': '行[い]き 来[き]',
    '外宇宙': '外宇宙[がいうちゅう]',
    '異星人': '異星人[いせいじん]',
    '荒野': '荒野[こうや]',
    '優那': '優那[ゆうな]',
    '菜々美': '菜々美[ななみ]'
}

JAPANESE_PUNCTUATION = '　〜！？。、（）：「」『』０１２３４５６７８９ａｂｃｄｅｆｇｈｉｊｋｌｍｎｏｐｑｒｓｔｕｖｗｘｙｚＡＢＣＤＥＦＧＨＩＪＫＬＭＮＯＰＱＲＳＴＵＶＷＸＹＺ'

SPECIAL_CHARACTERS = '〜'

def analyze_japanese(text):
    if text in KANA_TO_KANJI_MAPPING:
        text = KANA_TO_KANJI_MAPPING[text]
    tokens = [m for m in tokenizer_obj.tokenize(text, mode)]
    return {
        'tokens': [token.surface() for token in tokens],
        # 'base_tokens': [token.normalized_form() for token in tokens],
        'base_tokens': [token.dictionary_form() for token in tokens]
    }

def is_japanese_extended(text):
    return is_japanese(text) and text not in string.punctuation and text not in JAPANESE_PUNCTUATION

def to_anki_format(index, kanji, reading):
    return '{}{}[{}]'.format(' ' if index > 0 else '', kanji, reading) 

def add_furigana(text):
    tokens = [m for m in tokenizer_obj.tokenize(text, tokenizer.Tokenizer.SplitMode.C)]
    parsed = ''
    token_indexes_to_skip = []
    for index, token in enumerate(tokens):   
        if index in token_indexes_to_skip:
          continue
        to_parse = is_japanese_extended(token.surface()) and not is_katakana(token.surface()) and not is_hiragana(token.surface())
        if to_parse:
            if token.surface()[-1] in SPECIAL_CHARACTERS:
                parsed += add_furigana(token.surface()[:-1]) + token.surface()[-1]
            else:
                if index > 0:
                    parsed += ' '
                reading = to_hiragana(token.reading_form())
                if index < len(tokens)-1 and token.surface() + tokens[index+1].surface() in KANJI_READING_MAPPING:
                    parsed += KANJI_READING_MAPPING[tokens[index].surface() + tokens[index+1].surface()]
                    token_indexes_to_skip.append(index+1)
                elif token.surface() in KANJI_READING_MAPPING:
                    parsed += KANJI_READING_MAPPING[token.surface()]
                else:
                    surface_index = 0
                    reading_index = 0
                    while len(token.surface()) > surface_index:
                        if is_hiragana(token.surface()[surface_index]) or is_katakana(token.surface()[surface_index]):
                            parsed += token.surface()[surface_index]
                            reading_index += 1
                            surface_index += 1
                        else:
                            next_index = -1
                            for token_index in range(surface_index, len(token.surface())):
                                if is_hiragana(token.surface()[token_index]) or is_katakana(token.surface()[token_index]):
                                    next_index = token_index
                                    break
                            if next_index < 0:
                                parsed += to_anki_format(
                                  index=surface_index, 
                                  kanji=token.surface()[surface_index:], reading=reading[reading_index:])
                                break
                            else:
                                reading_index_tail = reading_index
                                while reading[reading_index_tail] != token.surface()[next_index] or (reading_index_tail < len(reading)-1 and reading[reading_index_tail] == reading[reading_index_tail+1]):
                                    reading_index_tail += 1
                                parsed += to_anki_format(
                                  index=surface_index, 
                                  kanji=token.surface()[surface_index:next_index], reading=reading[reading_index:reading_index_tail])
                                reading_index = reading_index_tail
                            reading_length = next_index - surface_index
                            if reading_length > 0:
                                surface_index += reading_length
                            else:
                                break
        else:
            parsed += token.surface()
    return parsed
