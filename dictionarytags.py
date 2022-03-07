import re

CURRICULUMS = {
   'JLPT': ["N" + str(n+1) for n in range(5)],
   'WK':["WK" + str(n+1) for n in range(60)]
}

def get_level(entry, curriculum):
    tags = entry[7].split(' ')
    for tag in tags:
        if tag in CURRICULUMS[curriculum]:
            return int(re.findall('\d+', tag)[0])
    return None