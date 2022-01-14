import requests

def get_jpod_audio(url):
    try:
        requests.packages.urllib3.disable_warnings(requests.packages.urllib3.exceptions.InsecureRequestWarning)
        r = requests.get(url, verify=False, timeout=5)
        return r
    except:
        return None

def validate_jpod_audio_url(url):
    jpod_audio = get_jpod_audio(url)
    if jpod_audio:
        return len(jpod_audio.content) != 52288 # invalid audio
    else:
        return False

def get_jpod_audio_url(kanji, kana):
    url = 'https://assets.languagepod101.com/dictionary/japanese/audiomp3.php?kanji={}&kana={}'.format(kanji, kana)
    return url if (validate_jpod_audio_url(url)) else ''