import json
import os

from getConfig import CONFIG

langs = ['CHS','CHT','DE','EN','ES','FR','ID','JP','KR','PT','RU','TH','VI']
data = {}


def print_progress_bar(iteration, total, length = 50):
    percent = f"{100 * (iteration / float(total)):.1f}"
    filled_length = int(length * iteration // total)
    bar = '█' * filled_length + '-' * (length - filled_length)
    print(f'\rLoading OL: |{bar}| {percent}%', end='\r')
    if iteration == total: 
        print()


def load_textmap_lang(lang):
    """Загружает TextMap для языка: либо единый TextMap{lang}.json,
    либо, если его нет, склеивает TextMap{lang}_0.json, TextMap{lang}_1.json и т.д."""
    single_path = f'{CONFIG.DATA_PATH}/TextMap/TextMap{lang}.json'
    if os.path.exists(single_path):
        with open(single_path, 'r', encoding='utf-8') as file:
            return json.load(file)

    merged = {}
    part = 0
    found_any = False
    while True:
        part_path = f'{CONFIG.DATA_PATH}/TextMap/TextMap{lang}_{part}.json'
        if not os.path.exists(part_path):
            break
        found_any = True
        with open(part_path, 'r', encoding='utf-8') as file:
            merged.update(json.load(file))
        part += 1

    if not found_any:
        raise FileNotFoundError(
            f'Не найден ни TextMap{lang}.json, ни TextMap{lang}_0.json в {CONFIG.DATA_PATH}/TextMap'
        )

    return merged


def load_data(progress_callback = None):
    global langs, data
    
    if data:
        return
    
    for index, lang in enumerate(langs):
        data[lang] = load_textmap_lang(lang)
        if progress_callback:
            progress_callback(index + 1, len(langs))
        print_progress_bar(index + 1, len(langs))


def gen_ol(text, lang='EN'):
    textdata = {}
    textId_list = []
        
    for item in data[lang]:
        if (data[lang][item]) == text:
            textId_list.append(item)
    try:
        textId = textId_list[0]
    except Exception as e:
        print(f"Error while generating OL for text: {text}. Error: {str(e)}")
        return

    for l in langs:
        textdata[l] = data[l].get(textId, '')
        
    output = f"{{{{На других языках\n|en   = {textdata['EN']}\n|zhs  = {textdata['CHS']}\n|zht  = {textdata['CHT']}\n|ja   = {textdata['JP']}\n|ko   = {textdata['KR']}\n|es   = {textdata['ES']}\n|fr   = {textdata['FR']}\n|ru   = {textdata['RU']}\n|th   = {textdata['TH']}\n|vi   = {textdata['VI']}\n|de   = {textdata['DE']}\n|id   = {textdata['ID']}\n|pt   = {textdata['PT']}\n}}}}\n"
    
    return output