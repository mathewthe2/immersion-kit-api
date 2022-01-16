import genanki

custom_css = """.card {
font-family: 'localnoto', 'notosans', 'ヒラギノ明朝 ProN', 'Hiragino Mincho Pro', 'serif';
font-size: 50px;
text-align: center;
color: White;
background-color: Black;
}

img {
 width: auto;
 height: auto;
 max-width: 400px;
 max-height: 400px;
}

.expression {
 margin-bottom: -0.0em;
 margin-top: 1.2em;
 font-size: 25px;
}"""

SENTENCE_MODEL = genanki.Model(
  1239585222,
  'Immersion Kit Sentence',
  css=custom_css,
  fields=[
    {'name': 'Expression'},
    {'name': 'English'},
    {'name': 'Reading'},
    {'name': 'Screenshot'},
    {'name': 'Audio Sentence'},
    {'name': 'ID'}
  ],
  templates=[
    {
      'name': 'Sentence',
      'qfmt': """<div style="font-size: 25px">{{Expression}}</div>
<br/>
{{Screenshot}}""",
      'afmt': """{{FrontSide}}
<hr id="answer">
<div style="font-size: 25px">{{English}}</div>
<br/>
<div style="font-size: 20px">{{Audio Sentence}} {{furigana:Reading}}</div >
<br/>"""
    },
  ])

AUDIO_MODEL = genanki.Model(
  1500274576,
  'Immersion Kit Audio',
  css=custom_css,
  fields=[
    {'name': 'Expression'},
    {'name': 'English'},
    {'name': 'Reading'},
    {'name': 'Screenshot'},
    {'name': 'Audio Sentence'},
    {'name': 'ID'}
  ],
  templates=[
    {
      'name': 'Audio',
      'qfmt': '<div style="display: none">{{Audio Sentence}}</div>{{Screenshot}}',
      'afmt': """{{FrontSide}}
<hr id="answer">
<div style="font-size: 25px">{{furigana:Reading}}</div >
<div style="font-size: 20px">{{English}}</div>
{{Audio Sentence}}"""
    },
  ])

VOCABULARY_MODEL = genanki.Model(
     2023469461,
    'Immersion Kit Vocabulary',
    css=custom_css,
  fields=[
    {'name': 'Vocabulary-Kanji'},
    {'name': 'Vocabulary-Reading'},
    {'name': 'Vocabulary-English'},
    {'name': 'Vocabulary-Audio'},
    {'name': 'Expression'}, # Sentence
    {'name': 'Sentence-English'},
    {'name': 'Screenshot'},
    {'name': 'Sentence-Audio'},
    {'name': 'ID'},
  ],
  templates=[
    {
      'name': 'Vocabulary',
      'qfmt': '{{Vocabulary-Kanji}}',
      'afmt': """<div>
  {{Vocabulary-Audio}} {{Sentence-Audio}}
<div>
{{FrontSide}}
<hr id="answer">
<div>
  {{Vocabulary-Reading}}
</div>
<div style="font-size: 25px">
  {{Vocabulary-English}}
</div>
<br>
<div>
  {{Screenshot}}
</div>
<div class="expression">
  {{Expression}}
</div>
<div style="font-size: 25px">
  {{Sentence-English}}
</div>""",
    },
  ])

ANKI_MODELS = {
    "audio": AUDIO_MODEL,
    "sentence": SENTENCE_MODEL,
    "vocabulary": VOCABULARY_MODEL
}
