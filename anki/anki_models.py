import genanki

SENTENCE_MODEL = genanki.Model(
     1239585222,
    'Immersion Kit Sentence',
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
      'qfmt': '<div style="display: none">{{Audio Sentence}}</div> {{Screenshot}}',
      'afmt': '{{FrontSide}}<hr id="answer"><div style="font-size: 20px">{{Audio Sentence}} {{furigana:Reading}}</div ><br/><div style="font-size: 20px">{{English}}</div>',
    },
  ])

ANKI_MODELS = {
    "sentence": SENTENCE_MODEL,
    "audio": AUDIO_MODEL
}