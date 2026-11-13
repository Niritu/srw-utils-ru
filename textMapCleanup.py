import re
from getConfig import CONFIG
import json
import os


def replace_text(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()

        content = re.sub(r"\\\\n", "<br />", content)
        content = re.sub(r"<color=#f29e38ff>(.*?)</color>", r"{{Color|h|\1}}", content)
        content = re.sub(r"<color=#8790abff>(.*?)</color>", r"\1", content)
        content = re.sub(r"<unbreak>(.*?)</unbreak>", r"\1", content)
        content = re.sub(r"\{LAYOUT_MOBILE#Tap\}\{LAYOUT_CONTROLLER#Press\}\{LAYOUT_KEYBOARD#Click\}", r"(Tap/Press/Click)", content)
        content = re.sub(r"\{NICKNAME\}", r"(Trailblazer)", content)
        content = re.sub(r'\{RUBY_B#(.*?)\}(.*?)\{RUBY_E#\}', r'{{Rubi|\2|\1}}', content)
        content = re.sub(r'\{F#(.*?)\}\{M#(.*?)\}', r'{{MC|\2|\1}}', content)

        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(content)

        print(f"Replacements completed and saved to {file_path}")
    except FileNotFoundError:
        print(f"File not found: {file_path}")
    except Exception as e:
        print(f"An error occurred: {str(e)}")


def load_json_parts(base_path_no_ext):
    """
    Loads TextMap{lang}.json if it exists as a single file.
    If not, looks for TextMap{lang}_0.json, TextMap{lang}_1.json, ... and merges them.
    Returns a merged dict.
    """
    single_path = f'{base_path_no_ext}.json'
    if os.path.exists(single_path):
        with open(single_path, 'r', encoding='utf-8') as file:
            return json.load(file)

    merged = {}
    idx = 0
    found_any = False
    while True:
        part_path = f'{base_path_no_ext}_{idx}.json'
        if not os.path.exists(part_path):
            break
        found_any = True
        with open(part_path, 'r', encoding='utf-8') as file:
            part = json.load(file)
        merged.update(part)
        idx += 1

    if not found_any:
        raise FileNotFoundError(f'Neither {single_path} nor split parts found (e.g. {base_path_no_ext}_0.json)')

    return merged


def merge_jsons(file1_base, file2_base, output_file):
    content1 = load_json_parts(file1_base)
    content2 = load_json_parts(file2_base)

    merged_content = content1
    merged_content.update(content2)

    with open(output_file, 'w', encoding='utf-8') as file:
        json.dump(merged_content, file, ensure_ascii=False, indent=2)


repl_langs = ["CHS", "CHT", "ZHS", "ZHT", "DE", "EN", "ES", "FR", "ID", "JA", "JP", "KO", "KR", "PT", "RU", "TH", "VI", "TR", "IT"]
merge_langs = {
    "CHS": ["MainCHS", "CHS"],
    "CHT": ["MainCHT", "CHT"],
    "DE": ["MainDE", "DE"],
    "EN": ["MainEN", "EN"],
    "ES": ["MainES", "ES"],
    "FR": ["MainFR", "FR"],
    "ID": ["MainID", "ID"],
    "JP": ["MainJP", "JP"],
    "KR": ["MainKR", "KR"],
    "PT": ["MainPT", "PT"],
    "RU": ["MainRU", "RU"],
    "TH": ["MainTH", "TH"],
    "VI": ["MainVI", "VI"],
}

for lang, files in merge_langs.items():
    merge_jsons(
        f'{CONFIG.DATA_PATH}/TextMap/TextMap{files[0]}',
        f'{CONFIG.DATA_PATH}/TextMap/TextMap{files[1]}',
        f'{CONFIG.DATA_PATH}/TextMap/TextMap{lang}.json'
    )

for n in range(0, len(repl_langs)):
    replace_text(f'{CONFIG.DATA_PATH}/TextMap/TextMap' + repl_langs[n] + ".json")
