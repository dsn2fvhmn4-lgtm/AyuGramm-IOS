# ==AyuPlugin==
# @id lyrics-cleaner
# @name Lyrics cleaner
# @author murk-sus & dsn2fvhmn4-lgtm
# @version 1.0
# @description Python plugin: removes "[Куплет 1]", "Припев:", "(x2)" and similar labels from song lyrics. Switches in Settings → AyuGram → Lyrics sources.
# @tags lyrics, python
# @inject true
# ==/AyuPlugin==

ayu.settings.declare([
    {'key': 'labels', 'type': 'toggle', 'title': 'Убирать «[Куплет]», «Припев:»', 'subtitle': 'Метки частей песни', 'default': True},
    {'key': 'repeats', 'type': 'toggle', 'title': 'Убирать «(x2)», «×3»', 'subtitle': 'Пометки повторов', 'default': True},
    {'key': 'credits', 'type': 'toggle', 'title': 'Убирать «Слова:», «Музыка:»', 'subtitle': 'Строки с авторами', 'default': False},
])

UPPER = 'АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ'
LOWER = 'абвгдеёжзийклмнопрстуфхцчшщъыьэюя'
CASE = {}
for i in range(len(UPPER)):
    CASE[UPPER[i]] = LOWER[i]

def low(text):
    # str.lower() in this interpreter only folds Latin letters.
    return ''.join([CASE.get(ch, ch) for ch in text.lower()])

LABELS = ['куплет', 'припев', 'бридж', 'проигрыш', 'интро', 'аутро', 'verse', 'chorus', 'bridge', 'intro', 'outro', 'hook', 'pre-chorus', 'refrain']
CREDITS = ['слова:', 'музыка:', 'текст:', 'lyrics:', 'music:', 'written by']
REPEATS = ['(x2)', '(x3)', '(x4)', '(х2)', '(х3)', '(х4)', 'x2', 'x3', '×2', '×3', '×4']

def setting(key):
    return ayu.settings.get(key) == '1'

def is_label(line):
    text = low(line.strip())
    if not text:
        return False
    if text[0] == '[' and text[-1] == ']':
        return True
    body = text.rstrip(':').strip()
    for word in LABELS:
        if body == word or (body.startswith(word) and len(body) <= len(word) + 4):
            return True
    return False

def is_credit(line):
    text = low(line.strip())
    for word in CREDITS:
        if text.startswith(word):
            return True
    return False

def strip_repeats(line):
    out = line.rstrip()
    for mark in REPEATS:
        if low(out).endswith(mark):
            out = out[:len(out) - len(mark)].rstrip()
    return out

@ayu.hooks.before(ayu.hooks.points.lyrics_text)
def clean(text, ctx):
    labels = setting('labels')
    repeats = setting('repeats')
    credits = setting('credits')
    result = []
    for line in text.split('\n'):
        value = line
        if labels and is_label(value):
            value = ''
        elif credits and is_credit(value):
            value = ''
        elif repeats:
            value = strip_repeats(value)
        result.append(value)
    # One output line per input line: the app keeps the timings and drops emptied lines.
    return '\n'.join(result)
