# Immersion Kit API

## Stack
- Python 3.8
- Flask 2.0.1


## Prerequisities

#### Enchant

```bash
brew install enchant
```


## Getting started
```bash
virtualenv --python=python3.8 venv     
source venv/bin/activate
pip install -r requirements.txt
python -m spacy download en
python flask_app.py
```

## Setting up Database Credentials
```bash
touch .env
echo "SUPABASE_CONNECTION_STRING=" > .env
```

Note: You can use any Relational DB such as PostgreSQL or MySQL that is supported by SQLAlchemy.
