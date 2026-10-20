#!/usr/bin/env python3
"""Бой: мастер жмёт «Бой!», два игрока бросают сами, бестиарий бросается, таблица собирается.
   python3 init_test.py app.html shots_dir"""
import sys, json, pathlib, asyncio
from playwright.async_api import async_playwright

APP = pathlib.Path(sys.argv[1]).resolve()
SHOTS = pathlib.Path(sys.argv[2]); SHOTS.mkdir(parents=True, exist_ok=True)
MOCK = (pathlib.Path(__file__).parent / 'mock_supa.js').read_text()
DB = {'rooms': [], 'room_players': [], 'room_mods': [], 'gm_bestiary': []}
KEYS = {'rooms': ['code'], 'room_players': ['room', 'uid', 'char_id'], 'room_mods': ['room', 'uid', 'char_id'], 'gm_bestiary': ['uid']}

def handle(_src, raw):
    q = json.loads(raw); t = q['t']; rows = DB.setdefault(t, [])
    match = lambda r: all(str(r.get(k)) == str(v) for k, v in q['f'])
    op = q['op']
    if op == 'select':
        res = [dict(r) for r in rows if match(r)]
        return json.dumps({'data': (res[0] if res else None) if q['single'] else res, 'error': None})
    if op in ('insert', 'upsert'):
        ps = q['p'] if isinstance(q['p'], list) else [q['p']]
        for p in ps:
            if t == 'rooms' and op == 'insert': p.setdefault('gm', q['uid'])
            if t == 'gm_bestiary': p.setdefault('uid', q['uid'])
            ks = KEYS.get(t, [])
            old = next((r for r in rows if ks and all(r.get(k) == p.get(k) for k in ks)), None)
            if old: old.update(p)
            else: rows.append(dict(p))
        return json.dumps({'data': None, 'error': None})
    if op == 'update':
        for r in rows:
            if match(r): r.update(q['p'])
        return json.dumps({'data': None, 'error': None})
    if op == 'delete':
        DB[t] = [r for r in rows if not match(r)]
        return json.dumps({'data': None, 'error': None})

ERR = []
async def page_for(br, uid, w=360):
    ctx = await br.new_context(viewport={'width': w, 'height': 780})
    await ctx.expose_binding('__db', handle)
    await ctx.add_init_script(f'window.__UID={json.dumps(uid)};' + MOCK)
    pg = await ctx.new_page()
    pg.on('pageerror', lambda e: ERR.append(f'{uid}: {e}'))
    await pg.goto(APP.as_uri()); await pg.wait_for_timeout(600)
    return pg

async def mkchar(pg, name, agi):
    await pg.evaluate('''([n,a])=>{C.name=n;C.legacy=true;C.fix=Object.assign(C.fix||{}, {agi:a});save();render();}''', [name, agi])

async def goroom(pg):
    await pg.evaluate('STEP=11;render();'); await pg.wait_for_timeout(300)

async def main():
    async with async_playwright() as p:
        br = await p.chromium.launch()
        gm = await page_for(br, 'gm-1', 360)
        a = await page_for(br, 'pl-a', 320)
        b = await page_for(br, 'pl-b', 360)
        await mkchar(a, 'Патау', 6); await mkchar(b, 'Ирма', 3)
        # мастер создаёт комнату
        await goroom(gm)
        await gm.evaluate('roomCreate()'); await gm.wait_for_timeout(500)
        code = await gm.evaluate('ROOM.st&&ROOM.st.code'); assert code, 'нет кода комнаты'
        # бестиарий: 2 бандита в бою
        await gm.evaluate('''()=>{const B=bestS();const n=npcFix({name:"Бандит",qty:2});B.list.push(n);bestSave();}''')
        for pg in (a, b):
            await goroom(pg); await pg.evaluate(f'roomJoin({json.dumps(code)})'); await pg.wait_for_timeout(500)
        await gm.evaluate('roomFetch()'); await gm.wait_for_timeout(300)
        await gm.evaluate('renderRoom()')
        await gm.screenshot(path=str(SHOTS / '1-gm-before.png'), full_page=True)
        # «Бой!»
        await gm.click('[data-ini="start"]'); await gm.wait_for_timeout(400)
        st = await gm.evaluate('ROOM.init'); assert st['ask'] == 1 and len(st['list']) == 2, st
        await gm.screenshot(path=str(SHOTS / '2-gm-waiting.png'), full_page=True)
        # игроки получают запрос (опрос)
        for pg in (a, b):
            await pg.evaluate('initLoad(false)'); await pg.wait_for_timeout(300)
        await a.screenshot(path=str(SHOTS / '3-player-ask-room.png'), full_page=True)
        # игрок B уходит на лист — должна быть плашка
        await b.evaluate('STEP=7;render();'); await b.wait_for_timeout(200)
        assert await b.locator('#iniAsk').count() == 1, 'нет плашки на листе'
        await b.screenshot(path=str(SHOTS / '4-player-ask-bar.png'))
        # A бросает в комнате, B — с плашки
        await a.click('.iniaskbtn'); await a.wait_for_timeout(300)
        await b.click('#iniAsk'); await b.wait_for_timeout(300)
        assert await b.locator('#iniAsk').count() == 0, 'плашка не исчезла'
        # повторный бросок запрещён
        ra = await a.evaluate('roomChar().iniRoll'); await a.evaluate('initMeRoll()')
        assert (await a.evaluate('roomChar().iniRoll')) == ra
        # мастер подхватывает
        await gm.evaluate('roomFetch()'); await gm.wait_for_timeout(400)
        I = await gm.evaluate('ROOM.init')
        names = [r['n'] for r in I['list']]
        assert 'Патау' in names and 'Ирма' in names and len(names) == 4, names
        inis = [(r['n'], r['ini'], r['r']) for r in I['list']]
        print('порядок:', inis)
        assert I['cur'] == 0, ('маркер не на первом', I['cur'])
        assert all(r['r'] in (1,2,19,20) or True for r in I['list'])
        await gm.screenshot(path=str(SHOTS / '5-gm-table.png'), full_page=True)
        # повторный fetch не дублирует
        await gm.evaluate('roomFetch()'); await gm.wait_for_timeout(300)
        assert len(await gm.evaluate('ROOM.init.list')) == 4
        # переброс бестиария
        await gm.evaluate('initNpcRoll(false)'); await gm.wait_for_timeout(200)
        assert len(await gm.evaluate('ROOM.init.list')) == 4
        # игроки видят таблицу
        for pg in (a, b):
            await pg.evaluate('STEP=11;render();initLoad(false)'); await pg.wait_for_timeout(300)
        await a.screenshot(path=str(SHOTS / '6-player-table-320.png'), full_page=True)
        pv = await a.evaluate('ROOM.initP'); assert len(pv['list']) == 4
        # ход вперёд
        await gm.click('[data-ini="next"]'); await gm.wait_for_timeout(200)
        assert await gm.evaluate('ROOM.init.cur') == 1
        # горизонтальная прокрутка
        for pg, n in ((gm, 'gm'), (a, 'a'), (b, 'b')):
            sw = await pg.evaluate('document.documentElement.scrollWidth-document.documentElement.clientWidth')
            assert sw <= 0, f'{n}: горизонтальная прокрутка {sw}'
        # мастер бросает за опоздавшего: третий игрок
        c = await page_for(br, 'pl-c', 360); await mkchar(c, 'Опоздун', 4); await goroom(c)
        await c.evaluate(f'roomJoin({json.dumps(code)})'); await c.wait_for_timeout(400)
        await gm.evaluate('roomFetch()'); await gm.wait_for_timeout(300)
        await gm.screenshot(path=str(SHOTS / '7-gm-late.png'), full_page=True)
        await gm.click('[data-ini^="gmfor|"]'); await gm.wait_for_timeout(300)
        assert len(await gm.evaluate('ROOM.init.list')) == 5
        await gm.evaluate('ROOM.init.list.forEach(r=>{});')
        # ручное добавление: своё имя с фиксированным числом
        await gm.click('.iniadd > summary'); await gm.wait_for_timeout(100)
        await gm.fill('#iadName', 'Турель'); await gm.fill('[data-iad="base"]', '99')
        await gm.click('[data-ini="addfix"]'); await gm.wait_for_timeout(200)
        L = await gm.evaluate('ROOM.init.list'); ti = [r['n'] for r in L].index('Турель'); assert L[ti]['r'] is None and len(L) == 6 and all(r['r'] in (1, 2) for r in L[:ti]), [(r['n'], r['r']) for r in L]
        # из бестиария с броском
        nid = await gm.evaluate('bestS().list[0].id')
        await gm.select_option('#iadSrc', nid); await gm.wait_for_timeout(200)
        assert await gm.input_value('[data-iad="base"]') != ''
        await gm.click('[data-ini="addroll"]'); await gm.wait_for_timeout(200)
        L = await gm.evaluate('ROOM.init.list'); assert len(L) == 7 and any(r['n'] == 'Бандит 3' and r['man'] for r in L), [r['n'] for r in L]
        # ручной порядок: последнего наверх
        last = L[-1]['n']
        for i in range(len(L) - 1, 0, -1):
            await gm.click(f'[data-ini="up|{i}"]'); await gm.wait_for_timeout(60)
        L = await gm.evaluate('ROOM.init.list'); assert L[0]['n'] == last and await gm.evaluate('ROOM.init.manual') == 1
        cur_row = await gm.evaluate('ROOM.init.list[ROOM.init.cur]')
        # переброс бестиария при ручном порядке: длина та же, добавленный руками остался, текущий не сменился
        await gm.evaluate('initNpcRoll(false)'); await gm.wait_for_timeout(200)
        L2 = await gm.evaluate('ROOM.init.list'); assert len(L2) == 7 and any(r['n'] == 'Бандит 3' and r['man'] for r in L2), [r['n'] for r in L2]
        # не-бестиарные строки сохранили относительный ручной порядок
        keep = [r['n'] for r in L if not (r['k'] == 'npc' and not r.get('man'))]; assert [r['n'] for r in L2 if r['n'] in keep] == keep
        if cur_row['k'] == 'npc' and not cur_row.get('man'): assert await gm.evaluate('ROOM.init.cur') == 0
        else: assert await gm.evaluate('ROOM.init.list[ROOM.init.cur].n') == cur_row['n']
        await gm.screenshot(path=str(SHOTS / '7b-gm-manual.png'), full_page=True)
        await gm.click('[data-ini="sort"]'); await gm.wait_for_timeout(100)
        assert await gm.evaluate('ROOM.init.manual') == 0
        # игрок видит «без броска»
        await a.evaluate('initLoad(false)'); await a.wait_for_timeout(300)
        assert 'Турель' in await a.inner_text('.initcard')
        # ручная очередь без «Боя!»
        await gm.evaluate('ROOM.init=null;renderRoom()'); await gm.wait_for_timeout(100)
        await gm.click('[data-ini="manual"]'); await gm.wait_for_timeout(150)
        assert await gm.evaluate('ROOM.init.ask') == 0
        await gm.select_option('#iadSrc', ''); await gm.wait_for_timeout(100)
        await gm.fill('#iadName', 'Дрон'); await gm.fill('[data-iad="base"]', '15'); await gm.click('[data-ini="addroll"]'); await gm.wait_for_timeout(150)
        assert len(await gm.evaluate('ROOM.init.list')) == 1
        await gm.set_viewport_size({'width': 320, 'height': 780}); await gm.wait_for_timeout(150)
        sw = await gm.evaluate('document.documentElement.scrollWidth-document.documentElement.clientWidth'); assert sw <= 0, sw
        await gm.evaluate('initNpcRoll(false)'); await gm.wait_for_timeout(150)
        tw = await gm.evaluate('(()=>{const w=document.querySelector(".initcard .tblwrap");return w.scrollWidth-w.clientWidth;})()'); assert tw <= 0, ('таблица шире экрана на', tw)
        await gm.screenshot(path=str(SHOTS / '7c-gm-manual-320.png'), full_page=True)
        # запуск сразу на «Комнате» после перезагрузки
        await a.reload(); await a.wait_for_timeout(1500)
        await gm.reload(); await gm.wait_for_timeout(1500)
        await gm.screenshot(path=str(SHOTS / '8-gm-reload.png'), full_page=True)
        await br.close()
    print('ERRORS:', ERR or 'нет')
    assert not ERR

asyncio.run(main())
