from config import MEDIA_FILE_HOST

s = '/gamegengotextbook/jlptn5/Game%20Gengo%20Grammar%20N5/media/GamgeGengo_Grammar_N5_IMG_001.jpg'
s = 'https://immersion-kit.sfo3.digitaloceanspaces.com/media/gamegengotextbook/jlptn5/Game%20Gengo%20Grammar%20N5/media/GameGengo_Grammar_N5_AUDIO_001.mp3'
s = 'xxx'
# url = MEDIA_FILE_HOST + '/' + s
has_file_extension = len(s.rsplit('.', 1)) > 1
print(has_file_extension)