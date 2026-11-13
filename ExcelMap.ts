import * as fs from 'fs';
import * as path from 'path';
import * as JSONbig from 'json-bigint';
import { formatText, FormatContext } from './TextFormat';

const configPath = path.join(__dirname, 'scriptconfig.json');
const scriptConfig = JSONbig.parse(fs.readFileSync(configPath, 'utf8'));

const CONFIG = {
    EXCELS: scriptConfig.DataPath + "/ExcelOutput_Fix",
    // Сырые (неочищенные) текстмапы кладёт textMapCleanup.py. Если папки нет - берём обычные.
    TEXTMAP_RAW: scriptConfig.DataPath + "/TextMap/Raw",
    TEXTMAP: scriptConfig.DataPath + "/TextMap",
    OUTPUT: scriptConfig.DataPath + "/MappedExcelOutput_RU",
    MAPPED: scriptConfig.DataPath + "/Mapped",
    // Коды языков = суффиксы файлов TextMap{КОД}.json. В выводе ключ будет "TextMap{КОД}".
    LANGUAGES: ["RU", "EN", "CHS", "CHT", "JP", "KR", "ES", "FR", "TH", "VI", "DE", "ID", "PT"]
}

const EXCELS = new Map<string, any>();
// "TextMapRU" -> (hash -> уже отформатированный текст). Только те хэши, что реально встречаются в экселях.
const LANG_TEXT = new Map<string, Map<string, string>>();
const MAPPED_EXCELS: { [key: string]: { [key: string]: any } } = {
    ITEM: {}
}

function collectHashes(node: any, out: Set<string>): void {
    if (Array.isArray(node)) {
        node.forEach(n => collectHashes(n, out));
    } else if (node && typeof node == "object") {
        Object.keys(node).forEach(key => {
            const value = node[key];
            if (key == "Hash") out.add(String(value));
            else if (value && typeof value == "object") collectHashes(value, out);
        });
    }
}

function loadLanguage(code: string, needed: Set<string>): void {
    const dir = fs.existsSync(CONFIG.TEXTMAP_RAW) ? CONFIG.TEXTMAP_RAW : CONFIG.TEXTMAP;
    const file = path.join(dir, `TextMap${code}.json`);
    if (!fs.existsSync(file)) {
        console.warn(`[${code}] ${file} not found, language skipped.`);
        return;
    }

    // Значения в текстмапах - строки, ключи - строки, поэтому обычный JSON.parse (быстрее и легче json-bigint).
    let raw: { [hash: string]: string } | null = JSON.parse(fs.readFileSync(file, 'utf8'));
    const ctx: FormatContext = {
        lang: code,
        lookup: (hash: string) => raw ? raw[hash] : undefined,
        textJoinConfig: EXCELS.get("TextJoinConfig"),
        textJoinItem: EXCELS.get("TextJoinItem")
    };

    const result = new Map<string, string>();
    needed.forEach(hash => {
        const text = raw![hash];
        if (text) result.set(hash, formatText(text, ctx));
    });
    LANG_TEXT.set(`TextMap${code}`, result);
    raw = null; // отпускаем большой словарь до загрузки следующего языка
    console.log(`[${code}] mapped ${result.size} texts`);
}

async function main(): Promise<void> {
    const excels = fs.readdirSync(CONFIG.EXCELS);
    excels.forEach(fileName => {
        console.log(fileName);
        let data = fs.readFileSync(path.join(CONFIG.EXCELS, fileName), 'utf8');
        EXCELS.set(path.basename(fileName, ".json"), JSONbig.parse(data));
    });

    const needed = new Set<string>();
    EXCELS.forEach(excel => collectHashes(excel, needed));
    console.log(`Unique hashes: ${needed.size}`);

    CONFIG.LANGUAGES.forEach(code => loadLanguage(code, needed));

    if (!fs.existsSync(CONFIG.OUTPUT)) {
        fs.mkdirSync(CONFIG.OUTPUT);
    }
    if (!fs.existsSync(CONFIG.MAPPED)) {
        fs.mkdirSync(CONFIG.MAPPED);
    }

    itemToId();

    EXCELS.forEach((excel, name) => {
        let output = mapObject(excel, name);
        fs.writeFileSync(path.join(CONFIG.OUTPUT, name + ".json"), JSONbig.stringify(output, null, 2));
        console.log(`Saved "${path.join(CONFIG.OUTPUT, name + ".json")}"`);
    });

    return;
}

function mapObject(item: any, excel: string) {
    if (Array.isArray(item)) return mapArray(item, excel);

    let result: { [key: string]: any } = {};

    Object.entries(item).map(([key, value]) => {
        if (key == "Hash") {
            getText(String(value), result);
        } else if (key == "ItemID") {
            result[key] = value;
            let item = MAPPED_EXCELS.ITEM[String(value)];
            if (item) result["ItemName"] = item;
        } else if (Array.isArray(value)) {
            result[key] = mapArray(value, excel);
        } else if (typeof value == "object") {
            result[key] = mapObject(value, excel);
        } else {
            result[key] = value;
        }
    });

    return result;
}

function mapArray(items: any[], excel: string): any[] {
    return items.map((item) => {
        if (Array.isArray(item)) return mapArray(item, excel);
        else if (typeof item == "object") return mapObject(item, excel);
        else return item;
    });
}

function getText(hash: string, result: { [key: string]: any }): void {
    result["Hash"] = hash;
    LANG_TEXT.forEach((texts, key) => {
        const value = texts.get(hash);
        if (value) result[key] = value;
    });
}

function itemToId() {
    if (!fs.existsSync(path.join(CONFIG.EXCELS, "ItemConfig.json"))) {
        console.error(`${path.join(CONFIG.EXCELS, "ItemConfig.json")} does not exist.`);
        return process.exit();
    }

    let data = JSONbig.parse(fs.readFileSync(path.join(CONFIG.EXCELS, "ItemConfig.json"), 'utf8'));
    Object.entries(data).map(([key, value]: [string, any]) => {
        let result: { [key: string]: any } = {};
        if (value.ItemName) {
            getText(String(value.ItemName.Hash), result)
        };
        MAPPED_EXCELS.ITEM[key] = result;
    });

    fs.writeFileSync(path.join(CONFIG.MAPPED, "ItemConfig.json"), JSONbig.stringify(MAPPED_EXCELS.ITEM, null, 2));
}

main();
