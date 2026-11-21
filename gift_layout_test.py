"""선물 연출 레이아웃 점검 — 여러 화면 크기에서 잘리지 않는지 (로컬 파일 + 더미 데이터)."""
import json
from playwright.sync_api import sync_playwright

FILE = "file:///workspace/work-famdash/index.html"

SEED = """
() => {
  const d = new Date(); const p = n => String(n).padStart(2, '0');
  const today = d.getFullYear() + '-' + p(d.getMonth() + 1) + '-' + p(d.getDate());
  localStorage.setItem('sora-home-dashboard-sync-v2', JSON.stringify({ off: true }));
  localStorage.setItem('sora-home-dashboard-v1', JSON.stringify({
    v: 1, xpTune: 1, xpTune2: 1, xpTune3: 1, orderTune1: 1, starterTune1: 1, nameTune1: 1,
    questDate: today, title: '우리가족 대시보드',
    kids: {
      haseong: { name: '하성', tag: '9살', partner: 'charmander', level: 20, xp: 195,
        dexOpen: ['charmander','pichu','cinnamoroll','mymelody','squirtle','hellokitty','bulbasaur','pompompurin','eevee','pochacco','pikachu','kuromi','jigglypuff','samurott','snorlax','psyduck','hooh','ditto','sharpedomega','totoro','steelixmega','genesect','mew'],
        quests: [{ id: 'h1', text: '리딩앤', xp: 10, done: false }] },
      hayun: { name: '하윤', tag: '7살', partner: 'pichu', level: 6, xp: 100,
        dexOpen: ['charmander','pichu','cinnamoroll','mymelody','squirtle','hellokitty','cinderella','bulbasaur','pompompurin'],
        quests: [{ id: 'y1', text: '한글 2장', xp: 20, done: false }] }
    }, events: {}, ddays: [], wishes: [], chat: { me: '엄마', msgs: [] }
  }));
}
"""

sizes = [(1920, 1080), (1440, 900), (1280, 800), (1024, 768), (834, 1112), (390, 844), (360, 640)]

with sync_playwright() as p:
    b = p.chromium.launch()
    for w, h in sizes:
        ctx = b.new_context(viewport={"width": w, "height": h})
        pg = ctx.new_page()
        errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.goto(FILE)
        pg.evaluate(SEED)
        pg.reload()
        pg.wait_for_timeout(800)
        pg.click('.kid-card[data-kid=haseong] .kid-top')
        pg.wait_for_timeout(350)
        pg.click('.kid-card[data-kid=haseong] .quest[data-id="h1"] .qcheck')
        pg.wait_for_timeout(800)
        s1 = pg.evaluate("""() => {
          const g = document.getElementById('giftLv').getBoundingClientRect();
          const stage = document.getElementById('giftStage').getBoundingClientRect();
          return { giftScroll: document.querySelector('#giftLv').scrollHeight > window.innerHeight + 1,
                   stageTop: Math.round(stage.top), stageBottom: Math.round(stage.bottom),
                   giftOn: document.getElementById('giftLv').classList.contains('on') };
        }""")
        box = pg.locator('#giftBox').bounding_box()
        pg.mouse.click(box['x'] + box['width'] / 2, box['y'] + box['height'] / 2)
        pg.wait_for_timeout(1100)
        s2 = pg.evaluate("""() => {
          const c = document.querySelector('.go-card');
          const r = c.getBoundingClientRect();
          return { cardTop: Math.round(r.top), cardBottom: Math.round(r.bottom),
                   cardW: Math.round(r.width), scrolls: c.scrollHeight > c.clientHeight + 1,
                   fits: r.top >= 0 && r.bottom <= window.innerHeight + 1 };
        }""")
        print(f"{w}x{h}", json.dumps([s1, s2], ensure_ascii=False), errs[:2])
        ctx.close()
    b.close()
