from sudachipy import tokenizer
from sudachipy import dictionary
from wanakana import to_hiragana, is_japanese, is_katakana, is_hiragana
import string

tokenizer_obj = dictionary.Dictionary(dict_type="small").create()
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

KANJI_READING_MAPPING = {
    '私': '私[わたし]',
    '貴女': '貴女[あなた]',
    '外宇宙': '外宇宙[がいうちゅう]'
}

JAPANESE_PUNCTUATION = '　〜！？。、（）：「」『』０１２３４５６７８９ａｂｃｄｅｆｇｈｉｊｋｌｍｎｏｐｑｒｓｔｕｖｗｘｙｚＡＢＣＤＥＦＧＨＩＪＫＬＭＮＯＰＱＲＳＴＵＶＷＸＹＺ'

SPECIAL_CHARACTERS = '〜'

def analyze_japanese(text):
    tokens = [m for m in tokenizer_obj.tokenize(text, mode)]
    return {
        'tokens': [token.surface() for token in tokens],
        'base_tokens': [token.normalized_form() for token in tokens]
    }

def is_japanese_extended(text):
    return is_japanese(text) and text not in string.punctuation and text not in JAPANESE_PUNCTUATION

def add_furigana(text):
    tokens = [m for m in tokenizer_obj.tokenize(text, tokenizer.Tokenizer.SplitMode.C)]
    parsed = ''
    for index, token in enumerate(tokens):   
        to_parse = is_japanese_extended(token.surface()) and not is_katakana(token.surface()) and not is_hiragana(token.surface())
        if to_parse:
            if token.surface()[-1] in SPECIAL_CHARACTERS:
                parsed += add_furigana(token.surface()[:-1]) + token.surface()[-1]
            else:
                if index > 0:
                    parsed += ' '
                reading = to_hiragana(token.reading_form())
                if token.surface() in KANJI_READING_MAPPING:
                    parsed += KANJI_READING_MAPPING[token.surface()]
                elif is_hiragana(token.surface()[-1]):
                    hiragana_count = 1
                    while is_hiragana(token.surface()[(hiragana_count+1) * -1]):
                        hiragana_count += 1
                    parsed += '{}[{}]{}'.format(token.surface()[:hiragana_count * -1], to_hiragana(token.reading_form()[:hiragana_count * -1]), to_hiragana(token.reading_form()[hiragana_count * -1:]))
                elif is_hiragana(token.surface()[0]):
                    hiragana_count = 0
                    while is_hiragana(token.surface()[hiragana_count+1]):
                        hiragana_count += 1
                    parsed += '{} {}[{}]'.format(token.surface()[:hiragana_count+1], token.surface()[hiragana_count+1:], to_hiragana(token.reading_form()[hiragana_count+1:]))
                else:
                    parsed += '{}[{}]'.format(token.surface(), reading)
        else:
            parsed += token.surface()
    return parsed

# s = '広いな……この廃墟。'
# s = 'この先に多数の機械生命体反応を確認'
# s = '早く……'
# print(add_furigana(s))
print(analyze_japanese('我が儘'))