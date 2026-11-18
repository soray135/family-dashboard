"""3칼럼 개편 검증 — ① 왼/가운데/오른쪽 3칼럼 + 아이 카드 가로 2열 ② 대화방이 남은 세로 높이를 채움
   ③ 접힘/펼침·도감·말풍선 반응·전송 회귀 ④ 1600×1000 / 1440×900 / 1024×768 / 390×844, JS 오류 0"""
import sys
from playwright.sync_api import sync_playwright

from seed_v7 import FILE, SEED
FAIL = []
def chk(name, cond, extra=""):
    print(("  OK   " if cond else "  FAIL ") + name + ("" if cond else f"   {extra}"))
    if not cond: FAIL.append(name)


GEO = r"""() => {
  const b = s => { const e = document.querySelector(s); if (!e) return null; const r = e.getBoundingClientRect();
    return {l: Math.round(r.left), r: Math.round(r.right), t: Math.round(r.top), b: Math.round(r.bottom),
            w: Math.round(r.width), h: Math.round(r.height)}; };
  const log = document.querySelector('.chat-log');
  const msgs = [...document.querySelectorAll('.chat-log .msg')];
  const lr = log.getBoundingClientRect();
  const visible = msgs.filter(m => { const r = m.getBoundingClientRect();
    return r.top >= lr.top - 1 && r.bottom <= lr.bottom + 1; }).length;
  const form = document.querySelector('.chat-form').getBoundingClientRect();
  const card = document.querySelector('.chat-card').getBoundingClientRect();
  return {
    left: b('.col-left'), center: b('.col-center'), side: b('.col-side'),
    kidsRow: b('.kids-row'), haseong: b('.kid-card[data-kid=haseong]'), hayun: b('.kid-card[data-kid=hayun]'),
    pet: b('.kid-card[data-kid=haseong] .pet'),
    chat: b('.chat-card'), chatlog: b('.chat-log'), form: b('.chat-form'),
    logToFormGap: Math.round(form.top - log.getBoundingClientRect().bottom),
    formToCardGap: Math.round(card.bottom - form.bottom),
    logFill: Math.round((lr.height / card.height) * 100),
    msgs: msgs.length, visible,
    scrollTop: Math.round(log.scrollTop), scrollH: Math.round(log.scrollHeight), clientH: Math.round(log.clientHeight),
    docW: document.documentElement.scrollWidth, innerW: innerWidth,
    docH: document.documentElement.scrollHeight, innerH: innerHeight,
    cols: getComputedStyle(document.querySelector('.grid')).gridTemplateColumns,
    overflowX: document.documentElement.scrollWidth > innerWidth + 1
  };
}"""

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

with sync_playwright() as p:
    b = p.chromium.launch()

    for W, H in [(1600, 1000), (1440, 900)]:
        print(f"[{W}×{H} · 3칼럼 데스크톱]")
        pg, errs = open_page(b, W, H)
        g = pg.evaluate(GEO)
        chk("칼럼은 왼쪽·가운데·오른쪽 3개", g["left"] and g["center"] and g["side"]
            and len(str(g["cols"]).split()) == 3, g["cols"])
        chk("왼쪽 < 가운데 < 오른쪽 가로 순서", g["left"]["r"] <= g["center"]["l"] + 1 and g["center"]["r"] <= g["side"]["l"] + 1, g)
        chk("가운데가 가장 넓음(넓게)", g["center"]["w"] > g["left"]["w"] + 60 and g["center"]["w"] > g["side"]["w"] + 60,
            (g["left"]["w"], g["center"]["w"], g["side"]["w"]))
        chk("아이 카드 두 장이 가로로 나란히", abs(g["haseong"]["t"] - g["hayun"]["t"]) <= 1 and g["haseong"]["r"] <= g["hayun"]["l"] + 1,
            (g["haseong"], g["hayun"]))
        chk("아이 카드 두 장 높이 같음", abs(g["haseong"]["h"] - g["hayun"]["h"]) <= 1)
        chk("아이 카드 컴팩트(높이 <= 270, 캐릭터 <= 110)", g["haseong"]["h"] <= 270 and g["pet"]["w"] <= 110,
            (g["haseong"]["h"], g["pet"]["w"]))
        chk("대화방은 아이 카드 바로 아래", g["chat"]["t"] >= g["kidsRow"]["b"] - 1 and g["chat"]["t"] <= g["kidsRow"]["b"] + 18,
            (g["kidsRow"]["b"], g["chat"]["t"]))
        chk("세 칼럼 바닥선 일치", abs(g["left"]["b"] - g["center"]["b"]) <= 1 and abs(g["center"]["b"] - g["side"]["b"]) <= 1,
            (g["left"]["b"], g["center"]["b"], g["side"]["b"]))
        chk("대화방이 가운데 남은 높이를 꽉 채움(>= 75%)", g["logFill"] >= 75, g["logFill"])
        chk("로그 아래·입력창 위 여백 없음(<= 8px)", g["logToFormGap"] <= 8, g["logToFormGap"])
        chk("입력창 아래 여백 없음(<= 14px)", g["formToCardGap"] <= 14, g["formToCardGap"])
        chk("대화 10개 이상 보임", g["visible"] >= (10 if H >= 1000 else 9), (g["visible"], g["msgs"]))
        chk("최신 메시지가 아래에 붙어 있음(스크롤 맨 아래)", g["scrollH"] - g["scrollTop"] - g["clientH"] <= 2,
            (g["scrollTop"], g["scrollH"], g["clientH"]))
        chk("가로 스크롤 없음", not g["overflowX"], (g["docW"], g["innerW"]))
        chk("한 화면에 들어옴(세로 스크롤 없음)", g["docH"] <= g["innerH"] + 1, (g["docH"], g["innerH"]))
        chk("기본은 접힘(퀘스트 높이 0)", pg.eval_on_selector('.kid-card[data-kid=haseong] [data-questwrap]',
            'e => Math.round(e.getBoundingClientRect().height)') == 0)
        chk("접힌 카드 aria-expanded=false", pg.get_attribute('.kid-card[data-kid=haseong] [data-qtoggle]', 'aria-expanded') == "false")
        chk("도감 버튼 보임", pg.eval_on_selector('.kid-card[data-kid=haseong] [data-dex]', 'e => e.offsetWidth > 0'))
        chk("JS 오류 0", not errs, errs[:3])

        print(f"[{W}×{H} · 카드 펼치기]")
        pg.click('.kid-card[data-kid=haseong] .kid-top'); pg.wait_for_timeout(800)
        g2 = pg.evaluate(GEO)
        chk("펼치면 퀘스트가 열림", pg.eval_on_selector('.kid-card[data-kid=haseong] [data-questwrap]',
            'e => Math.round(e.getBoundingClientRect().height)') > 150)
        chk("펼쳐도 대화방이 남아 있음(로그 >= 200px)", g2["chatlog"]["h"] >= 200, g2["chatlog"]["h"])
        chk("펼친 줄이 화면을 다 먹지 않음(<= 52%)",
            g2["kidsRow"]["h"] <= g2["center"]["h"] * 0.52 + 2, (g2["kidsRow"]["h"], g2["center"]["h"]))
        chk("펼쳐도 바닥선·한 화면 유지", abs(g2["left"]["b"] - g2["center"]["b"]) <= 1 and g2["docH"] <= g2["innerH"] + 1,
            (g2["left"]["b"], g2["center"]["b"], g2["docH"], g2["innerH"]))
        chk("퀘스트 목록은 카드 안에서 스크롤", pg.eval_on_selector('.kid-card[data-kid=haseong] [data-quests]',
            'e => e.scrollHeight > e.clientHeight + 2'))
        before = pg.inner_text('.kid-card[data-kid=haseong] [data-qprog]')
        pg.locator('.kid-card[data-kid=haseong] .quest .qcheck').nth(5).click(); pg.wait_for_timeout(350)
        after = pg.inner_text('.kid-card[data-kid=haseong] [data-qprog]')
        chk("펼친 카드에서 퀘스트 체크 동작", before != after and after.strip() == "오늘 5/10", (before, after))
        pg.click('.kid-card[data-kid=haseong] .kid-top'); pg.wait_for_timeout(700)
        chk("다시 누르면 접힘", pg.eval_on_selector('.kid-card[data-kid=haseong] [data-questwrap]',
            'e => Math.round(e.getBoundingClientRect().height)') == 0)

        print(f"[{W}×{H} · 도감·말풍선 반응·전송]")
        pg.locator('.kid-card[data-kid=hayun] [data-dex]').click(); pg.wait_for_timeout(500)
        chk("도감 모달 열림", pg.eval_on_selector_all('.dex-grid > *', 'els => els.length') > 0)
        chk("도감 모달에 종류 수 표시", pg.inner_text('#dexTitle').count('/') > 0 and pg.inner_text('#dexTitle').split('/')[-1].strip().startswith('32'),
            pg.inner_text('#dexTitle'))
        pg.keyboard.press("Escape"); pg.wait_for_timeout(400)
        chk("도감 모달 닫힘", pg.eval_on_selector_all('.modal.open', 'els => els.length') == 0)

        n_rx_before = pg.eval_on_selector_all('.msg-rx', 'els => els.length')
        pg.locator('.msg-bubble').nth(-1).click(); pg.wait_for_timeout(400)
        chk("말풍선을 누르면 반응 피커", pg.eval_on_selector('#rxPicker', 'e => !e.hidden'))
        pg.click('#rxPicker button[data-emoji="👍"]'); pg.wait_for_timeout(450)
        chk("고른 이모지가 말풍선 아래에 달림", pg.eval_on_selector_all('.msg-rx', 'els => els.length') > n_rx_before)
        chk("반응 이모지가 말풍선 아래 줄에 있음", pg.evaluate("""() => {
            const m = [...document.querySelectorAll('.chat-log .msg')].pop();
            const b = m.querySelector('.msg-bubble').getBoundingClientRect();
            const f = m.querySelector('.msg-foot') && m.querySelector('.msg-foot').getBoundingClientRect();
            return !!f && f.top >= b.bottom - 2;
        }"""))
        pg.click('body'); pg.wait_for_timeout(200)

        pg.fill('#chatInput', '엄마: 다들 준비됐지? 😊')
        pg.press('#chatInput', 'Enter'); pg.wait_for_timeout(500)
        chk("메시지 전송됨", pg.inner_text('.chat-log .msg:last-child .msg-text').strip() == '엄마: 다들 준비됐지? 😊',
            pg.inner_text('.chat-log .msg:last-child .msg-text'))
        g3 = pg.evaluate(GEO)
        chk("전송 후에도 맨 아래로 스크롤", g3["scrollH"] - g3["scrollTop"] - g3["clientH"] <= 2,
            (g3["scrollTop"], g3["scrollH"], g3["clientH"]))
        chk("JS 오류 0(상호작용 후)", not errs, errs[:3])
        pg.context.close()

    print("[1024×768 · 태블릿]")
    pg, errs = open_page(b, 1024, 768)
    g = pg.evaluate(GEO)
    chk("태블릿: 2칼럼(위 날씨|타이머, 아래 아이들+대화방)",
        g["left"]["t"] == g["side"]["t"] and g["center"]["t"] > g["left"]["b"], (g["left"], g["side"], g["center"]))
    chk("태블릿: 아이 카드 가로 2열", abs(g["haseong"]["t"] - g["hayun"]["t"]) <= 1 and g["haseong"]["r"] <= g["hayun"]["l"] + 1)
    chk("태블릿: 대화방이 아이들 아래", g["chat"]["t"] > g["kidsRow"]["b"])
    chk("태블릿: 가로 스크롤 없음", not g["overflowX"])
    chk("태블릿: JS 오류 0", not errs, errs[:3])
    pg.context.close()

    print("[390×844 · 모바일]")
    pg, errs = open_page(b, 390, 844, mobile=True)
    g = pg.evaluate(GEO)
    chk("모바일: 한 칼럼으로 쌓임", g["left"]["l"] == g["center"]["l"] == g["side"]["l"] and g["left"]["t"] < g["center"]["t"] < g["side"]["t"],
        (g["left"], g["center"], g["side"]))
    chk("모바일: 아이 카드는 위·아래로", g["haseong"]["t"] < g["hayun"]["t"] and abs(g["haseong"]["w"] - g["hayun"]["w"]) <= 1)
    chk("모바일: 카드 폭이 화면 안", g["left"]["r"] <= 390 and g["chat"]["r"] <= 390)
    chk("모바일: 가로 스크롤 없음", not g["overflowX"], (g["docW"], g["innerW"]))
    chk("모바일: 대화 로그 스크롤 영역(<= 300px)", g["chatlog"]["h"] <= 301, g["chatlog"]["h"])
    chk("모바일: 페이지 세로 스크롤 정상", g["docH"] > g["innerH"])
    chk("모바일: JS 오류 0", not errs, errs[:3])
    pg.screenshot(path="/workspace/downloads/v7_mobile_top.png")
    pg.evaluate("document.querySelector('.col-center').scrollIntoView({block:'start'})")
    pg.wait_for_timeout(400)
    pg.screenshot(path="/workspace/downloads/v7_mobile_mid.png")
    pg.context.close()

    b.close()

print()
print("실패:", len(FAIL))
for f in FAIL: print(" -", f)
sys.exit(1 if FAIL else 0)
