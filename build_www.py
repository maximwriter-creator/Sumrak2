#!/usr/bin/env python3
"""Собирает www/index.html из src/app.html и src/data.json.
Шрифты PT Sans / PT Sans Narrow / PT Serif встраиваются в страницу, чтобы приложение работало без интернета."""
import base64, json, os, re

ROOT = os.path.dirname(os.path.abspath(__file__))
FONTS = [
    ("PT Sans", "pt-sans", [("400", "normal"), ("700", "normal")]),
    ("PT Sans Narrow", "pt-sans-narrow", [("400", "normal"), ("700", "normal")]),
    ("PT Serif", "pt-serif", [("400", "normal"), ("700", "normal"), ("400", "italic")]),
]
SUBSETS = {"cyrillic": "U+0301,U+0400-045F,U+0490-0491,U+04B0-04B1,U+2116",
           "latin": "U+0000-00FF,U+0131,U+0152-0153,U+02BB-02BC,U+02C6,U+02DA,U+02DC,U+0304,U+0308,U+0329,U+2000-206F,U+20AC,U+2122,U+2191,U+2193,U+2212,U+2215,U+FEFF,U+FFFD"}

def font_css():
    out = []
    for family, pkg, variants in FONTS:
        base = os.path.join(ROOT, "node_modules", "@fontsource", pkg, "files")
        for weight, style in variants:
            for sub, rng in SUBSETS.items():
                fn = os.path.join(base, f"{pkg}-{sub}-{weight}-{style}.woff2")
                if not os.path.exists(fn):
                    print("нет файла шрифта:", fn); continue
                b64 = base64.b64encode(open(fn, "rb").read()).decode()
                out.append(f"@font-face{{font-family:'{family}';font-style:{style};font-weight:{weight};font-display:swap;"
                           f"src:url(data:font/woff2;base64,{b64}) format('woff2');unicode-range:{rng}}}")
    return "\n".join(out)

def main():
    app = open(os.path.join(ROOT, "src", "app.html"), encoding="utf-8").read()
    data = open(os.path.join(ROOT, "src", "data.json"), encoding="utf-8").read()
    json.loads(data)  # проверка, что данные книги — корректный JSON
    assert "__DATA__" in app, "в src/app.html нет плейсхолдера __DATA__"
    html = app.replace("__DATA__", data.replace("</", "<\\/"))
    html = re.sub(r'<link rel="preconnect"[^>]*>\s*', "", html)
    html = re.sub(r'<link href="https://fonts\.googleapis\.com[^>]*>', "<style>\n" + font_css() + "\n</style>", html)
    os.makedirs(os.path.join(ROOT, "www"), exist_ok=True)
    open(os.path.join(ROOT, "www", "index.html"), "w", encoding="utf-8").write(html)
    print("www/index.html собран:", round(len(html.encode()) / 1024), "КБ")

if __name__ == "__main__":
    main()
