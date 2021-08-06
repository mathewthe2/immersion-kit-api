from flask import Flask, request
from flask_cors import CORS
from config import DEFAULT_CATEGORY
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

if __name__ == "__main__":
    app.run(debug=False)