import json
from playwright.sync_api import sync_playwright

FILE = "file:///workspace/work-famdash/index.html"

LEGACY = """
(() => {
  const st = { v:1, kids: {
      haseong: { name:'하성이', partner:'charmander', level: 3, xp: 99 },
      hayun:   { name:'하윤이', partner:'pichu', level: 1, xp: 0 }
    }, ddays: [], wishes: [], chat: { me:'엄마', msgs: [] } };
  localStorage.setItem('sora-home-dashboard-v1', JSON.stringify(st));
  localStorage.setItem('sora-home-dashboard-sync-v2', JSON.stringify({ off:true }));
})();
"""

with sync_playwright() as p:
    b = p.chromium.launch()
    ctx = b.new_context(viewport={"width": 1600, "height": 1000})
    page = ctx.new_page()
    errs = []
    page.on("pageerror", lambda e: errs.append(str(e)))
    page.on("console", lambda m: errs.append("console:" + m.text) if m.type == "error" else None)
    page.add_init_script(LEGACY)
    page.goto(FILE)
    page.wait_for_timeout(900)
    if page.locator("#gateModal.open").count():
        page.click("#gateSkip"); page.wait_for_timeout(500)

    def snap(tag):
        return page.evaluate("""() => {
          const c = document.querySelector('.kid-card[data-kid="haseong"]');
          return { tag: arguments0,
            lv: c.querySelector('[data-lv]').textContent,
            xp: c.querySelector('[data-xptext]').textContent,
            bar: c.querySelector('[data-xpbar]').style.width,
            vmax: c.querySelector('.xp-track').getAttribute('aria-valuemax'),
            now: c.querySelector('.xp-track').getAttribute('aria-valuenow'),
            dex: c.querySelector('[data-dexcount]').textContent,
            celeb: document.querySelector('#celebrate').classList.contains('on'),
            celebSub: document.querySelector('#celebSub').textContent.trim(),
            quests: [...c.querySelectorAll('.quest')].map(q => [q.querySelector('.qtext')?.textContent || q.textContent.slice(0,6), q.querySelector('.qxp')?.textContent || ''])
          };
        }""")

    out = {}
    out["레거시 xp=99 로드"] = page.evaluate("""() => {
      const c = document.querySelector('.kid-card[data-kid=\\"haseong\\"]');
      return { lv: c.querySelector('[data-lv]').textContent, xp: c.querySelector('[data-xptext]').textContent,
               bar: c.querySelector('[data-xpbar]').style.width, dex: c.querySelector('[data-dexcount]').textContent };
    }""")

    # 카드는 기본이 접힘 — 퀘스트를 만지려면 먼저 펼쳐요
    page.click('.kid-card[data-kid="haseong"] .kid-top')
    page.wait_for_timeout(500)

    # 99 + 20 → 119 (레벨업 없음, 200 기준)
    page.click('.kid-card[data-kid="haseong"] .quest:first-child .qcheck')
    page.wait_for_timeout(400)
    out["99 + 20체크"] = page.evaluate("""() => {
      const c = document.querySelector('.kid-card[data-kid=\\"haseong\\"]');
      return { lv: c.querySelector('[data-lv]').textContent, xp: c.querySelector('[data-xptext]').textContent,
               bar: c.querySelector('[data-xpbar]').style.width, dex: c.querySelector('[data-dexcount]').textContent };
    }""")

    # 나머지 퀘스트 모두 체크 → 200 넘으면 레벨업
    for i in range(1, 5):
        page.click('.kid-card[data-kid="haseong"] .quest:nth-child(%d) .qcheck' % (i + 1))
        page.wait_for_timeout(250)
    out["추가 체크 후"] = page.evaluate("""() => {
      const c = document.querySelector('.kid-card[data-kid=\\"haseong\\"]');
      return { lv: c.querySelector('[data-lv]').textContent, xp: c.querySelector('[data-xptext]').textContent,
               bar: c.querySelector('[data-xpbar]').style.width, dex: c.querySelector('[data-dexcount]').textContent,
               celeb: document.querySelector('#celebrate').classList.contains('on'),
               sub: document.querySelector('#celebSub').textContent.trim(),
               title: document.querySelector('#celebTitle').textContent };
    }""")

    out["퀘스트 점수(하성이)"] = page.evaluate("""() => [...document.querySelectorAll('.kid-card[data-kid=\\"haseong\\"] .quest')].map(q => q.querySelector('.qxp').textContent)""")
    out["퀘스트 점수(하윤)"] = page.evaluate("""() => [...document.querySelectorAll('.kid-card[data-kid=\\"hayun\\"] .quest')].map(q => {
        const n = q.querySelector('.qxp'); return n ? n.textContent : null; })""")
    out["+5 옵션"] = page.evaluate("""() => [...document.querySelectorAll('.kid-card[data-kid=\\"haseong\\"] .q-xp option')].map(o => o.value)""")

    # +5 옵션으로 퀘스트 추가
    page.fill('.kid-card[data-kid="haseong"] .q-input', '테스트5점')
    page.select_option('.kid-card[data-kid="haseong"] .q-xp', '5')
    page.click('.kid-card[data-kid="haseong"] .q-add')
    page.wait_for_timeout(400)
    out["+5 추가 결과"] = page.evaluate("""() => {
      const qs=[...document.querySelectorAll('.kid-card[data-kid=\\"haseong\\"] .quest')];
      const last=qs[qs.length-1];
      const c=document.querySelector('.kid-card[data-kid=\\"haseong\\"]');
      return { last: last.textContent.replace(/\\s+/g,' ').trim(), cnt: qs.length, lv:c.querySelector('[data-lv]').textContent, xp:c.querySelector('[data-xptext]').textContent };
    }""")

    # 타이머 동작 확인 — v12부터 펼친 퀘스트는 타이머 위로 떠오르므로 먼저 접어요
    page.click('.kid-card[data-kid="haseong"] .kid-top')
    page.wait_for_timeout(600)
    page.click('.ttab[data-tmode="stopwatch"]')
    page.click('#swStart')
    page.wait_for_timeout(1600)
    out["스톱워치"] = page.evaluate("""() => ({ t: document.querySelector('#swDisplay').textContent, st: document.querySelector('#swState').textContent })""")
    page.click('#swStart')
    page.click('.ttab[data-tmode="timer"]')
    page.click('#timerStart')
    page.wait_for_timeout(1200)
    out["타이머"] = page.evaluate("""() => ({ t: document.querySelector('#timerDisplay').textContent, st: document.querySelector('#timerState').textContent, bar: document.querySelector('#timerBar').style.width })""")
    page.click('#timerPause')
    out["중지 후"] = page.evaluate("""() => ({ st: document.querySelector('#timerState').textContent, btn: document.querySelector('#timerStart').textContent })""")

    out["errors"] = errs
    print(json.dumps(out, ensure_ascii=False, indent=2))
    b.close()
