import json
import argparse
import re
import os

from utils.files import write_file
from utils.misc import autoround, copy_icon, parse_extraeffect
from utils.pageinfo import pageinfo
import utils.ol as ol
from getConfig import CONFIG

DAMAGE_TYPE_TRANSLATION = {
    'Physical': 'Физический',
    'Fire': 'Огненный',
    'Ice': 'Ледяной',
    'Wind': 'Ветряной',
    'Lightning': 'Электрический',
    'Thunder': 'Электрический',
    'Imaginary': 'Мнимый',
    'Quantum': 'Квантовый'
}

parser = argparse.ArgumentParser()
parser.add_argument('--id', type=int)
parser.add_argument('--ver', type=float)
parser.add_argument('--files', type=bool)
parser.add_argument('--ids', nargs='+')
parser.add_argument('--new', type=bool)
args = parser.parse_args()

mons_id = str(args.id) if args.id else None
id_list: list = args.ids or []
ver = str(args.ver)
files = args.files

ol.load_data()


with open(f'{CONFIG.EXCEL_PATH}/MonsterConfig.json', 'r', encoding='utf-8') as file:
    monsterconfig = json.load(file)
    
with open(f'{CONFIG.EXCEL_PATH_OLD}/MonsterConfig.json', 'r', encoding='utf-8') as file:
    monsterconfig_old = json.load(file)
    
with open(f'{CONFIG.EXCEL_PATH}/MonsterTemplateConfig.json', 'r', encoding='utf-8') as file:
    monstertemplateconfig = json.load(file)
    
with open(f'{CONFIG.EXCEL_PATH}/MonsterSkillConfig.json', 'r', encoding='utf-8') as file:
    monsterskillconfig = json.load(file)

with open(f'{CONFIG.EXCEL_PATH}/MonsterCamp.json', 'r', encoding='utf-8') as file:
    monstercamp = json.load(file)


def parseMonster(id, ver):        
    name = monsterconfig[id]['MonsterName']['TextMapRU']
    print(f'=========={name}==========')
    
    filename = name.replace(' (Иллюзия конца)', '').replace(' (исправная)', '').replace(' (исправный)', '').replace(' (неисправная)', '').replace(' (неисправный)', '').replace(' (синтетический)', '')
    template_id = str(monsterconfig[id]['MonsterTemplateID'])
    intro = monsterconfig[id]['MonsterIntroduction']['TextMapRU']
    skill_list = monsterconfig[id]['SkillList']
    
    #tier
    if monstertemplateconfig[template_id]['Rank'] == 'BigBoss':
        tier = 'Эхо войны'
    elif monstertemplateconfig[template_id]['Rank'] == 'LittleBoss':
        tier = 'Босс'
    elif monstertemplateconfig[template_id]['Rank'] == 'Elite':
        tier = 'Элитный'
    else:
        tier = 'Обычный'
        
    if monstertemplateconfig[template_id]['Rank'] == 'BigBoss':
        tier2 = 'противник из [[Эхо войны|«Эха войны»]]'
    elif monstertemplateconfig[template_id]['Rank'] == 'LittleBoss':
        tier2 = '[[босс]]'
    elif monstertemplateconfig[template_id]['Rank'] == 'Elite':
        tier2 = 'элитный противник'
    else:
        tier2 = 'обычный противник'
        
    
    #files
    if files:
        largeimage = monstertemplateconfig[template_id]['ImagePath']
        copy_icon(largeimage, f'Враг {name}.png', f'Enemy Images')
        
        icon = monstertemplateconfig[template_id]['RoundIconPath']
        copy_icon(icon, f'Враг {name} Иконка.png', f'Enemy Icons')
    
    
    #stat modifiers
    atkratio = autoround(monsterconfig[id]['AttackModifyRatio']['Value'])
    defratio = autoround(monsterconfig[id]['DefenceModifyRatio']['Value'])
    hpratio = autoround(monsterconfig[id]['HPModifyRatio']['Value'])
    spdratio = autoround(monsterconfig[id]['SpeedModifyRatio']['Value'])
    stanceratio = autoround(monsterconfig[id]['StanceModifyRatio']['Value'])
    try:
        speedadd = autoround(monsterconfig[id]['SpeedModifyValue']['Value'])
    except KeyError:
        speedadd = 0
    try:
        stanceadd = autoround(monsterconfig[id]['StanceModifyValue']['Value'])
    except KeyError:
        stanceadd = 0
        
    #stats
    atk = autoround(monstertemplateconfig[template_id]['AttackBase']['Value']) * atkratio
    if atk != 18:
        atk_text = f'|сила_атаки    = {atk}\n'
    else:
        atk_text = ''
    try:
        defence = autoround(monstertemplateconfig[template_id]['DefenceBase']['Value']) * defratio
    except KeyError:
        defence = 0 * defratio
    if defence != 210:
        def_text = f'|защита        = {defence}\n'
    else:
        def_text = ''
    hp = autoround(monstertemplateconfig[template_id]['HPBase']['Value']) * hpratio
    hp_text = f'|hp            = {hp}\n'
    try:
        spd = autoround(monstertemplateconfig[template_id]['SpeedBase']['Value']) * spdratio + speedadd
    except KeyError:
        spd = 0
    spd_text = f'|скорость      = {spd}\n'
    try:
        stance = int((autoround(monstertemplateconfig[template_id]['StanceBase']['Value']) * stanceratio + stanceadd) / 3)
    except KeyError:
        stance = 0
    try:
        eres = autoround(monstertemplateconfig[template_id]['StatusResistanceBase']['Value'])
    except KeyError:
        eres = 0.1
    eres_text = f'|сопр_эфф      = {eres}\n'
    
    #weakness
    weak_list = monsterconfig[id]['StanceWeakList']
    weak_list = list(map(lambda x: x.replace('Thunder', 'Lightning'), weak_list))
    weak_text = ''
    for weak in weak_list:
        translated_weak = DAMAGE_TYPE_TRANSLATION.get(weak, weak)
        if weak == weak_list[-1]:
            weak_end = ''
        else:
            weak_end = ';'
        weak_text = weak_text + f'{translated_weak}{weak_end}'
        
    #res
    damage_res_text = ''
    for item in monsterconfig[id]['DamageTypeResistance']:
        dmgtype = item['DamageType'].replace('Physical', '|физ_сопр      = ').replace('Fire', '|огн_сопр      = ').replace('Ice', '|лед_сопр      = ').replace('Wind', '|ветр_сопр     = ').replace('Thunder', '|элек_сопр     = ').replace('Imaginary', '|мним_сопр     = ').replace('Quantum', '|квант_сопр    = ')
        dmgres = autoround(item['Value']['Value'])
        damage_res_text = damage_res_text + f'{dmgtype}{dmgres}\n'
    
    debuff_res_text = ''
    for item in monsterconfig[id]['DebuffResist']:
        debufftype = item['Key'].replace('STAT_CTRL_Frozen', '|замороз_сопр  = ').replace('STAT_Entangle', '|связыв_сопр   = ').replace('STAT_Confine', '|заключ_сопр   = ').replace('STAT_DOT_Burn', '|горение_сопр  = ').replace('STAT_DOT_Electric', '|шок_сопр      = ').replace('STAT_DOT_Poison', '|выветр_сопр   = ').replace('STAT_CTRL', '|контроль_сопр = ')
        debuffres = autoround(item['Value']['Value'])
        debuff_res_text = debuff_res_text + f'{debufftype}{debuffres}\n'
    
    #skills
    skill_text = ''
    type_list = []
    phase_show = False
    number = 1
    for n in range(len(skill_list)):        
        skill = skill_list[n]
        try:
            skill_name = monsterskillconfig[str(skill)]['SkillName']['TextMapRU']
        except KeyError:
            skill_name = ''
        
        try:
            skill_desc = monsterskillconfig[str(skill)]['SkillDesc']['TextMapRU']
        except KeyError:
            skill_desc = ''
            
        try:
            skill_type = monsterskillconfig[str(skill)]['SkillTag']['TextMapRU']
        except KeyError:
            skill_type = ''

        if monsterskillconfig[str(skill)].get('PhaseList'):

            # damage type list
            # NOTE: EN-версия скрипта определяет тип урона поиском "Fire DMG" и т.п.
            # прямо в тексте описания навыка. Для русского текста это не сработает
            # (там не будет фразы "Fire DMG"), поэтому здесь оставлен рабочий способ
            # через поле DamageType в конфиге навыка.
            dmgtype = monsterskillconfig[str(skill)].get('DamageType')
            if dmgtype and dmgtype not in type_list:
                type_list.append(dmgtype)

            # energy
            try:
                energy_value = autoround(monsterskillconfig[str(skill)]['SPHitBase']['Value'])
                skill_energy = f'|Энергия{number}   = {energy_value}\n'
            except KeyError:
                skill_energy = ''

            # danger
            try:
                if monsterskillconfig[str(skill)]['IsThreat'] is True:
                    skill_danger = f'|Опасность{number} = 1\n'
                else:
                    skill_danger = ''
            except KeyError:
                skill_danger = ''

            # phases
            phase_text = f'|Фаза{number}      = '
            phase_list = monsterskillconfig[str(skill)]['PhaseList']
            for phase in phase_list:
                phase_end = '' if phase == phase_list[-1] else ','
                if phase != 1:
                    phase_show = True
                phase_text += f'{phase}{phase_end}'

            # parse extra effect
            extraeffect_idlist = monsterskillconfig[str(skill)].get('ExtraEffectIDList')
            if extraeffect_idlist:
                skill_desc = parse_extraeffect(skill_desc, extraeffect_idlist)

            skill_text += (
                f'\n|Название{number}  = {skill_name}\n'
                f'|Тип{number}       = {skill_type}\n'
                f'|Описание{number}  = {skill_desc}\n'
                f'{skill_energy}{skill_danger}{phase_text}\n'
            )

            number = number + 1
        
    #remove phase if no phase
    if phase_show == False:
        skill_text = re.sub(r'\|Фаза.*\n', '', skill_text)
        
    #dmg types
    type_text = ''
    if type_list:
        for dmgtype in type_list:
            translated_type = DAMAGE_TYPE_TRANSLATION.get(dmgtype, dmgtype)
            if dmgtype == type_list[-1]:
                type_end = ''
            else:
                type_end = ';'
            type_text = type_text + f'{translated_type}{type_end}'
            
    #faction
    try:
        camp_id = str(monstertemplateconfig[template_id]['MonsterCampID'])
        camp_name = monstercamp[camp_id]['Name']['TextMapRU']
        if camp_name in ['Ярило-VI', 
                        'Лофу Сяньчжоу', 
                        'Виртуальная вселенная', 
                        'Охотники за Стелларонами', 
                        'Легион Антиматерии',
                        'Корпорация межзвёздного мира',
                        'Рой']:
            camp_link = f'{camp_name} (Фракция противника)|{camp_name}'
        else:
            camp_link = camp_name
    except KeyError:
        camp_name = ''
        camp_link = ''
    
    OLtext = ol.gen_ol(name, lang='RU')
    
    page_content = f"{pageinfo(name)}\n{{{{Враг Инфобокс\n|Изображение = Враг {filename}.png\n|Тип         = {tier}\n|Тип_урона   = {type_text}\n|Уязвимость  = {weak_text}\n|Стойкость   = {stance}\n|Фракция     = {camp_name}\n|Локация     = \n}}}}\n'''{name}''' — {tier2}, член фракции [[{camp_link}]].\n\n==Описание==\n{{{{Описание|{intro}}}}}\n\n==Характеристики==\n{{{{Характеристики врага\n{damage_res_text}\n{debuff_res_text}\n{atk_text}{def_text}{hp_text}{spd_text}{eres_text}}}}}\n\n==Навыки==\n{{{{Навыки врага{skill_text}}}}}\n\n==На других языках==\n{OLtext}\n==История изменений==\n{{{{История изменений|{ver}}}}}\n\n==Навигация==\n{{{{Враг Навбокс|{tier}}}}}\n\n[[en:]]"

    return([page_content, name])


def output_mons(id):
    output = parseMonster(id, ver)

    if not os.path.exists(f'{CONFIG.OUTPUT_PATH}/Monsters'):
        os.makedirs(f'{CONFIG.OUTPUT_PATH}/Monsters')

    file_name = output[1].replace(' ', '_').replace(':', '').replace('"', '')
    file_write_path = f'{CONFIG.OUTPUT_PATH}/Monsters/{file_name}.wikitext'

    write_file(file_write_path, output[0], overwrite = False)


if mons_id:
    output_mons(mons_id)


if args.new:
    old_names = [value.get('MonsterName').get('TextMapRU') for value in monsterconfig_old.values()]    
    for id, value in monsterconfig.items():
        if value.get('MonsterName').get('TextMapRU') not in old_names:
            id_list.append(id)
        """if id not in list(monsterconfig_old.keys()):
            id_list.append(id)"""


if id_list:
    for id in id_list:
        output_mons(id)
