import genanki

custom_css = ".card {\n font-family: 'localnoto', 'notosans', 'ヒラギノ明朝 ProN', 'Hiragino Mincho Pro', 'serif';\n font-size: 25px;\n text-align: center;\n color: White; \n background-color: Black;\n}\n"

SENTENCE_MODEL = genanki.Model(
  1239585222,
  'Immersion Kit Sentence',
  css=custom_css,
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

AUDIO_MODEL = genanki.Model(
  1500274576,
  'Immersion Kit Audio',
  css=custom_css,
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
      'name': 'Audio',
      'qfmt': '<div style="display: none">{{Audio Sentence}}</div>{{Screenshot}}',
      'afmt': '{{FrontSide}}<hr id="answer"><div style="font-size: 20px">{{Audio Sentence}} {{furigana:Reading}}</div ><br/><div style="font-size: 20px">{{English}}</div>',
    },
  ])

VOCABULARY_MODEL = genanki.Model(
     2023469461,
    'Immersion Kit Vocabulary',
    css=custom_css,
  fields=[
    {'name': 'ID'},
    {'name': 'Vocabulary-Kanji'},
    {'name': 'Vocabulary-Reading'},
    {'name': 'Vocabulary-English'},
    {'name': 'Vocabulary-Audio'},
    {'name': 'Expression'}, # Sentence
    {'name': 'Sentence-English'},
    {'name': 'Screenshot'},
    {'name': 'Sentence-Audio'},
  ],
  templates=[
    {
      'name': 'Vocabulary',
      'qfmt': '<span style="font-size: 50px;  ">{{Vocabulary-Kanji}}</span>',
      'afmt': '<div>{{Vocabulary-Audio}}{{Sentence-Audio}}</div>{{FrontSide}}<hr id="answer">{{Screenshot}}<div style="font-size: 20px">{{Vocabulary-Reading}}</div><div style="font-size: 20px">{{Vocabulary-English}}</div ><br/><div style="font-size: 20px">{{Expression}}</div><div style="font-size: 20px">{{Sentence-English}}</div>',
    },
  ])

ANKI_MODELS = {
    "audio": AUDIO_MODEL,
    "sentence": SENTENCE_MODEL,
    "vocabulary": VOCABULARY_MODEL
}
