#!/usr/bin/env python3
"""Сборка www/index.html для APK.

src/app.html + src/data.json  →  www/index.html, в котором всё внутри файла:
  * данные Книги игрока (вместо __DATA__);
  * шрифты PT Sans / PT Sans Narrow / PT Serif (из node_modules/@fontsource, base64);
  * библиотека Supabase (из node_modules/@supabase/supabase-js), чтобы комнаты,
    облачная копия и карта «Кампейн» не зависели от CDN.

Запуск: python3 build_www.py   (после npm ci)
"""
import base64, json, pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parent
NM = ROOT / 'node_modules'
SRC_APP = ROOT / 'src' / 'app.html'
SRC_DATA = ROOT / 'src' / 'data.json'
OUT = ROOT / 'www' / 'index.html'

FONTS = [  # пакет, семейство, файлы css (вес/стиль)
    ('pt-sans', 'PT Sans', ['400.css', '700.css']),
    ('pt-sans-narrow', 'PT Sans Narrow', ['400.css', '700.css']),
    ('pt-serif', 'PT Serif', ['400.css', '700.css', '400-italic.css']),
]
SUBSETS = ('cyrillic-ext', 'cyrillic', 'latin-ext', 'latin')


def fail(msg):
    print('ОШИБКА СБОРКИ:', msg, file=sys.stderr)
    sys.exit(1)


def font_css():
    out = []
    for pkg, family, files in FONTS:
        base = NM / '@fontsource' / pkg
        if not base.is_dir():
            fail(f'нет node_modules/@fontsource/{pkg} — сначала npm ci')
        for f in files:
            css = (base / f).read_text(encoding='utf-8')
            for block in re.findall(r'@font-face\s*{[^}]*}', css):
                m = re.search(r"url\((?:\./)?(files/[^)]+?\.woff2)\)", block)
                if not m:
                    continue
                fname = m.group(1)
                if not any(f'-{s}-' in fname for s in SUBSETS):
                    continue
                data = base64.b64encode((base / fname).read_bytes()).decode('ascii')
                style = re.search(r'font-style:\s*([^;]+);', block).group(1).strip()
                weight = re.search(r'font-weight:\s*([^;]+);', block).group(1).strip()
                ur = re.search(r'unicode-range:\s*([^;]+);', block)
                out.append(
                    "@font-face{font-family:'%s';font-style:%s;font-weight:%s;font-display:swap;"
                    "src:url(data:font/woff2;base64,%s) format('woff2');%s}"
                    % (family, style, weight, data, ('unicode-range:' + ur.group(1).strip() + ';') if ur else ''))
    if len(out) < 10:
        fail(f'шрифтов найдено слишком мало ({len(out)}) — проверьте версии @fontsource')
    return '\n'.join(out)


def main():
    if not SRC_APP.exists():
        fail('нет src/app.html')
    if not SRC_DATA.exists():
        fail('нет src/data.json')
    html = SRC_APP.read_text(encoding='utf-8')
    if html.count('__DATA__') != 1:
        fail(f'в src/app.html должно быть ровно одно место __DATA__, найдено {html.count("__DATA__")}')
    data = json.loads(SRC_DATA.read_text(encoding='utf-8'))
    blob = json.dumps(data, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/')
    html = html.replace('__DATA__', blob, 1)

    # всё, что ниже, меняем только в <head> приложения — встроенную карту и данные это не затрагивает
    head_end = html.find('</head>')
    if head_end < 0:
        fail('в src/app.html нет </head>')
    head, rest = html[:head_end], html[head_end:]

    head = re.sub(r'<link[^>]+fonts\.(?:googleapis|gstatic)\.com[^>]*>\s*', '', head)
    head += '<style id="embedded-fonts">\n' + font_css() + '\n</style>\n'

    sb = NM / '@supabase' / 'supabase-js' / 'dist' / 'umd' / 'supabase.js'
    if not sb.exists():
        fail('нет node_modules/@supabase/supabase-js/dist/umd/supabase.js — сначала npm ci')
    js = sb.read_text(encoding='utf-8').replace('</script', '<\\/script')
    head += '<script id="embedded-supabase">' + js + '\n</script>\n'

    html = head + rest
    # контроль: блок карты и данные книги на месте
    if 'id="meccaSrc"' not in html:
        print('ВНИМАНИЕ: в приложении нет встроенной карты «Кампейн» (meccaSrc)', file=sys.stderr)
    if 'id="book"' not in html:
        fail('нет блока данных книги <script id="book">')
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(html, encoding='utf-8')
    print(f'www/index.html: {len(html.encode("utf-8")) / 1e6:.1f} МБ')


if __name__ == '__main__':
    main()
