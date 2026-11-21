"""레벨업 선물상자 동작 검증 — 로컬 파일 + 더미 데이터만 (실제 가족 방·라이브 URL 접속 없음)."""
import json
from playwright.sync_api import sync_playwright

FILE = "file:///workspace/work-famdash/index.html"

SEED = """
(cfg) => {
  const d = new Date();
  const p = n => String(n).padStart(2, '0');
  const today = d.getFullYear() + '-' + p(d.getMonth() + 1) + '-' + p(d.getDate());
  localStorage.clear();
  localStorage.setItem('sora-home-dashboard-sync-v2', JSON.stringify({ off: true }));
  const quests = cfg.quests || [];
  const st = {
    v: 1, xpTune: 1, xpTune2: 1, xpTune3: 1, orderTune1: 1, starterTune1: 1, nameTune1: 1,
    questDate: today, title: '우리가족 대시보드',
    kids: {
      haseong: { name: '하성', tag: '9살', partner: 'charmander', level: cfg.hsLevel || 8, xp: cfg.hsXp || 0,
        dexOpen: cfg.hsDex || [], quests: cfg.hsQuests || [{ id: 'h1', text: '리딩앤', xp: 10, done: false }] },
      hayun: { name: '하윤', tag: '7살', partner: 'pichu', level: cfg.hyLevel || 3, xp: cfg.hyXp || 0,
        dexOpen: cfg.hyDex || [], quests: quests }
    },
    events: {}, ddays: [], wishes: [], chat: { me: '엄마', msgs: [] }
  };
  localStorage.setItem('sora-home-dashboard-v1', JSON.stringify(st));
}
"""

HS_SEQ = ['charmander','pichu','cinnamoroll','mymelody','squirtle','hellokitty','bulbasaur','pompompurin','eevee','pochacco','pikachu','kuromi','jigglypuff','samurott','snorlax','psyduck','hooh','ditto','sharpedomega','totoro','steelixmega','genesect','mew','caterpie','palkia','dialga','kyogreprimal','groudonprimal','charizardmegax','charizardmegay','giratina','arceus']
HY_SEQ = ['charmander','pichu','cinnamoroll','mymelody','squirtle','hellokitty','cinderella','bulbasaur','pompompurin','rapunzel','eevee','pochacco','belle','pikachu','kuromi','ariel','snowwhite','elsa','jigglypuff','snorlax','psyduck','ditto','mew','totoro','ainyang','kokonyang','ttokttoknyang','bebenyang','daldalnyang','helssinyang','ippeunyang','reobeunyang']


def new_page(b, cfg, width=1440, height=900):
    ctx = b.new_context(viewport={"width": width, "height": height})
    pg = ctx.new_page()
    errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.goto(FILE)
    pg.evaluate(SEED, cfg)
    pg.reload()
    pg.wait_for_timeout(900)
    return ctx, pg, errs


def click_box(pg):
    box = pg.locator('#giftBox').bounding_box()
    pg.mouse.click(box['x'] + box['width'] / 2, box['y'] + box['height'] / 2)


with sync_playwright() as p:
    b = p.chromium.launch()

    # A) 한 번에 2레벨 — 친구 두 마리, 칩 전환, 파트너로 데려가기
    cfg = {"hyLevel": 3, "hyXp": 10, "hyDex": HY_SEQ[:6],
           "quests": [{"id": 'y1', "text": '한글 2장', "xp": 400, "done": False},
                      {"id": 'y2', "text": '수학 2장', "xp": 20, "done": False}]}
    ctx, pg, errs = new_page(b, cfg)
    pg.click('.kid-card[data-kid=hayun] .kid-top')
    pg.wait_for_timeout(500)
    pg.click('.kid-card[data-kid=hayun] .quest[data-id="y1"] .qcheck')
    pg.wait_for_timeout(900)
    s1 = pg.evaluate("""() => ({
      on: document.getElementById('giftLv').classList.contains('on'),
      badge: document.getElementById('giftBadge').textContent.trim(),
      level: document.querySelector('.kid-card[data-kid=hayun] [data-lv]').textContent,
      dex: document.querySelector('.kid-card[data-kid=hayun] [data-dexcount]').textContent
    })""")
    click_box(pg)
    pg.wait_for_timeout(1200)
    s2 = pg.evaluate("""() => ({
      opened: !document.getElementById('giftOpen').hidden,
      chips: [...document.querySelectorAll('.go-chip')].map(c => c.textContent.trim()),
      name: document.getElementById('goName').textContent.trim(),
      dex: document.getElementById('goDex').textContent.trim()
    })""")
    # 첫 칩(다른 친구) 눌러 소개 바꾸기
    pg.click('.go-chip:first-of-type')
    pg.wait_for_timeout(250)
    s3 = pg.evaluate("""() => ({ name: document.getElementById('goName').textContent.trim(),
                                  desc: document.getElementById('goDesc').textContent.trim(),
                                  take: document.getElementById('giftTake').textContent.trim() })""")
    pg.click('#giftTake')
    pg.wait_for_timeout(600)
    s4 = pg.evaluate("""() => ({
      on: document.getElementById('giftLv').classList.contains('on'),
      partner: document.querySelector('.kid-card[data-kid=hayun] [data-petname]').textContent,
      hifive: document.getElementById('hiFive').classList.contains('on'),
      saved: JSON.parse(localStorage.getItem('sora-home-dashboard-v1')).kids.hayun.partner
    })""")
    print("A multi-level:", json.dumps([s1, s2, s3, s4], ensure_ascii=False))
    print("A errors:", errs[:3])
    ctx.close()

    # B) 도감 완성 상태에서 레벨업 — 특별 축하, 파트너 버튼 숨김
    cfg = {"hsLevel": 32, "hsXp": 195, "hsDex": HS_SEQ,
           "hsQuests": [{"id": 'h1', "text": '리딩앤', "xp": 10, "done": False}]}
    ctx, pg, errs = new_page(b, cfg)
    pg.click('.kid-card[data-kid=haseong] .kid-top')
    pg.wait_for_timeout(400)
    pg.click('.kid-card[data-kid=haseong] .quest[data-id="h1"] .qcheck')
    pg.wait_for_timeout(800)
    click_box(pg)
    pg.wait_for_timeout(1100)
    s = pg.evaluate("""() => ({
      opened: !document.getElementById('giftOpen').hidden,
      tag: document.getElementById('goTag').textContent.trim(),
      name: document.getElementById('goName').textContent.trim(),
      desc: document.getElementById('goDesc').textContent.trim(),
      takeHidden: document.getElementById('giftTake').hidden,
      chips: document.querySelectorAll('.go-chip').length
    })""")
    print("B dex complete:", json.dumps(s, ensure_ascii=False))
    print("B errors:", errs[:3])
    ctx.close()

    # C) 체크 취소(레벨 다운) — 선물이 뜨지 않아야 함
    cfg = {"hsLevel": 9, "hsXp": 5, "hsDex": HS_SEQ[:12],
           "hsQuests": [{"id": 'h1', "text": '리딩앤', "xp": 10, "done": True}]}
    ctx, pg, errs = new_page(b, cfg)
    pg.click('.kid-card[data-kid=haseong] .kid-top')
    pg.wait_for_timeout(400)
    pg.click('.kid-card[data-kid=haseong] .quest[data-id="h1"] .qcheck')
    pg.wait_for_timeout(700)
    s = pg.evaluate("""() => ({
      on: document.getElementById('giftLv').classList.contains('on'),
      level: document.querySelector('.kid-card[data-kid=haseong] [data-lv]').textContent,
      xp: document.querySelector('.kid-card[data-kid=haseong] [data-xptext]').textContent
    })""")
    print("C level down:", json.dumps(s, ensure_ascii=False))
    print("C errors:", errs[:3])
    ctx.close()

    # D) 마지막 퀘스트로 레벨업 + 오늘 퀘스트 100% — 선물 닫으면 하이파이브
    cfg = {"hyLevel": 2, "hyXp": 170, "hyDex": HY_SEQ[:5],
           "quests": [{"id": 'y1', "text": '한글 2장', "xp": 20, "done": True},
                      {"id": 'y2', "text": '수학 2장', "xp": 20, "done": False}]}
    ctx, pg, errs = new_page(b, cfg)
    pg.click('.kid-card[data-kid=hayun] .kid-top')
    pg.wait_for_timeout(400)
    pg.click('.kid-card[data-kid=hayun] .quest[data-id="y2"] .qcheck')
    pg.wait_for_timeout(800)
    s1 = pg.evaluate("""() => ({ gift: document.getElementById('giftLv').classList.contains('on'),
                                 hifive: document.getElementById('hiFive').classList.contains('on') })""")
    click_box(pg)
    pg.wait_for_timeout(1000)
    s2 = pg.evaluate("""() => ({ gift: document.getElementById('giftLv').classList.contains('on'),
                                 hifive: document.getElementById('hiFive').classList.contains('on') })""")
    pg.click('#giftCloseBtn')
    pg.wait_for_timeout(900)
    s3 = pg.evaluate("""() => ({ gift: document.getElementById('giftLv').classList.contains('on'),
                                 hifive: document.getElementById('hiFive').classList.contains('on'),
                                 sub: document.getElementById('hfSub').textContent.trim(),
                                 partner: JSON.parse(localStorage.getItem('sora-home-dashboard-v1')).kids.hayun.partner })""")
    print("D hifive:", json.dumps([s1, s2, s3], ensure_ascii=False))
    print("D errors:", errs[:3])
    ctx.close()

    # E) ESC로 닫기
    cfg = {"hsLevel": 8, "hsXp": 195, "hsDex": HS_SEQ[:11],
           "hsQuests": [{"id": 'h1', "text": '리딩앤', "xp": 10, "done": False}]}
    ctx, pg, errs = new_page(b, cfg)
    pg.click('.kid-card[data-kid=haseong] .kid-top')
    pg.wait_for_timeout(400)
    pg.click('.kid-card[data-kid=haseong] .quest[data-id="h1"] .qcheck')
    pg.wait_for_timeout(700)
    pg.keyboard.press('Escape')
    pg.wait_for_timeout(500)
    s = pg.evaluate("""() => ({ on: document.getElementById('giftLv').classList.contains('on'),
                                body: document.body.classList.contains('gift-open') })""")
    print("E esc:", json.dumps(s, ensure_ascii=False))
    print("E errors:", errs[:3])
    ctx.close()

    # F) 휴대폰 화면 두 단계
    ctx, pg, errs = new_page(b, cfg, width=390, height=844)
    pg.click('.kid-card[data-kid=haseong] .kid-top')
    pg.wait_for_timeout(400)
    pg.click('.kid-card[data-kid=haseong] .quest[data-id="h1"] .qcheck')
    pg.wait_for_timeout(800)
    pg.screenshot(path="/workspace/downloads/레벨업_선물상자_모바일.png")
    click_box(pg)
    pg.wait_for_timeout(1200)
    pg.screenshot(path="/workspace/downloads/레벨업_캐릭터_소개_모바일.png")
    s = pg.evaluate("""() => ({ scrollable: document.querySelector('.go-card').scrollHeight > window.innerHeight,
                                cardH: document.querySelector('.go-card').getBoundingClientRect().height })""")
    print("F mobile:", json.dumps(s, ensure_ascii=False), errs[:3])
    ctx.close()

    b.close()
