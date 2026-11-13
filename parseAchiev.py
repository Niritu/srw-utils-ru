import json
import os
import re
import argparse

import utils.ol as ol
from utils.files import write_file
from utils.pageinfo import pageinfo
from getConfig import CONFIG

TEXTMAP_PATH = f'{CONFIG.DATA_PATH}/TextMap'

RARITY_TRANSLATION = {
    'Low': 'Низкая',
    'Mid': 'Средняя',
    'High': 'Высокая'
}

parser = argparse.ArgumentParser()
parser.add_argument('--ver', type = str)

args = parser.parse_args()
version = args.ver

with open(f'{CONFIG.EXCEL_PATH}/AchievementData.json', 'r', encoding='utf-8') as file:
    achievementjson = json.load(file)
    
with open(f'{CONFIG.EXCEL_PATH_OLD}/AchievementData.json', 'r', encoding='utf-8') as file:
    old_achievementjson = json.load(file)
    
with open(f'{CONFIG.EXCEL_PATH}/AchievementSeries.json', 'r', encoding='utf-8') as file:
    achievementseriesjson = json.load(file)

ol.load_data()

for item in achievementjson:
    title_map = achievementjson[item]['AchievementTitle']
    if 'TextMapRU' not in title_map:
        en_fallback = title_map.get('TextMapEN', '(нет и TextMapEN)')
        print(f'⚠ Нет RU-перевода: id={item}, EN title="{en_fallback}"')
        continue
    name = title_map['TextMapRU']
    
    if old_achievementjson.get(item) or name == '...':
        print(f'Skipped {name}.')
        continue
    
    OLtext = ol.gen_ol(name, lang='RU')
    desc = achievementjson[item]['AchievementDesc']['TextMapRU']
    rarity = RARITY_TRANSLATION.get(achievementjson[item]['Rarity'], achievementjson[item]['Rarity'])
    priority = str(achievementjson[item]['Priority'])
    
    try:
        hidedesc = achievementjson[item]['HideAchievementDesc']['TextMapRU']
    except KeyError:
        hidedesc = ''
    
    extradesc = ''
    
    if hidedesc != '':
        if '<br />※' in desc:
            extradesc = desc.split('<br />※')[1].strip()
        elif '<br />' in desc:
            extradesc = desc.split('<br />')[1].strip()
        desc = hidedesc
    
    params = [key["Value"] for key in achievementjson[item]['ParamList']]
    
    for n in range(0, len(params)):
        percent = params[n] * 100
        desc = desc.replace(f'#{n + 1}[i]%', str(percent) + '%')
        desc = desc.replace(f'#{n + 1}[i]', str(params[n]))
        desc = desc.replace(f'#{n + 1}', str(params[n]))
        
    for n in range(0, len(params)):
        percent = params[n] * 100
        extradesc = extradesc.replace(f'#{n + 1}[i]%', str(percent) + '%')
        extradesc = extradesc.replace(f'#{n + 1}[i]', str(params[n]))
        extradesc = extradesc.replace(f'#{n + 1}', str(params[n]))
    
    if hidedesc != '' and extradesc != '':
        lowerdesc = extradesc[0].lower() + extradesc[1:] + ''
    elif hidedesc != '' and extradesc == '':
        lowerdesc = desc[0].lower() + desc[1:] + ''
    else:
        lowerdesc = desc[0].lower() + desc[1:] + ''
    
    if lowerdesc.endswith('".'):
        lowerdesc = lowerdesc[:-2] + '."'
        
    try:
        if achievementjson[item]['ShowType'] == 'ShowAfterFinish':
            hidden = '1'
        else:
            hidden = ''
    except KeyError:
        hidden = ''
        
    seriesId = str(achievementjson[item]['SeriesID'])
    series = achievementseriesjson[seriesId]['SeriesTitle']['TextMapRU']
    
    clean_name = re.sub(r'[:*?"<>|]', ' ', name)
    
    file_write_path = f"{CONFIG.OUTPUT_PATH}/Achievements/{series}/{clean_name}.wikitext"
    directory_path = f'{CONFIG.OUTPUT_PATH}/Achievements/{series}'
    if not os.path.exists(directory_path):
        os.makedirs(directory_path)
    
    file_write = f"{pageinfo(name)}{{{{Достижение Инфобокс\n|Название    = {name}\n|Редкость    = {rarity}\n|Серия       = {series}\n|Описание    = {desc}\n|ДопОписание = {extradesc}\n|Скрыто      = {hidden}\n|Миссия      = \n|Тема        = \n}}}}\n'''{name}''' — [[достижения|достижение]] из серии «[[{series}]]».\n\nДля выполнения этого достижения, {lowerdesc}\n\n==На других языках==\n{OLtext}\n==История изменений==\n{{{{История изменений|{version}}}}}\n\n==Навигация==\n{{{{Достижения Навбокс}}}}\n\n[[en:]]\n"

    write_file(file_write_path, file_write)