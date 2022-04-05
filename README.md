# Immersion Kit API

Provides full-text search for Japanese and English text in Anki decks.

## Stack
- Python 3.8
- Flask 2.0.1


## Prerequisities

### Enchant

#### Mac (Intel)

```bash
brew install enchant
```

#### Mac (Apple Silicon)
```bash
brew install enchant
# Locate libenchant.dylib location
brew ls enchant
> ...
> /opt/homebrew/Cellar/enchant/2.3.2/lib/libenchant-2.2.dylib
> ...
# Set pyenchant library path to libenchant path
echo 'export PYENCHANT_LIBRARY_PATH=/opt/homebrew/Cellar/enchant/2.3.2/lib/libenchant-2.2.dylib' >> ~/.zshenv
```

#### Ubuntu

```
apt-get install enchant
```


## Getting started
```bash
virtualenv --python=python3.8 venv     
source venv/bin/activate
pip install -r requirements.txt
python -m spacy download en
python flask_app.py
```

## Add a Deck

1. Export the deck to JSON with [CrowdAnki](https://ankiweb.net/shared/info/1788670778) to the folder */resources/anime/*
2. Add a *deck-structure.json* to define the data of each column.

    ```json
    {
      "id-column": 0,
      "text-column": 1,
      "translation-column": 2,
      "text-with-furigana-column": 3,
      "image-column": 4,
      "sound-column": 5
    }
    ```
    
3. Add a *tags.json* file to the folder:

   ```json
    [
      "Action", 
      "Slice Of Life"
    ]
    ```
4. Parse the deck:

    ```python
    from deckparser import parse_deck 
    parse_deck('foldernameofyourdeck')
    ```
    This extracts media data from `deck.json`, adds tokenized word lists and exports to `data.json`.
