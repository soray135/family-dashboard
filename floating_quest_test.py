"""플로팅 퀘스트 확장 검증 (로컬 파일 + 더미 데이터만 · 라이브 URL/실제 방 접근 없음)
· PC(1600×1000, 1440×900, 1366×768, 1280×800): 퀘스트를 펼쳐도 왼쪽·오른쪽·타이머·사주세요 0px,
  하성이 10개 퀘스트가 스크롤 없이 전부 보임, 옆 아이 카드 자리 그대로, ESC/바깥 클릭/접기 버튼으로 닫힘, JS 오류 0
· 390×844 / 1024×768: 자연스럽게 펼쳐져 퀘스트가 잘리지 않음(내부 스크롤 없음), JS 오류 0
"""
import sys
from playwright.sync_api import sync_playwright

from seed_v7 import FILE, SEED

FAIL = []
SHOTS = "/workspace/downloads"


def chk(name, cond, extra=""):
    print(("  OK   " if cond else "  FAIL ") + name + ("" if cond else f"   {extra}"))
    if not cond:
        FAIL.append(name)


GEO = r"""() => {
  const sy = window.scrollY, sx = window.scrollX;
  const r = el => { if (!el) return null; const x = el.getBoundingClientRect();
    return {t:+(x.top+sy).toFixed(2), b:+(x.bottom+sy).toFixed(2), h:+x.height.toFixed(2),
            w:+x.width.toFixed(2), l:+(x.left+sx).toFixed(2)}; };
  const q = s => document.querySelector(s);
  const out = {cols:{}, left:{}, right:{}, docH:document.documentElement.scrollHeight,
               innerH:innerHeight, docW:document.documentElement.scrollWidth, innerW:innerWidth};
  out.cols.L = r(q('.col-left')); out.cols.C = r(q('.col-center')); out.cols.R = r(q('.col-chat'));
  out.left.weather = r(q('.weather-card')); out.left.cal = r(q('.cal-card')); out.left.dday = r(q('.dday-card'));
  out.right.card = r(q('.chat-card')); out.right.log = r(q('.chat-log')); out.right.form = r(q('.chat-form'));
  out.kids = r(q('.kids-row'));
  out.timer = r(q('.timer-card')); out.wish = r(q('.wish-card'));
  out.cards = {};
  ['haseong','hayun'].forEach(k => {
    const c = q('.kid-card[data-kid=' + k + ']');
    const ul = c.querySelector('[data-quests]');
    out.cards[k] = {card:r(c), ul:r(ul), n:ul.children.length,
                    ulScroll:[ul.scrollHeight, ul.clientHeight], cardScroll:c.scrollHeight,
                    fx:c.classList.contains('fx'), open:c.classList.contains('open'),
                    pet:r(c.querySelector('.pet')), form:r(c.querySelector('[data-qform]'))};
  });
  return out;
}"""


def diffs(base, cur):
    bad = []
    for grp in ("left", "right"):
        for k, a in base[grp].items():
            c = cur[grp][k]
            d = {f: round(c[f] - a[f], 2) for f in ("t", "b", "h", "w", "l") if abs(c[f] - a[f]) > 0.01}
            if d:
                bad.append(f"{k}{d}")
    for k in ("L", "R"):
        a, c = base["cols"][k], cur["cols"][k]
        d = {f: round(c[f] - a[f], 2) for f in ("t", "b", "h", "w", "l") if abs(c[f] - a[f]) > 0.01}
        if d:
            bad.append(f"col-{k}{d}")
    for k in ("timer", "wish"):
        a, c = base[k], cur[k]
        d = {f: round(c[f] - a[f], 2) for f in ("t", "b", "h", "w", "l") if abs(c[f] - a[f]) > 0.01}
        if d:
            bad.append(f"{k}{d}")
    return bad


def open_page(b, w, h, mobile=False):
    ctx = b.new_context(viewport={"width": w, "height": h}, is_mobile=mobile, has_touch=mobile)
    pg = ctx.new_page()
    errs = []
    pg.on("pageerror", lambda e: errs.append("pageerror:" + str(e)))
    pg.on("console", lambda m: errs.append("console:" + m.text) if m.type == "error" else None)
    pg.goto(FILE); pg.wait_for_timeout(400)
    pg.evaluate(SEED)
    pg.reload(); pg.wait_for_timeout(1300)
    return pg, errs


def reset(pg):
    for _ in range(3):
        if pg.eval_on_selector_all('.kid-card.open', 'els => els.length') == 0:
            return
        pg.eval_on_selector('.kid-card.open .kid-top', 'e => e.click()')
        pg.wait_for_timeout(600)


def open_kid(pg, kid):
    pg.click(f'.kid-card[data-kid={kid}] .kid-top')
    pg.wait_for_timeout(650)


with sync_playwright() as p:
    b = p.chromium.launch()

    for W, H in [(1600, 1000), (1440, 900), (1366, 768), (1280, 800)]:
        print(f"[{W}×{H} · 플로팅 확장]")
        pg, errs = open_page(b, W, H)
        base = pg.evaluate(GEO)

        for kid, other in (("haseong", "hayun"), ("hayun", "haseong")):
            reset(pg)
            open_kid(pg, kid)
            cur = pg.evaluate(GEO)
            d = diffs(base, cur)
            chk(f"{kid} 펼침 — 왼쪽·오른쪽·타이머·사주세요 위치/크기 0px", not d, d)
            c = cur["cards"][kid]
            chk(f"{kid} 펼침 — 카드가 플로팅(fx)으로 떠 있음", c["fx"] and c["open"], c["fx"])
            chk(f"{kid} 펼침 — 원래 자리(top/left/width) 유지",
                abs(c["card"]["t"] - base["cards"][kid]["card"]["t"]) <= 0.6
                and abs(c["card"]["l"] - base["cards"][kid]["card"]["l"]) <= 0.6
                and abs(c["card"]["w"] - base["cards"][kid]["card"]["w"]) <= 0.6,
                (base["cards"][kid]["card"], c["card"]))
            chk(f"{kid} 펼침 — 아래로 늘어남(높이 >= 원래, 화면 아래로는 안 넘침)",
                c["card"]["h"] >= base["cards"][kid]["card"]["h"] - 0.6 and c["card"]["b"] <= cur["innerH"] - 8,
                (base["cards"][kid]["card"]["h"], c["card"]["h"], c["card"]["b"], cur["innerH"]))
            chk(f"{kid} 펼침 — 퀘스트 {c['n']}개가 스크롤 없이 전부 보임",
                c["n"] > 0 and c["ulScroll"][0] <= c["ulScroll"][1] + 1,
                (c["n"], c["ulScroll"]))
            o = cur["cards"][other]
            chk(f"{kid} 펼침 — 접힌 {other} 카드는 원래 크기·자리 그대로",
                abs(o["card"]["h"] - base["cards"][other]["card"]["h"]) <= 0.6
                and abs(o["card"]["t"] - base["cards"][other]["card"]["t"]) <= 0.6
                and abs(o["card"]["l"] - base["cards"][other]["card"]["l"]) <= 0.6
                and abs(o["pet"]["w"] - base["cards"][other]["pet"]["w"]) <= 0.6,
                (base["cards"][other]["card"], o["card"], base["cards"][other]["pet"], o["pet"]))
            chk(f"{kid} 펼침 — 페이지 가로 스크롤 없음", cur["docW"] <= cur["innerW"] + 1,
                (cur["docW"], cur["innerW"]))
            print(f"       · 카드 높이 {base['cards'][kid]['card']['h']:.0f} → {c['card']['h']:.0f}px · "
                  f"퀘스트 {c['ulScroll'][0]}px/보임 {c['ulScroll'][1]}px · z-플로팅 {c['fx']}")

        # 닫기: 카드 바깥 클릭 / ESC / 접기 버튼
        reset(pg); open_kid(pg, "haseong")
        pg.mouse.click(20, 20)   # 왼쪽 위 빈 곳(카드 바깥)
        pg.wait_for_timeout(550)
        g = pg.evaluate(GEO)
        chk("카드 바깥 클릭 → 접힘", not g["cards"]["haseong"]["open"] and not g["cards"]["haseong"]["fx"],
            g["cards"]["haseong"])
        chk("바깥 클릭으로 접은 뒤 원래 배치 복귀", not diffs(base, g), diffs(base, g))

        open_kid(pg, "haseong")
        pg.keyboard.press("Escape")
        pg.wait_for_timeout(550)
        g = pg.evaluate(GEO)
        chk("ESC → 접힘", not g["cards"]["haseong"]["open"] and not g["cards"]["haseong"]["fx"]
            and not diffs(base, g), (g["cards"]["haseong"]["open"], diffs(base, g)))

        # 퀘스트 체크·추가·삭제·드래그는 카드를 닫지 않아야 함
        open_kid(pg, "haseong")
        pg.click('.kid-card[data-kid=haseong] .quest .qcheck')
        pg.wait_for_timeout(350)
        g = pg.evaluate(GEO)
        chk("퀘스트 체크해도 카드가 닫히지 않음", g["cards"]["haseong"]["open"] and g["cards"]["haseong"]["fx"],
            g["cards"]["haseong"])
        done_after = pg.evaluate("() => document.querySelectorAll('.kid-card[data-kid=haseong] .quest.done').length")
        chk("퀘스트 체크가 실제로 반영됨", done_after >= 1, done_after)
        pg.fill('.kid-card[data-kid=haseong] .q-input', '테스트 퀘스트')
        pg.click('.kid-card[data-kid=haseong] .q-add')
        pg.wait_for_timeout(400)
        g = pg.evaluate(GEO)
        chk("퀘스트 추가해도 카드가 닫히지 않음(추가 11개)",
            g["cards"]["haseong"]["open"] and g["cards"]["haseong"]["n"] == 11, g["cards"]["haseong"]["n"])
        chk("퀘스트 11개도 스크롤 없이 전부 보임 또는 안전선 안에서만 스크롤",
            g["cards"]["haseong"]["ulScroll"][0] <= g["cards"]["haseong"]["ulScroll"][1] + 1
            or g["cards"]["haseong"]["card"]["b"] <= g["innerH"] - 8,
            (g["cards"]["haseong"]["ulScroll"], g["cards"]["haseong"]["card"]["b"], g["innerH"]))
        pg.click('.kid-card[data-kid=haseong] .quest:last-child .qdel', force=True)
        pg.wait_for_timeout(400)
        g = pg.evaluate(GEO)
        chk("퀘스트 삭제해도 카드가 닫히지 않음", g["cards"]["haseong"]["open"] and g["cards"]["haseong"]["n"] == 10,
            (g["cards"]["haseong"]["open"], g["cards"]["haseong"]["n"]))

        # 길게 눌러 순서 바꾸기 / 하루 초기화도 카드를 닫지 않아야 함
        order0 = pg.eval_on_selector_all('.kid-card[data-kid=haseong] .quest .qtext', 'els => els.map(e => e.textContent)')
        bb = pg.locator('.kid-card[data-kid=haseong] .quest').nth(0).bounding_box()
        x, y = bb["x"] + bb["width"] / 2, bb["y"] + bb["height"] / 2
        pg.mouse.move(x, y)
        pg.mouse.down()
        pg.wait_for_timeout(520)
        for i in range(1, 9):
            pg.mouse.move(x, y + i * 12)
            pg.wait_for_timeout(25)
        pg.mouse.up()
        pg.wait_for_timeout(400)
        order1 = pg.eval_on_selector_all('.kid-card[data-kid=haseong] .quest .qtext', 'els => els.map(e => e.textContent)')
        g = pg.evaluate(GEO)
        chk("롤프레스 드래그로 순서가 바뀌고 카드는 열린 채", order0 != order1 and g["cards"]["haseong"]["open"],
            (order0, order1, g["cards"]["haseong"]["open"]))
        chk("드래그 뒤에도 퀘스트가 전부 보임", g["cards"]["haseong"]["ulScroll"][0] <= g["cards"]["haseong"]["ulScroll"][1] + 1,
            g["cards"]["haseong"]["ulScroll"])
        pg.click('.kid-card[data-kid=haseong] [data-reset]')
        pg.wait_for_timeout(400)
        g = pg.evaluate(GEO)
        chk("하루 초기화를 눌러도 카드는 열린 채", g["cards"]["haseong"]["open"]
            and pg.evaluate("() => document.querySelectorAll('.kid-card[data-kid=haseong] .quest.done').length") == 0)

        # 도감 버튼 → 모달이 뜨고 카드는 유지, ESC는 모달만 닫음
        pg.click('.kid-card[data-kid=haseong] [data-dex]')
        pg.wait_for_timeout(450)
        chk("도감 버튼 → 도감 모달 열림", pg.eval_on_selector('#dexModal', 'e => e.classList.contains("open")'))
        pg.keyboard.press("Escape")
        pg.wait_for_timeout(400)
        g = pg.evaluate(GEO)
        chk("도감 모달에서 ESC → 모달만 닫히고 카드는 유지",
            not pg.eval_on_selector('#dexModal', 'e => e.classList.contains("open")') and g["cards"]["haseong"]["open"])

        # 접기 버튼(퀘스트 접기)
        pg.click('.kid-card[data-kid=haseong] .kid-toggle')
        pg.wait_for_timeout(600)
        g = pg.evaluate(GEO)
        chk("퀘스트 접기 버튼 → 접힘", not g["cards"]["haseong"]["open"] and not diffs(base, g), diffs(base, g))

        # 한 아이를 연 채 다른 아이를 열면 앞 카드는 접히고, 뒤 카드가 떠오름
        reset(pg); open_kid(pg, "haseong"); open_kid(pg, "hayun")
        g = pg.evaluate(GEO)
        chk("하성이 연 채 하윤이를 열면 하성이만 접히고 하윤이가 뜸",
            g["cards"]["hayun"]["fx"] and not g["cards"]["haseong"]["fx"]
            and not g["cards"]["haseong"]["open"] and not diffs(base, g),
            (g["cards"]["hayun"]["fx"], g["cards"]["haseong"]["open"], diffs(base, g)))
        chk("JS 오류 0", not errs, errs[:3])

        if (W, H) == (1600, 1000):
            reset(pg); open_kid(pg, "haseong")
            pg.screenshot(path=SHOTS + "/대시보드_플로팅퀘스트_1600x1000.png")
            print("       저장: 대시보드_플로팅퀘스트_1600x1000.png")
            reset(pg); open_kid(pg, "hayun")
            pg.screenshot(path=SHOTS + "/대시보드_플로팅퀘스트_하윤_1600x1000.png")
        pg.context.close()

    print("[390×844 · 모바일]")
    pg, errs = open_page(b, 390, 844, mobile=True)
    base = pg.evaluate(GEO)
    open_kid(pg, "haseong")
    g = pg.evaluate(GEO)
    c = g["cards"]["haseong"]
    chk("모바일: 퀘스트가 자연스럽게 펼쳐짐(플로팅 아님)", c["open"] and not c["fx"], (c["open"], c["fx"]))
    chk("모바일: 하성이 10개 퀘스트가 잘리지 않고 전부 보임", c["n"] == 10 and c["ulScroll"][0] <= c["ulScroll"][1] + 1,
        (c["n"], c["ulScroll"]))
    chk("모바일: 페이지 안에 다 들어감(가로 스크롤 없음)", g["docW"] <= g["innerW"] + 1, (g["docW"], g["innerW"]))
    last_b = pg.eval_on_selector('.kid-card[data-kid=haseong] .quest:last-child',
                                 'e => e.getBoundingClientRect().bottom')
    chk("모바일: 마지막 퀘스트가 화면 안(문서 안)에 있음",
        last_b <= pg.eval_on_selector('.kid-card[data-kid=haseong]', 'e => e.getBoundingClientRect().bottom') + 1)
    pg.screenshot(path=SHOTS + "/대시보드_플로팅퀘스트_390x844.png", full_page=True)
    chk("모바일: JS 오류 0", not errs, errs[:3])
    pg.context.close()

    print("[1024×768 · 태블릿]")
    pg, errs = open_page(b, 1024, 768)
    base = pg.evaluate(GEO)
    open_kid(pg, "haseong")
    g = pg.evaluate(GEO)
    c = g["cards"]["haseong"]
    chk("태블릿: 플로팅 없이 자연 펼침", c["open"] and not c["fx"], (c["open"], c["fx"]))
    chk("태블릿: 퀘스트 10개 스크롤 없이 전부 보임", c["n"] == 10 and c["ulScroll"][0] <= c["ulScroll"][1] + 1,
        (c["n"], c["ulScroll"]))
    # 태블릿은 카드가 자연스럽게 펼쳐지며 아래 타이머·사주세요가 밀려 내려가는 게 정상이에요(문서 스크롤).
    # 왼쪽·대화방 칼럼은 그대로여야 합니다.
    colbad = []
    for grp in ("left", "right"):
        for k, a in base[grp].items():
            c = g[grp][k]
            if any(abs(c[f] - a[f]) > 0.01 for f in ("t", "b", "h", "w", "l")):
                colbad.append(k)
    chk("태블릿: 왼쪽·대화방 카드 변화 0px", not colbad, colbad)
    chk("태블릿: 세로 문서 스크롤로 퀘스트가 다 보임(가로 넘침 없음)", g["docW"] <= g["innerW"] + 1,
        (g["docW"], g["innerW"]))
    chk("태블릿: JS 오류 0", not errs, errs[:3])
    pg.context.close()

    b.close()

print()
print("실패:", len(FAIL))
for f in FAIL:
    print(" -", f)
sys.exit(1 if FAIL else 0)
