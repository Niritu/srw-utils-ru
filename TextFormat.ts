// Порт TextMap.wikiFormatting() из hsr-wiki-utils-RU.
// Работает с "сырым" текстом конкретного языка и не зависит от глобальных переменных,
// поэтому один и тот же форматтер применяется ко всем языкам.
// Написан без replaceAll / флагов s и u в литералах, чтобы компилироваться при любом target в tsconfig.

export const COLOR_MAP: { [hex: string]: string } = {
    'f29e38': 'Выделенный',
    'dd7a00': 'Выделенный',
    'dbc291': 'Ключевой|nobold=1',
    '42a8b9': 'fthuser',
    '87e0ff': 'Ледяной',
    '77ede5': 'heliobus',
    'eb4d3d': 'Огненный',
    'ec505f': 'Огненный',
    'ff3a3e': 'Огненный',
    'f3da75': 'Мнимый',
    '6f7cda': 'hblue',
    'ad5e68': 'hred',
    'ff4f53': 'humanoid',
    '00f6ff': 'mechanical',
    'ab88fe': 'aberrant'
};

// Цвета, которые просто вырезаются (оставляем только текст).
// cdcdd8 - из hsr-репо, 8790ab - из старого textMapCleanup.py этого репо.
const STRIP_COLORS = ['cdcdd8', '8790ab'];

// Как заменять переносы строк. В старом textMapCleanup.py было '<br />'.
export const NEWLINE = '<br />';

// В hsr-репо '|' в тексте заменяется на &vert;, чтобы не ломать шаблоны вики.
export const ESCAPE_PIPES = true;

// Хэш строки "Первопроходец" (имя ГГ) - подставляется вместо {NICKNAME} на каждом языке.
const TRAILBLAZER_HASH = '6354779731002018877';

export interface FormatContext {
    lang: string;                                   // 'RU', 'EN', 'KR' ...
    lookup: (hash: string) => string | undefined;   // сырой текст этого же языка по хэшу
    textJoinConfig?: any;                           // ExcelOutput/TextJoinConfig (опционально)
    textJoinItem?: any;                             // ExcelOutput/TextJoinItem (опционально)
}

function vals(obj: any): any[] {
    if (!obj) return [];
    return Array.isArray(obj) ? obj : Object.keys(obj).map(k => obj[k]);
}

// \p{P} требует флага u, поэтому регэксп собирается через конструктор (не проверяется компилятором).
const GENDER_WORD_RE = new RegExp('(\\s|^)(\\S*\\{[FM]#.+?\\}[^\\p{P}\\s]*?)(\\p{P}*)(\\s|$)', 'giu');

export function formatText(text: string, ctx: FormatContext, depth: number = 0): string {
    let s = ESCAPE_PIPES ? text.split('|').join('&vert;') : text;

    const trailblazer = ctx.lookup(TRAILBLAZER_HASH) || 'Trailblazer';

    s = s
        .replace(/\{NICKNAME\}/gi, '(' + trailblazer + ')')
        .split('\\n').join(NEWLINE)
        // {F#..}{M#..} подряд -> шаблон MC
        .replace(/\{(F|M)#([^}]+?)\}\{(F|M)#([^}]+?)\}/gi,
            (_m: string, g1: string, t1: string, g2: string, t2: string) =>
                '⟨⟨MC|' + (g1.toLowerCase() === 'm' ? 'м' : 'ж') + '=' + t1 + '|' +
                (g2.toLowerCase() === 'm' ? 'м' : 'ж') + '=' + t2 + '⟩⟩')
        // слово с вставкой {F#..} / {M#..} внутри
        .replace(GENDER_WORD_RE, (_m: string, ws1: string, word: string, punct: string, ws2: string) => {
            const fem = word.replace(/\{F#(.+?)\}/gi, '$1').replace(/\{M#(.+?)\}/gi, '');
            const masc = word.replace(/\{M#(.+?)\}/gi, '$1').replace(/\{F#(.+?)\}/gi, '');
            return ws1 + '⟨⟨MC|ж=' + fem + '|м=' + masc + '⟩⟩' + punct + ws2;
        })
        .replace(/<color=#(\w{1,6})\w{2}?>([\s\S]*?)<\/color>/gi, (_m: string, color: string, inner: string) => {
            color = color.toLowerCase();
            if (COLOR_MAP[color]) return '⟨⟨Цвет|' + COLOR_MAP[color] + '|' + inner + '⟩⟩';
            if (STRIP_COLORS.indexOf(color) !== -1) return inner;
            return '⟨⟨Цвет|#' + color + '|' + inner + '⟩⟩';
        })
        .replace(/<size=([\-\+]?\d+)>([\s\S]*?)<\/size>/gi, '⟨⟨Размер|$1|$2⟩⟩')
        .replace(/<align="?(\w+)"?>([\s\S]*?)<\/align>/gi, '<div align="$1">$2</div>')
        .replace(/\{RUBY_B#([\s\S]+?)\}([\s\S]+?)\{RUBY_E#\}/gi,
            (_m: string, top: string, normal: string) => '⟨⟨Rubi|' + normal + '|' + top + '⟩⟩')
        .replace(/\{TEXTJOIN#(\d+)\}/gi, (m: string, id: string) => {
            const cfg = vals(ctx.textJoinConfig).find((tj: any) => String(tj.TextJoinID) === id);
            if (!cfg || depth >= 3) return m;
            const items = vals(ctx.textJoinItem);
            const parts = (cfg.TextJoinItemList || []).map((itemId: any) => {
                const item = items.find((tj: any) => String(tj.TextJoinItemID) === String(itemId));
                const h = item && item.TextJoinText ? String(item.TextJoinText.Hash) : undefined;
                const raw = h ? ctx.lookup(h) : undefined;
                return raw ? formatText(raw, ctx, depth + 1) : '';
            });
            return '(' + parts.join('/') + ')';
        })
        .replace(/\{LAYOUT_(\w+)#([^}]+?)\}(?:\{LAYOUT_(\w+)#([^}]+?)\})?(?:\{LAYOUT_(\w+)#([^}]+?)\})?/gi,
            (_m: string, m1: string, t1: string, m2: string, t2: string, m3: string, t3: string) => {
                const out = ['{{tt|' + t1 + '|on ' + m1.toLowerCase() + '}}'];
                if (m2) out.push('{{tt|' + t2 + '|on ' + m2.toLowerCase() + '}}');
                if (m3) out.push('{{tt|' + t3 + '|on ' + m3.toLowerCase() + '}}');
                return '(' + out.join('/') + ')';
            });

    s = s
        .replace(/—/g, '&mdash;')
        .replace(/\\\{–\}/g, '—')
        .replace(/\u00d7/g, '&times;')
        .replace(/'(<\s*\/?\s*(?:i|b)\s*>)/gi, '&ast;$1')
        .replace(/(<\s*\/?\s*(?:i|b)\s*>)'/gi, '&ast;$1')
        .replace(/<\s*\/?\s*i\s*>/gi, "''")
        .replace(/<\s*\/?\s*b\s*>/gi, "'''")
        .replace(/\u00a0/g, ctx.lang === 'KR' ? ' ' : '&nbsp;')
        .replace(/⟨⟨Цвет\|(\w+?)\|(\s*)([\s\S]+?)(\s*)⟩⟩/gi, '$2⟨⟨Цвет|$1|$3⟩⟩$4')
        .replace(/⟨⟨Цвет\|\w+?\|⟩⟩/gi, '')
        .replace(/<\/?unbreak>/gi, '')
        .split('{SPACE}').join(' ')
        .split('⟨').join('{')
        .split('⟩').join('}');

    return s;
}
