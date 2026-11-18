"""3칼럼 개편 미리보기 — 대화 12개가 들어간 1600×1000 (대화 내용이 얼마나 보이는지 확인용)"""
from playwright.sync_api import sync_playwright
from seed_v7 import SEED, FILE

with sync_playwright() as p:
    b = p.chromium.launch()

    def page(w, h, mobile=False):
        ctx = b.new_context(viewport={"width": w, "height": h}, is_mobile=mobile, has_touch=mobile)
        pg = ctx.new_page()
        errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.on("console", lambda m: errs.append("console:" + m.text) if m.type == "error" else None)
        pg.goto(FILE); pg.wait_for_timeout(500)
        pg.evaluate(SEED); pg.reload(); pg.wait_for_timeout(1500)
        return pg, errs

    pg, errs = page(1600, 1000)
    pg.screenshot(path="/workspace/downloads/대시보드_3칼럼_1600x1000.png")
    print("1600 messages visible:", pg.evaluate("""() => {
        const l = document.querySelector('.chat-log').getBoundingClientRect();
        return [...document.querySelectorAll('.chat-log .msg')].filter(m => {
          const r = m.getBoundingClientRect(); return r.top >= l.top - 1 && r.bottom <= l.bottom + 1; }).length;
    }"""))
    pg.click('.kid-card[data-kid=haseong] .kid-top'); pg.wait_for_timeout(900)
    pg.screenshot(path="/workspace/downloads/대시보드_3칼럼_퀘스트펼침_1600x1000.png")
    print("errors:", errs[:4])
    pg.context.close()

    pg, errs = page(1440, 900)
    pg.screenshot(path="/workspace/downloads/대시보드_3칼럼_1440x900.png")
    print("1440 errors:", errs[:4])
    pg.context.close()

    pg, errs = page(390, 844, mobile=True)
    pg.evaluate("document.querySelector('.kids-row').scrollIntoView({block:'start'})")
    pg.wait_for_timeout(500)
    pg.screenshot(path="/workspace/downloads/대시보드_3칼럼_모바일_390x844.png")
    print("390 errors:", errs[:4])
    pg.context.close()

    b.close()
