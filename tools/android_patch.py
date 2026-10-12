#!/usr/bin/env python3
"""Правит android/app/build.gradle после `npx cap add android`:
   * versionCode = номер сборки, versionName = 1.<номер>;
   * подпись debug-сборки постоянным ключом из репозитория (иначе каждая сборка
     получит случайный ключ и APK не установится поверх старой версии).
   python3 tools/android_patch.py <номер сборки> <путь к keystore>"""
import pathlib, re, sys

num = int(sys.argv[1])
ks = pathlib.Path(sys.argv[2]).resolve()
if not ks.is_file():
    sys.exit(f'Нет файла ключа подписи: {ks}')
g = pathlib.Path('android/app/build.gradle')
s = g.read_text(encoding='utf-8')

s, n1 = re.subn(r'versionCode\s+\d+', f'versionCode {num}', s, count=1)
s, n2 = re.subn(r'versionName\s+"[^"]*"', f'versionName "1.{num}"', s, count=1)
if not (n1 and n2):
    sys.exit('В build.gradle не нашлись versionCode / versionName')

if 'signingConfigs {' not in s:
    signing = (
        '    signingConfigs {\n'
        '        debug {\n'
        f'            storeFile file("{ks.as_posix()}")\n'
        '            storePassword "android"\n'
        '            keyAlias "androiddebugkey"\n'
        '            keyPassword "android"\n'
        '        }\n'
        '    }\n')
    s, n3 = re.subn(r'(\n    buildTypes \{\n)', '\n' + signing + r'\1', s, count=1)
    if not n3:
        sys.exit('В build.gradle не нашёлся блок buildTypes')
    s, n4 = re.subn(r'(\n    buildTypes \{\n)', r'\1        debug {\n            signingConfig signingConfigs.debug\n        }\n', s, count=1)
    if not n4:
        sys.exit('Не удалось вписать подпись в buildTypes')
g.write_text(s, encoding='utf-8')
print(f'build.gradle: versionCode {num}, подпись {ks.name}')
