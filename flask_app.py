import io
import os
import requests
import urllib
from pathlib import Path
from flask import Flask, Response, request, jsonify 
from flask_cors import CORS
from werkzeug.wsgi import FileWrapper
from anki import generate_deck
from config import DEFAULT_CATEGORY, DEFAULT_ANKI_MODEL, RESOURCES_PATH, MEDIA_FILE_HOST, EXTENSION_MIMETYPE_MAP, EXAMPLE_LIMIT
from search import get_deck_by_id, look_up, get_sentence_by_id, get_sentences_for_reader, get_sentence_with_context, get_sentences_with_combinatory_ids
from data.deckData import DECK_LIST

app = Flask(__name__)
CORS(app)

@app.route('/')
def hello_world():
    return 'API Documentation: https://docs.immersionkit.com/public api/search/'

@app.route('/look_up_dictionary')
def look_up_dictionary():
    keyword = request.args.get('keyword')
    if not keyword:
        return 'No keyword specified.'
    else:
        has_tags = request.args.get('tags') is not None and request.args.get('tags') != ''
        has_jlpt = request.args.get('jlpt') is not None and request.args.get('jlpt').isdigit()
        has_wk = request.args.get('wk') is not None and request.args.get('wk').isdigit()
        has_sorting = request.args.get('sort') is not None and request.args.get('sort') != ''
        has_category = request.args.get('category') is not None and request.args.get('category') != ''
        has_min_length = request.args.get('min_length') is not None and request.args.get('min_length').isdigit()
        has_max_length = request.args.get('max_length') is not None and request.args.get('max_length').isdigit()
        user_levels = {
            'JLPT': None if not has_jlpt else int(request.args.get('jlpt')),
            'WK': None if not has_wk else int(request.args.get('wk'))
        }
        has_decks = request.args.get('decks') is not None and request.args.get('decks') != ''
        offset = request.args.get('offset', type=int, default=0)
        limit = min(EXAMPLE_LIMIT, request.args.get('limit', type=int, default=EXAMPLE_LIMIT))
        return look_up(
            text = request.args.get('keyword')[:50], 
            sorting = None if not has_sorting else request.args.get('sort'),
            min_length = None if not has_min_length else int(request.args.get('min_length')),
            max_length = None if not has_max_length else int(request.args.get('max_length')),
            category = DEFAULT_CATEGORY if not has_category else request.args.get('category'),
            tags = [] if not has_tags else request.args.get('tags').split(','),
            user_levels = user_levels,
            selected_decks = [] if not has_decks else request.args.get('decks').split(','),
            offset = offset,
            limit = limit)

@app.route('/sentence_with_context')
def sentence_with_context():
    sentence_id = request.args.get('id')
    if sentence_id is None:
        return 'No sentence id specified.'
    elif not sentence_id.isdigit():
        return {}
    else:
        return get_sentence_with_context(int(sentence_id))

@app.route('/deck')
def deck():
    deck_id = request.args.get('id')
    has_category = request.args.get('category') is not None and request.args.get('category') != ''
    if deck_id is None:
        return 'No id specified.'
    else: 
        return get_deck_by_id(request.args.get('id'), category=DEFAULT_CATEGORY if not has_category else request.args.get('category'))

@app.route('/decks')
def decks():
    return jsonify(DECK_LIST)

@app.route('/read')
def read():
    deck_id = request.args.get('id')
    episode = request.args.get('episode', type=int, default=1)
    offset = request.args.get('offset', type=int, default=0)
    limit = min(EXAMPLE_LIMIT, request.args.get('limit', type=int, default=10))
    if deck_id is None:
        return 'No id specified.'
    else: 
        return get_sentences_for_reader(deck_id, episode=episode, offset=offset, limit=limit)

@app.route('/sentences', methods=["GET", "POST"])
def sentences():
    # if request.method == 'POST':
    #     json = request.json
    #     if not json:
    #         return 'No data posted.'
    #     sentence_ids = json['ids']
    #     if sentence_ids is None:
    #         return 'No sentence ids specified.'
    #     else: 
    #         return get_sentences_with_combinatory_ids(sentence_ids)
    # else:
    sentence_ids = request.args.get('ids')
    if sentence_ids is None:
        return 'No sentence ids specified.'
    else: 
        return get_sentences_with_combinatory_ids(request.args.get('ids').split(','))

def download_file(file_path, filename, mimetype):
    return_data = io.BytesIO()
    with open(file_path, 'rb') as fo:
        return_data.write(fo.read())
    # (after writing, cursor will be at last byte, so move it to start)
    return_data.seek(0)
    w = FileWrapper(return_data)
    os.remove(file_path)
    filename = urllib.parse.quote(filename)
    return Response(w, mimetype=mimetype, headers = {'Content-disposition': 'attachment; filename={}'.format(filename)})

def download_static_file(request_url, filename, mimetype):
    response = requests.get(request_url)
    file_path = Path(RESOURCES_PATH, "static", filename)
    file = open(file_path, "wb")
    file.write(response.content)
    file.close()
    return download_file(file_path, filename, mimetype)

@app.route('/download_sentence_image')
def download_sentence_image():
    sentence_id = request.args.get('id')
    if not sentence_id:
        return 'No sentence id specified.'
    elif not sentence_id.isdigit():
        return 'Invalid sentence id format.'
    else: 
        sentence_id = int(sentence_id)
        has_category = request.args.get('category') is not None and request.args.get('category') != ''
        category = DEFAULT_CATEGORY if not has_category else request.args.get('category')
        sentence = get_sentence_by_id(sentence_id)
        if sentence is None:
            return 'File not found.'
        else:
            return download_static_file(
                request_url=sentence["image_url"],
                filename=os.path.basename(sentence["image_url"]),
                mimetype='image/jpeg'
            )


@app.route('/download_sentence_audio')
def download_sentence_audio():
    sentence_id = request.args.get('id')
    if not sentence_id:
        return 'No sentence id specified.'
    elif not sentence_id.isdigit():
        return 'Invalid sentence id format.'
    else:
        sentence_id = int(sentence_id)
        sentence = get_sentence_by_id(sentence_id)
        if sentence is None:
            return 'File not found.'
        else:
            return download_static_file(
                request_url=sentence["sound_url"],
                filename=os.path.basename(sentence["sound_url"]),
                mimetype='audio/mpeg'
            )

@app.route('/download_media')
def download_media():
    path = request.args.get('path')
    if path is None:
        return 'No path specified.'
    else:
        has_file_extension = len(path.rsplit('.', 1)) > 1
        if not has_file_extension:
            return 'File type not identified.'
        filename = path.rsplit('/', 1)[1]
        file_extension = path.rsplit('.', 1)[1]
        mimetype = EXTENSION_MIMETYPE_MAP[file_extension]
        return download_static_file(
            request_url=MEDIA_FILE_HOST + '/' + path,
            filename=filename,
            mimetype=mimetype
        )

@app.route('/download_sentence')
def download_sentence_apkg():
    sentence_id = request.args.get('id')
    if not sentence_id:
        return 'No sentence id specified.'
    elif not sentence_id.isdigit():
        return 'Invalid sentence id format.'
    else:
        sentence_id = int(sentence_id)
        has_model_type = request.args.get('model_type') is not None and request.args.get('model_type') != ''
        model_type = DEFAULT_ANKI_MODEL if not has_model_type else request.args.get('model_type')
        has_vocabulary = request.args.get('vocabulary_position') is not None and request.args.get('vocabulary_position') != ''
        vocabulary_position = None if not has_vocabulary else int(request.args.get('vocabulary_position'))
        character_position = None if not has_vocabulary else int(request.args.get('character_position'))
        sentence = get_sentence_by_id(sentence_id)
        if sentence is None:
            return 'File not found.'
        else:
            deck_name = generate_deck(sentence, character_position, model_type)
            file_path = Path(RESOURCES_PATH, 'decks', deck_name)
            return download_file(
                file_path=file_path,
                filename=deck_name,
                mimetype='application/apkg'
            ) 

if __name__ == "__main__":
    app.run(debug=False)