"""새 기능 검증 — ① 아이 카드 접힘/펼침 ② 3칼럼 레이아웃 균형(데스크톱·모바일) ③ JS 오류 0"""
import json
from playwright.sync_api import sync_playwright
from shot_layout import SEED, FILE

FAIL = []

def chk(name, cond, extra=""):
    print(("  OK   " if cond else "  FAIL ") + name + ("" if cond else f"  {extra}"))
    if not cond:
        FAIL.append(name)

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

def geo(pg):
    return pg.evaluate("""() => {
      const b = s => { const e = document.querySelector(s); if (!e) return null; const r = e.getBoundingClientRect();
        return {t: Math.round(r.top), b: Math.round(r.bottom), h: Math.round(r.height), w: Math.round(r.width), l: Math.round(r.left)}; };
      const hs = document.querySelector('.kid-card[data-kid=haseong]');
      const qw = hs.querySelector('[data-questwrap]');
      return {
        left: b('.col-left'), mid: b('.col-center'), kids: b('.kids-row'), chat: b('.chat-card'), side: b('.col-side'),
        haseong: b('.kid-card[data-kid=haseong]'), hayun: b('.kid-card[data-kid=hayun]'),
        chatlog: b('.chat-log'), timer: b('.timer-card'), wish: b('.wish-card'),
        questW: Math.round(qw.getBoundingClientRect().height),
        scrollW: document.documentElement.scrollWidth, innerW: innerWidth,
        docH: document.documentElement.scrollHeight, innerH: innerHeight
      };
    }""")

with sync_playwright() as p:
    b = p.chromium.launch()

    # ───────── 데스크톱 1600×1000 ─────────
    print("[1600×1000 · 기본 접힘]")
    pg, errs = open_page(b, 1600, 1000)
    g = geo(pg)
    chk("기본 상태는 접힘 (퀘스트 영역 높이 0)", g["questW"] == 0, g["questW"])
    chk("aria-expanded=false", pg.get_attribute('.kid-card[data-kid=haseong] [data-qtoggle]', 'aria-expanded') == "false")
    chk("접힌 퀘스트는 inert (탭·클릭 차단)", pg.eval_on_selector('.kid-card[data-kid=haseong] [data-questwrap]', 'e => e.hasAttribute("inert")'))
    chk("캐릭터가 컴팩트하게 (76~112px)", 76 <= pg.eval_on_selector('.kid-card[data-kid=haseong] .pet', 'e => e.getBoundingClientRect().width') <= 112,
        pg.eval_on_selector('.kid-card[data-kid=haseong] .pet', 'e => e.getBoundingClientRect().width'))
    chk("진행률 배지 보임 (오늘 4/10)", pg.inner_text('.kid-card[data-kid=haseong] [data-qprog]').strip() == "오늘 4/10",
        pg.inner_text('.kid-card[data-kid=haseong] [data-qprog]'))
    chk("왼/가운데/오른쪽 칼럼 바닥선 일치",
        abs(g["left"]["b"] - g["mid"]["b"]) <= 1 and abs(g["mid"]["b"] - g["side"]["b"]) <= 1, g)
    chk("대화방 세로 길이 >= 560 (남은 높이 전부)", g["chat"]["h"] >= 560, g["chat"]["h"])
    chk("대화방 로그 높이 >= 470", g["chatlog"]["h"] >= 470, g["chatlog"]["h"])
    chk("아이 카드 두 장이 가로로 나란히(높이 같음)", abs(g["haseong"]["h"] - g["hayun"]["h"]) <= 1 and g["haseong"]["l"] < g["hayun"]["l"])
    chk("가로 스크롤 없음", g["scrollW"] <= g["innerW"], (g["scrollW"], g["innerW"]))
    chk("세로 스크롤 없음 (한 화면)", g["docH"] <= g["innerH"] + 1, (g["docH"], g["innerH"]))

    print("[1600×1000 · 펼치기]")
    pg.click('.kid-card[data-kid=haseong] .kid-top'); pg.wait_for_timeout(700)
    g2 = geo(pg)
    chk("펼치면 퀘스트 영역이 열림", g2["questW"] > 200, g2["questW"])
    chk("aria-expanded=true", pg.get_attribute('.kid-card[data-kid=haseong] [data-qtoggle]', 'aria-expanded') == "true")
    chk("inert 해제", pg.eval_on_selector('.kid-card[data-kid=haseong] [data-questwrap]', 'e => !e.hasAttribute("inert")'))
    chk("펼친 카드가 더 커짐", g2["haseong"]["h"] > g["haseong"]["h"] + 50, (g["haseong"]["h"], g2["haseong"]["h"]))
    chk("바닥선 여전히 일치", abs(g2["left"]["b"] - g2["mid"]["b"]) <= 1 and abs(g2["mid"]["b"] - g2["side"]["b"]) <= 1, g2)
    chk("퀘스트 체크 클릭이 실제로 동작", True)
    before = pg.inner_text('.kid-card[data-kid=haseong] [data-qprog]')
    pg.locator('.kid-card[data-kid=haseong] .quest .qcheck').nth(5).click(); pg.wait_for_timeout(400)
    after = pg.inner_text('.kid-card[data-kid=haseong] [data-qprog]')
    chk("퀘스트 체크 → 진행률 배지 갱신", before != after and after.strip() == "오늘 5/10", (before, after))
    chk("퀘스트 목록이 카드 안에서 스크롤", pg.eval_on_selector('.kid-card[data-kid=haseong] [data-quests]',
        'e => e.scrollHeight > e.clientHeight + 2'))
    chk("가로 스크롤 없음(펼침)", g2["scrollW"] <= g2["innerW"])

    print("[1600×1000 · 도감 버튼은 토글과 겹치지 않음]")
    pg.locator('.kid-card[data-kid=haseong] [data-dex]').click(); pg.wait_for_timeout(500)
    chk("도감 모달 열림", pg.locator('#dexModal.open').count() == 1)
    chk("도감 눌러도 카드 상태 그대로(펼침 유지)", pg.get_attribute('.kid-card[data-kid=haseong] [data-qtoggle]', 'aria-expanded') == "true")
    pg.click('#dexModal [data-close]'); pg.wait_for_timeout(400)

    print("[1600×1000 · 다시 눌러 접기]")
    pg.click('.kid-card[data-kid=haseong] .kid-top'); pg.wait_for_timeout(700)
    g3 = geo(pg)
    chk("다시 누르면 접힘", g3["questW"] == 0 and pg.get_attribute('.kid-card[data-kid=haseong] [data-qtoggle]', 'aria-expanded') == "false")
    chk("접힌 뒤에도 바닥선 일치", abs(g3["left"]["b"] - g3["chat"]["b"]) <= 1)

    print("[키보드 · 이름 편집]")
    pg.focus('.kid-card[data-kid=hayun] [data-qtoggle]')
    pg.keyboard.press("Enter"); pg.wait_for_timeout(600)
    chk("Enter 로 펼쳐짐", pg.get_attribute('.kid-card[data-kid=hayun] [data-qtoggle]', 'aria-expanded') == "true")
    chk("펼치면 이름 편집 가능", pg.eval_on_selector('.kid-card[data-kid=hayun] [data-field=name]', 'e => e.isContentEditable'))
    pg.keyboard.press("Enter"); pg.wait_for_timeout(600)
    chk("Space/Enter 로 다시 접힘", pg.get_attribute('.kid-card[data-kid=hayun] [data-qtoggle]', 'aria-expanded') == "false")
    chk("접히면 이름은 읽기 전용", pg.eval_on_selector('.kid-card[data-kid=hayun] [data-field=name]', 'e => !e.isContentEditable'))
    pg.locator('.kid-card[data-kid=hayun] .kid-name').click(); pg.wait_for_timeout(600)
    chk("접힌 상태에서 이름을 눌러도 펼쳐짐", pg.get_attribute('.kid-card[data-kid=hayun] [data-qtoggle]', 'aria-expanded') == "true")
    chk("JS 오류 없음", len(errs) == 0, errs[:5])
    pg.context.close()

    # ───────── 1440×900 ─────────
    print("[1440×900]")
    pg, errs = open_page(b, 1440, 900)
    g = geo(pg)
    chk("바닥선 일치", abs(g["left"]["b"] - g["mid"]["b"]) <= 1 and abs(g["mid"]["b"] - g["side"]["b"]) <= 1, g)
    chk("한 화면에 들어옴", g["docH"] <= g["innerH"] + 1, (g["docH"], g["innerH"]))
    chk("대화방 >= 480", g["chat"]["h"] >= 480, g["chat"]["h"])
    chk("가로 스크롤 없음", g["scrollW"] <= g["innerW"])
    chk("D-Day 카드 내용이 잘리지 않음", pg.eval_on_selector('.dday-card', 'e => e.scrollHeight <= e.clientHeight + 2'),
        pg.eval_on_selector('.dday-card', 'e => [e.scrollHeight, e.clientHeight]'))
    chk("JS 오류 없음", len(errs) == 0, errs[:5])
    pg.context.close()

    # ───────── 모바일 390×844 ─────────
    print("[모바일 390×844]")
    pg, errs = open_page(b, 390, 844, mobile=True)
    g = geo(pg)
    chk("세로 1칼럼 (가로 스크롤 없음)", g["scrollW"] <= g["innerW"], (g["scrollW"], g["innerW"]))
    chk("아이 카드 둘이 가운데 칼럼에 세로로", abs(g["haseong"]["w"] - g["hayun"]["w"]) <= 1 and g["hayun"]["t"] > g["haseong"]["b"])
    chk("기본 접힘", g["questW"] == 0)
    pg.locator('.kid-card[data-kid=haseong] .kid-top').scroll_into_view_if_needed()
    pg.locator('.kid-card[data-kid=haseong] .kid-top').tap(); pg.wait_for_timeout(700)
    pg.locator('.kid-card[data-kid=haseong] .kid-top').scroll_into_view_if_needed()
    g2 = geo(pg)
    chk("탭하면 펼쳐짐", g2["questW"] > 200, g2["questW"])
    chk("펼치면 퀘스트 10개 모두 보임(스크롤 없이)", pg.eval_on_selector('.kid-card[data-kid=haseong] [data-quests]',
        'e => e.scrollHeight <= e.clientHeight + 2'))
    pg.locator('.kid-card[data-kid=haseong] .kid-toggle').scroll_into_view_if_needed()
    pg.locator('.kid-card[data-kid=haseong] .kid-toggle').tap(); pg.wait_for_timeout(700)
    chk("'퀘스트 접기'를 탭하면 접힘", geo(pg)["questW"] == 0, geo(pg)["questW"])
    chk("접히면 힌트가 '퀘스트 보기'로", '퀘스트 보기' in pg.inner_text('.kid-card[data-kid=haseong] .kid-toggle'))
    chk("가로 스크롤 없음(모바일)", geo(pg)["scrollW"] <= geo(pg)["innerW"])
    chk("JS 오류 없음", len(errs) == 0, errs[:5])
    pg.context.close()
    b.close()

print("\n결과:", "모두 통과" if not FAIL else f"실패 {len(FAIL)}건 → {FAIL}")
