import io
import os
import requests
from flask import Flask, request, send_file
from flask_cors import CORS
from pathlib import Path
from config import DEFAULT_CATEGORY, RESOURCES_PATH, MEDIA_FILE_HOST, EXTENSION_MIMETYPE_MAP
from search import get_deck_by_id, look_up, get_sentence_by_id, get_sentence_with_context, get_sentences_with_combinatory_ids

app = Flask(__name__)
CORS(app)

@app.route('/')
def hello_world():
    return 'Hello from Flask!'

@app.route('/look_up_dictionary')
def look_up_dictionary():
    keyword = request.args.get('keyword')
    if keyword is None:
        return 'No keyword specified.'
    else:
        has_tags = request.args.get('tags') is not None and request.args.get('tags') != ''
        has_jlpt = request.args.get('jlpt') is not None and request.args.get('jlpt') != ''
        has_wk = request.args.get('wk') is not None and request.args.get('wk') != ''
        has_sorting = request.args.get('sort') is not None and request.args.get('sort') != ''
        has_category = request.args.get('category') is not None and request.args.get('category') != ''
        user_levels = {
            'JLPT': None if not has_jlpt else int(request.args.get('jlpt')),
            'WK': None if not has_wk else int(request.args.get('wk'))
        }
        return look_up(
            text = request.args.get('keyword')[:50], 
            sorting = None if not has_sorting else request.args.get('sort'),
            category = DEFAULT_CATEGORY if not has_category else request.args.get('category'),
            tags = [] if not has_tags else request.args.get('split').split(','),
            user_levels=user_levels)

@app.route('/sentence_with_context')
def sentence_with_context():
    sentence_id = request.args.get('id')
    has_category = request.args.get('category') is not None and request.args.get('category') != ''
    if sentence_id is None:
        return 'No sentence id specified.'
    else: 
        return get_sentence_with_context(request.args.get('id'), category=DEFAULT_CATEGORY if not has_category else request.args.get('category'))

@app.route('/deck')
def deck():
    deck_id = request.args.get('id')
    has_category = request.args.get('category') is not None and request.args.get('category') != ''
    if deck_id is None:
        return 'No idspecified.'
    else: 
        return get_deck_by_id(request.args.get('id'), category=DEFAULT_CATEGORY if not has_category else request.args.get('category'))

@app.route('/sentences')
def sentences():
    sentences_ids = request.args.get('ids')
    if sentences_ids is None:
        return 'No sentence ids specified.'
    else: 
        return get_sentences_with_combinatory_ids(request.args.get('ids').split(','))

def download_static_file(request_url, filename, mimetype):
    response = requests.get(request_url)
    file_path = Path(RESOURCES_PATH, "static", filename)
    file = open(file_path, "wb")
    file.write(response.content)
    file.close()

    return_data = io.BytesIO()
    with open(file_path, 'rb') as fo:
        return_data.write(fo.read())
    # (after writing, cursor will be at last byte, so move it to start)
    return_data.seek(0)

    os.remove(file_path)

    return send_file(return_data, mimetype=mimetype,
                    attachment_filename=filename,
                    as_attachment=True)

@app.route('/download_sentence_image')
def download_sentence_image():
    sentence_id = request.args.get('id')
    if sentence_id is None:
        return 'No sentence id specified.'
    else:
        has_category = request.args.get('category') is not None and request.args.get('category') != ''
        category = DEFAULT_CATEGORY if not has_category else request.args.get('category')
        sentence = get_sentence_by_id(sentence_id, category)
        if sentence is None:
            return 'File not found.'
        else:
            return download_static_file(
                request_url=sentence["image_url"],
                filename=sentence["image"],
                mimetype='image/jpeg'
            )


@app.route('/download_sentence_audio')
def download_sentence_audio():
    sentence_id = request.args.get('id')
    if sentence_id is None:
        return 'No sentence id specified.'
    else:
        has_category = request.args.get('category') is not None and request.args.get('category') != ''
        category = DEFAULT_CATEGORY if not has_category else request.args.get('category')
        sentence = get_sentence_by_id(sentence_id, category)
        if sentence is None:
            return 'File not found.'
        else:
            return download_static_file(
                request_url=sentence["sound_url"],
                filename=sentence["sound"],
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

if __name__ == "__main__":
    app.run(debug=False)