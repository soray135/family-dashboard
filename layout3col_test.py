"""3칼럼 배치 검증 — ① 왼쪽(날씨·달력·D-Day) · 가운데(아이 둘 위 / 타이머·사주세요 아래) · 오른쪽(대화방)
   ② 대화방이 오른쪽 칼럼 세로를 꽉 채움 ③ 좁은 폭에서 타이머·사주세요·대화방 도구가 카드 밖으로 넘치지 않음
   ④ 접힘/펼침·도감·말풍선 반응·전송 회귀 ⑤ 1600×1000 / 1440×900 / 1024×768 / 390×844, JS 오류 0"""
import sys
from playwright.sync_api import sync_playwright

from seed_v7 import FILE, SEED

FAIL = []


def chk(name, cond, extra=""):
    print(("  OK   " if cond else "  FAIL ") + name + ("" if cond else f"   {extra}"))
    if not cond:
        FAIL.append(name)


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
  const chips = [...document.querySelectorAll('#whoPick .who-chip')].map(e => Math.round(e.getBoundingClientRect().top));
  const rx = [...document.querySelectorAll('#reactionRow .re-btn')].map(e => Math.round(e.getBoundingClientRect().top));
  const inside = (sel) => {          // 카드 밖으로 삐져나온 자식이 있는지
    const c = document.querySelector(sel); if (!c) return ['no-card'];
    const cr = c.getBoundingClientRect(); const bad = [];
    c.querySelectorAll('*').forEach(ch => { const r = ch.getBoundingClientRect();
      if (r.width && (r.right > cr.right + 1.5 || r.left < cr.left - 1.5)) bad.push(ch.tagName + '.' + (ch.className || ch.id)); });
    return {out: bad.slice(0, 4), scroll: c.scrollWidth - c.clientWidth};
  };
  return {
    left: b('.col-left'), center: b('.col-center'), chatCol: b('.col-chat'),
    kidsRow: b('.kids-row'), stack: b('.stack-row'),
    haseong: b('.kid-card[data-kid=haseong]'), hayun: b('.kid-card[data-kid=hayun]'),
    pet: b('.kid-card[data-kid=haseong] .pet'), timer: b('.timer-card'), wish: b('.wish-card'),
    chat: b('.chat-card'), chatlog: b('.chat-log'), form: b('.chat-form'),
    logToFormGap: Math.round(form.top - lr.bottom),
    formToCardGap: Math.round(card.bottom - form.bottom),
    logFill: Math.round((lr.height / card.height) * 100),
    msgs: msgs.length, visible,
    scrollTop: Math.round(log.scrollTop), scrollH: Math.round(log.scrollHeight), clientH: Math.round(log.clientHeight),
    chips, rx, timerInside: inside('.timer-card'), wishInside: inside('.wish-card'), chatInside: inside('.chat-card'),
    docW: document.documentElement.scrollWidth, innerW: innerWidth,
    docH: document.documentElement.scrollHeight, innerH: innerHeight,
    cols: getComputedStyle(document.querySelector('.grid')).gridTemplateColumns,
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


def no_overflow(g, key, label):
    bad = g[key]
    chk(label, isinstance(bad, dict) and not bad["out"] and bad["scroll"] <= 1 and True, bad)


with sync_playwright() as p:
    b = p.chromium.launch()

    for W, H in [(1600, 1000), (1440, 900)]:
        print(f"[{W}×{H} · 3칼럼]")
        pg, errs = open_page(b, W, H)
        g = pg.evaluate(GEO)

        chk("칼럼 3개(왼쪽·가운데·오른쪽)", g["left"] and g["center"] and g["chatCol"]
            and len(str(g["cols"]).split()) == 3, g["cols"])
        chk("왼쪽 < 가운데 < 오른쪽 가로 순서",
            g["left"]["r"] <= g["center"]["l"] + 1 and g["center"]["r"] <= g["chatCol"]["l"] + 1, g)
        chk("오른쪽 대화방 칼럼 폭 360~420px", 360 <= g["chatCol"]["w"] <= 420, g["chatCol"]["w"])
        chk("가운데가 가장 넓음", g["center"]["w"] > g["left"]["w"] + 40 and g["center"]["w"] > g["chatCol"]["w"] + 40,
            (g["left"]["w"], g["center"]["w"], g["chatCol"]["w"]))

        chk("아이 카드 두 장이 가로로 나란히", abs(g["haseong"]["t"] - g["hayun"]["t"]) <= 1
            and g["haseong"]["r"] <= g["hayun"]["l"] + 1, (g["haseong"], g["hayun"]))
        chk("아이 카드 두 장 높이 같음", abs(g["haseong"]["h"] - g["hayun"]["h"]) <= 1)
        chk("아이 카드 컴팩트(높이 <= 270, 캐릭터 <= 110)", g["haseong"]["h"] <= 270 and g["pet"]["w"] <= 110,
            (g["haseong"]["h"], g["pet"]["w"]))

        chk("타이머·사주세요는 아이들 바로 아래", g["stack"]["t"] >= g["kidsRow"]["b"] - 1
            and g["stack"]["t"] <= g["kidsRow"]["b"] + 18, (g["kidsRow"]["b"], g["stack"]["t"]))
        chk("타이머(왼쪽) | 사주세요(오른쪽) 나란히", abs(g["timer"]["t"] - g["wish"]["t"]) <= 1
            and abs(g["timer"]["b"] - g["wish"]["b"]) <= 1 and g["timer"]["r"] <= g["wish"]["l"] + 1,
            (g["timer"], g["wish"]))
        chk("타이머·사주세요 가운데 칼럼 폭을 반씩", abs(g["timer"]["w"] - g["wish"]["w"]) <= 2,
            (g["timer"]["w"], g["wish"]["w"]))

        chk("세 칼럼 바닥선 일치", abs(g["left"]["b"] - g["center"]["b"]) <= 1
            and abs(g["center"]["b"] - g["chatCol"]["b"]) <= 1, (g["left"]["b"], g["center"]["b"], g["chatCol"]["b"]))
        chk("대화방이 오른쪽 칼럼 세로를 꽉 채움(>= 700px, 칼럼 높이와 같음)",
            g["chat"]["h"] == g["chatCol"]["h"] and g["chat"]["h"] >= 700, (g["chat"], g["chatCol"]))
        chk("대화 로그가 카드의 75% 이상", g["logFill"] >= 75, g["logFill"])
        chk("로그 아래·입력창 위 여백 없음(<= 8px)", g["logToFormGap"] <= 8, g["logToFormGap"])
        chk("입력창 아래 여백 없음(<= 14px)", g["formToCardGap"] <= 14, g["formToCardGap"])
        chk("대화 10개 이상 보임", g["visible"] >= (10 if H >= 1000 else 9), (g["visible"], g["msgs"]))
        chk("최신 메시지가 아래에 붙어 있음(맨 아래로 스크롤)",
            g["scrollH"] - g["scrollTop"] - g["clientH"] <= 2, (g["scrollTop"], g["scrollH"], g["clientH"]))
        chk("보낸 사람 칩 네 개는 한 줄", len(set(g["chips"])) == 1 and len(g["chips"]) == 4, g["chips"])
        chk("빠른 반응은 칩 아래 줄에(넘치지 않음)", len(set(g["rx"])) == 1 and g["rx"][0] > g["chips"][0], (g["chips"], g["rx"]))
        no_overflow(g, "chatInside", "대화방 도구가 카드 밖으로 넘치지 않음")
        no_overflow(g, "timerInside", "타이머 조작부가 카드 밖으로 넘치지 않음")
        no_overflow(g, "wishInside", "사주세요 입력줄이 카드 밖으로 넘치지 않음")
        chk("타이머 숫자가 크게 보임(>= 44px)",
            pg.eval_on_selector('#timerDisplay', 'e => parseFloat(getComputedStyle(e).fontSize)') >= 44,
            pg.eval_on_selector('#timerDisplay', 'e => getComputedStyle(e).fontSize'))
        chk("가로 스크롤 없음", not (g["docW"] > g["innerW"] + 1), (g["docW"], g["innerW"]))
        chk("한 화면에 들어옴(세로 스크롤 없음)", g["docH"] <= g["innerH"] + 1, (g["docH"], g["innerH"]))
        chk("기본은 접힘(퀘스트 높이 0)", pg.eval_on_selector('.kid-card[data-kid=haseong] [data-questwrap]',
            'e => Math.round(e.getBoundingClientRect().height)') == 0)
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
        chk("펼쳐도 타이머·사주세요가 살아 있음(>= 340px)",
            g2["timer"]["h"] >= 340 and g2["wish"]["h"] >= 340, (g2["timer"]["h"], g2["wish"]["h"]))
        chk("펼쳐도 바닥선·한 화면 유지", abs(g2["left"]["b"] - g2["center"]["b"]) <= 1
            and g2["docH"] <= g2["innerH"] + 1, (g2["left"]["b"], g2["center"]["b"], g2["docH"], g2["innerH"]))
        chk("퀘스트 목록은 카드 안에서 스크롤", pg.eval_on_selector('.kid-card[data-kid=haseong] [data-quests]',
            'e => e.scrollHeight > e.clientHeight + 2'))
        before = pg.inner_text('.kid-card[data-kid=haseong] [data-qprog]')
        pg.locator('.kid-card[data-kid=haseong] .quest .qcheck').nth(5).click(); pg.wait_for_timeout(350)
        after = pg.inner_text('.kid-card[data-kid=haseong] [data-qprog]')
        chk("펼친 카드에서 퀘스트 체크 동작", before != after and after.strip() == "오늘 5/10", (before, after))
        pg.click('.kid-card[data-kid=haseong] .kid-top'); pg.wait_for_timeout(700)
        chk("다시 누르면 접힘", pg.eval_on_selector('.kid-card[data-kid=haseong] [data-questwrap]',
            'e => Math.round(e.getBoundingClientRect().height)') == 0)

        print(f"[{W}×{H} · 도감·말풍선 반응·전송·타이머·사주세요]")
        pg.locator('.kid-card[data-kid=hayun] [data-dex]').click(); pg.wait_for_timeout(500)
        chk("도감 모달 열림", pg.eval_on_selector_all('.dex-grid > *', 'els => els.length') > 0)
        chk("도감 모달에 종류 수 표시", pg.inner_text('#dexTitle').count('/') > 0
            and pg.inner_text('#dexTitle').split('/')[-1].strip().startswith('32'), pg.inner_text('#dexTitle'))
        pg.keyboard.press("Escape"); pg.wait_for_timeout(400)
        chk("도감 모달 닫힘", pg.eval_on_selector_all('.modal.open', 'els => els.length') == 0)

        n_rx_before = pg.eval_on_selector_all('.msg-rx', 'els => els.length')
        pg.locator('.msg-bubble').nth(-1).click(); pg.wait_for_timeout(400)
        chk("말풍선을 누르면 반응 피커", pg.eval_on_selector('#rxPicker', 'e => !e.hidden'))
        pg.click('#rxPicker button[data-emoji="👍"]'); pg.wait_for_timeout(450)
        chk("고른 이모지가 말풍선 아래에 달림", pg.eval_on_selector_all('.msg-rx', 'els => els.length') > n_rx_before)
        pg.click('body'); pg.wait_for_timeout(200)

        pg.fill('#chatInput', '엄마: 다들 준비됐지? 😊')
        pg.press('#chatInput', 'Enter'); pg.wait_for_timeout(500)
        chk("메시지 전송됨", pg.inner_text('.chat-log .msg:last-child .msg-text').strip() == '엄마: 다들 준비됐지? 😊',
            pg.inner_text('.chat-log .msg:last-child .msg-text'))
        g3 = pg.evaluate(GEO)
        chk("전송 후에도 맨 아래로 스크롤", g3["scrollH"] - g3["scrollTop"] - g3["clientH"] <= 2,
            (g3["scrollTop"], g3["scrollH"], g3["clientH"]))

        pg.click('#timerQuick button[data-min="5"]'); pg.wait_for_timeout(250)
        chk("타이머 5분 선택 표시", pg.inner_text('#timerDisplay').strip() == "05:00", pg.inner_text('#timerDisplay'))
        pg.click('#timerStart'); pg.wait_for_timeout(1200)
        chk("타이머 시작(숫자 줄어듦)", pg.inner_text('#timerDisplay').strip() != "05:00", pg.inner_text('#timerDisplay'))
        pg.click('#timerReset'); pg.wait_for_timeout(250)
        pg.click('.ttab[data-tmode=stopwatch]'); pg.wait_for_timeout(300)
        chk("스톱워치 탭 전환", pg.eval_on_selector('#swPane', 'e => !e.hidden'))
        pg.click('#swStart'); pg.wait_for_timeout(900)
        chk("스톱워치 작동", pg.inner_text('#swDisplay').strip() != "00:00.00", pg.inner_text('#swDisplay'))
        chk("스톱워치 숫자가 카드 안에 한 줄로", pg.eval_on_selector('#swDisplay', """e => {
            const p = e.closest('.timer-card').getBoundingClientRect(); const r = e.getBoundingClientRect();
            return r.width > 0 && r.left >= p.left && r.right <= p.right; }"""))
        pg.click('#swReset'); pg.wait_for_timeout(200)
        pg.click('.ttab[data-tmode=timer]'); pg.wait_for_timeout(250)

        n_wish = pg.eval_on_selector_all('.wish', 'els => els.length')
        pg.fill('#wishName', '새 학기 가방')
        pg.click('#wishAdd'); pg.wait_for_timeout(400)
        chk("사주세요 항목 추가", pg.eval_on_selector_all('.wish', 'els => els.length') == n_wish + 1)
        chk("추가한 항목이 목록에 보임", '새 학기 가방' in pg.inner_text('.wish-list'))
        g4 = pg.evaluate(GEO)
        no_overflow(g4, "wishInside", "항목이 늘어도 사주세요 카드 안(스크롤)")
        chk("JS 오류 0(상호작용 후)", not errs, errs[:3])
        pg.context.close()

    print("[1024×768 · 태블릿]")
    pg, errs = open_page(b, 1024, 768)
    g = pg.evaluate(GEO)
    chk("태블릿: 위 날씨·달력·D-Day | 대화방", g["left"]["t"] == g["chatCol"]["t"]
        and g["chatCol"]["l"] > g["left"]["r"], (g["left"], g["chatCol"]))
    chk("태블릿: 대화방이 왼쪽 칼럼과 같은 높이", abs(g["chatCol"]["b"] - g["left"]["b"]) <= 1,
        (g["left"]["b"], g["chatCol"]["b"]))
    chk("태블릿: 아이 카드 두 장 가로 2열(전체 폭)", abs(g["haseong"]["t"] - g["hayun"]["t"]) <= 1
        and abs(g["haseong"]["w"] - g["hayun"]["w"]) <= 1 and g["kidsRow"]["w"] > g["left"]["w"], g["kidsRow"])
    chk("태블릿: 타이머 | 사주세요는 아이들 아래", g["timer"]["t"] > g["kidsRow"]["b"]
        and abs(g["timer"]["t"] - g["wish"]["t"]) <= 1 and g["timer"]["r"] <= g["wish"]["l"] + 1,
        (g["kidsRow"]["b"], g["timer"], g["wish"]))
    no_overflow(g, "wishInside", "태블릿: 사주세요 입력줄이 카드 안")
    no_overflow(g, "timerInside", "태블릿: 타이머 조작부가 카드 안")
    no_overflow(g, "chatInside", "태블릿: 대화방 도구가 카드 안")
    chk("태블릿: 가로 스크롤 없음", not (g["docW"] > g["innerW"] + 1), (g["docW"], g["innerW"]))
    chk("태블릿: 대화 로그가 넉넉함(>= 400px)", g["chatlog"]["h"] >= 400, g["chatlog"]["h"])
    chk("태블릿: JS 오류 0", not errs, errs[:3])
    pg.screenshot(path="/workspace/downloads/layout_1024.png", full_page=True)
    pg.context.close()

    print("[390×844 · 모바일]")
    pg, errs = open_page(b, 390, 844, mobile=True)
    g = pg.evaluate(GEO)
    chk("모바일: 한 칼럼으로 쌓임(날씨 → 아이들 → 대화방 → 타이머·사주세요)",
        g["left"]["l"] == g["kidsRow"]["l"] == g["chatCol"]["l"] == g["stack"]["l"]
        and g["left"]["t"] < g["kidsRow"]["t"] < g["chatCol"]["t"] < g["stack"]["t"],
        (g["left"], g["kidsRow"], g["chatCol"], g["stack"]))
    chk("모바일: 아이 카드는 위·아래로", g["haseong"]["t"] < g["hayun"]["t"]
        and abs(g["haseong"]["w"] - g["hayun"]["w"]) <= 1)
    chk("모바일: 타이머·사주세요도 위·아래로", g["timer"]["t"] < g["wish"]["t"]
        and abs(g["timer"]["w"] - g["wish"]["w"]) <= 1)
    chk("모바일: 카드 폭이 화면 안", g["left"]["r"] <= 390 and g["chat"]["r"] <= 390 and g["wish"]["r"] <= 390,
        (g["left"]["r"], g["chat"]["r"], g["wish"]["r"]))
    chk("모바일: 가로 스크롤 없음", not (g["docW"] > g["innerW"] + 1), (g["docW"], g["innerW"]))
    no_overflow(g, "wishInside", "모바일: 사주세요 입력줄이 카드 안")
    no_overflow(g, "timerInside", "모바일: 타이머 조작부가 카드 안")
    no_overflow(g, "chatInside", "모바일: 대화방 도구가 카드 안")
    chk("모바일: 대화 로그 스크롤 영역(<= 300px)", g["chatlog"]["h"] <= 300, g["chatlog"]["h"])
    chk("모바일: 페이지 세로 스크롤 정상", g["docH"] > g["innerH"])
    chk("모바일: JS 오류 0", not errs, errs[:3])
    pg.screenshot(path="/workspace/downloads/layout_390.png")
    pg.evaluate("document.querySelector('.col-chat').scrollIntoView({block:'start'})")
    pg.wait_for_timeout(400)
    pg.screenshot(path="/workspace/downloads/layout_390_chat.png")
    pg.evaluate("document.querySelector('.stack-row').scrollIntoView({block:'start'})")
    pg.wait_for_timeout(400)
    pg.screenshot(path="/workspace/downloads/layout_390_stack.png")
    pg.context.close()

    b.close()

print()
print("실패:", len(FAIL))
for f in FAIL:
    print(" -", f)
sys.exit(1 if FAIL else 0)
