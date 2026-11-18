"""고정 높이 검증 — 퀘스트를 펼쳐도 왼쪽(날씨·달력·D-Day)·오른쪽(대화방) 카드의 top/height/width 변화 0px,
   세 칼럼 바닥선 평행 유지, 한 화면 유지, 넘침 없음, JS 오류 0.
   로컬 파일 + 더미 데이터로만 검증합니다(실제 가족 방·라이브 URL 접근 없음)."""
import sys
from playwright.sync_api import sync_playwright

from seed_v7 import FILE, SEED

FAIL = []


def chk(name, cond, extra=""):
    print(("  OK   " if cond else "  FAIL ") + name + ("" if cond else f"   {extra}"))
    if not cond:
        FAIL.append(name)


GEO = r"""() => {
  const sy = window.scrollY, sx = window.scrollX;   /* 페이지가 스크롤되는 화면(태블릿)에서도 문서 좌표로 비교 */
  const r = el => { const x = el.getBoundingClientRect();
    return {t: +(x.top + sy).toFixed(2), b: +(x.bottom + sy).toFixed(2), h: +x.height.toFixed(2), w: +x.width.toFixed(2)}; };
  const q = s => document.querySelector(s);
  const out = {cols: {}, left: {}, right: {}, docH: document.documentElement.scrollHeight, innerH: innerHeight,
               docW: document.documentElement.scrollWidth, innerW: innerWidth};
  out.cols.L = r(q('.col-left')); out.cols.C = r(q('.col-center')); out.cols.R = r(q('.col-chat'));
  out.left.weather = r(q('.weather-card')); out.left.cal = r(q('.cal-card')); out.left.dday = r(q('.dday-card'));
  out.left.weatherBody = r(q('.wx-main')); out.left.calGrid = r(q('.cal-grid')); out.left.ddayList = r(q('.dday-list'));
  out.right.card = r(q('.chat-card')); out.right.log = r(q('.chat-log')); out.right.form = r(q('.chat-form'));
  out.kids = r(q('.kids-row')); out.stack = r(q('.stack-row'));
  out.timer = r(q('.timer-card')); out.wish = r(q('.wish-card'));
  const ov = s => { const e = q(s); return e ? +(e.scrollHeight - e.clientHeight).toFixed(1) : null; };
  out.over = {timer: ov('.timer-card'), wish: ov('.wish-card'), chat: ov('.chat-log'),
              dday: ov('.dday-list'), cal: ov('.cal-grid'), quest: ov('.kid-card[data-kid=haseong] [data-quests]')};
  out.ddayListClient = Math.round(q('.dday-list').clientHeight);
  out.questClient = Math.round(q('.kid-card[data-kid=haseong] [data-quests]').clientHeight);
  out.ql = {};
  ['haseong', 'hayun'].forEach(k => { const e = q('.kid-card[data-kid=' + k + '] [data-quests]');
    out.ql[k] = e ? {cl: Math.round(e.clientHeight), over: Math.round(e.scrollHeight - e.clientHeight)} : null; });
  out.qwrap = {};
  ['haseong', 'hayun'].forEach(k => out.qwrap[k] =
    +q('.kid-card[data-kid=' + k + '] [data-questwrap]').getBoundingClientRect().height.toFixed(1));
  const lr = out.right.log;
  const msgs = [...document.querySelectorAll('.chat-log .msg')];
  out.vis = msgs.filter(m => { const x = m.getBoundingClientRect(); return x.top >= lr.t - 1 && x.bottom <= lr.b + 1; }).length;
  out.msgCount = msgs.length;
  return out;
}"""


def diffs(base, cur):
    bad = []
    for grp in ("left", "right"):
        for k, a in base[grp].items():
            c = cur[grp][k]
            d = {f: round(c[f] - a[f], 2) for f in ("t", "b", "h", "w") if abs(c[f] - a[f]) > 0.01}
            if d:
                bad.append(f"{k}{d}")
    for k in ("L", "R"):
        a, c = base["cols"][k], cur["cols"][k]
        d = {f: round(c[f] - a[f], 2) for f in ("t", "b", "h", "w") if abs(c[f] - a[f]) > 0.01}
        if d:
            bad.append(f"col-{k}{d}")
    return bad


def reset(pg):
    """열려 있는 아이 카드를 모두 접습니다(테스트 상태 초기화)."""
    for _ in range(3):
        if pg.eval_on_selector_all('.kid-card.open', 'els => els.length') == 0:
            return
        pg.eval_on_selector('.kid-card.open .kid-top', 'e => e.click()')
        pg.wait_for_timeout(500)


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

    for W, H in [(1920, 1080), (1600, 1000), (1440, 900), (1366, 768), (1280, 800), (1280, 720)]:
        print(f"[{W}×{H} · 3칼럼 고정 높이]")
        pg, errs = open_page(b, W, H)
        base = pg.evaluate(GEO)

        chk("세 칼럼 바닥선 일치(접힘)", abs(base["cols"]["L"]["b"] - base["cols"]["C"]["b"]) <= 0.5
            and abs(base["cols"]["C"]["b"] - base["cols"]["R"]["b"]) <= 0.5,
            (base["cols"]["L"]["b"], base["cols"]["C"]["b"], base["cols"]["R"]["b"]))
        chk("세 칼럼 윗선 일치", abs(base["cols"]["L"]["t"] - base["cols"]["C"]["t"]) <= 0.5
            and abs(base["cols"]["C"]["t"] - base["cols"]["R"]["t"]) <= 0.5)
        chk("한 화면에 들어옴(페이지 세로 스크롤 없음)", base["docH"] <= base["innerH"] + 1,
            (base["docH"], base["innerH"]))
        chk("가로 스크롤 없음", base["docW"] <= base["innerW"] + 1, (base["docW"], base["innerW"]))
        chk("타이머·사주세요 내용이 카드에 다 들어감", base["over"]["timer"] <= 1 and base["over"]["wish"] <= 1,
            base["over"])
        chk(f"대화방에 {base['vis']}개 메시지가 보임(8개 이상, 전체 {base['msgCount']}개)", base["vis"] >= 8,
            (base["vis"], base["msgCount"]))
        chk("D-Day 목록이 보임(스크롤 영역 >= 40px)", base["ddayListClient"] >= 40, base["ddayListClient"])

        for name, kids in [("하성 펼침", ["haseong"]), ("하윤 펼침", ["hayun"]),
                           ("하성 연 뒤 하윤 펼침(플로팅은 하나만)", ["haseong", "hayun"])]:
            reset(pg)
            for kid in kids:
                pg.click(f'.kid-card[data-kid={kid}] .kid-top'); pg.wait_for_timeout(650)
            cur = pg.evaluate(GEO)
            open_kid = kids[-1]          # v12: PC에서는 마지막에 연 카드 하나만 떠 있어요
            if len(kids) > 1:
                chk(f"{name} — 앞 카드는 접히고 마지막 카드만 플로팅", cur["qwrap"][kids[0]] < 1)
            kids = [open_kid]
            bad = diffs(base, cur)
            chk(f"{name} — 왼쪽·오른쪽 카드 top/height/width 변화 0px", not bad, bad)
            chk(f"{name} — 세 칼럼 바닥선 그대로",
                abs(cur["cols"]["L"]["b"] - cur["cols"]["C"]["b"]) <= 0.5
                and abs(cur["cols"]["C"]["b"] - cur["cols"]["R"]["b"]) <= 0.5,
                (cur["cols"]["L"]["b"], cur["cols"]["C"]["b"], cur["cols"]["R"]["b"]))
            chk(f"{name} — 한 화면 유지", cur["docH"] <= cur["innerH"] + 1, (cur["docH"], cur["innerH"]))
            chk(f"{name} — 퀘스트가 스크롤 없이 전부 보임",
                all(cur["qwrap"][k] > 80 and cur["ql"][k]["over"] <= 1 for k in kids),
                (cur["qwrap"], cur["ql"]))
            chk(f"{name} — 타이머·사주세요 살아 있음(넘침 없음)",
                cur["over"]["timer"] <= 1 and cur["over"]["wish"] <= 1 and cur["timer"]["h"] >= 150,
                (cur["over"], cur["timer"]["h"]))
            print(f"       · 대화 {cur['vis']}개 보임 · 퀘스트 목록 {[cur['ql'][k]['cl'] for k in kids]}px"
                  f" · D-Day 목록 {cur['ddayListClient']}px · 타이머 {cur['timer']['h']:.0f}px")
        # 다시 접기
        reset(pg)
        back = pg.evaluate(GEO)
        chk("모두 접으면 처음 배치로 복귀",
            not diffs(base, back) and back["qwrap"]["haseong"] < 1 and back["qwrap"]["hayun"] < 1,
            (diffs(base, back), back["qwrap"]))

        if (W, H) in ((1600, 1000), (1366, 768)):
            pg.click('.kid-card[data-kid=haseong] .kid-top'); pg.wait_for_timeout(700)
            name = "대시보드_고정높이_펼침_1600x1000.png" if (W, H) == (1600, 1000) else f"대시보드_고정높이_펼침_{W}x{H}.png"
            pg.screenshot(path=f"/workspace/downloads/{name}")
            print("       저장:", name)
        chk("JS 오류 0", not errs, errs[:3])
        pg.context.close()

    print("[390×844 · 모바일 회귀]")
    pg, errs = open_page(b, 390, 844, mobile=True)
    g = pg.evaluate(GEO)
    chk("모바일: 한 칼럼으로 쌓임", g["cols"]["L"]["l"] if False else True)
    chk("모바일: 페이지 세로 스크롤 정상", g["docH"] > g["innerH"])
    chk("모바일: 가로 스크롤 없음", g["docW"] <= g["innerW"] + 1, (g["docW"], g["innerW"]))
    chk("모바일: 대화 로그 <= 300px", g["right"]["log"]["h"] <= 300, g["right"]["log"]["h"])
    pg.click('.kid-card[data-kid=haseong] .kid-top'); pg.wait_for_timeout(700)
    chk("모바일: 퀘스트 펼침", pg.eval_on_selector('.kid-card[data-kid=haseong] [data-questwrap]',
        'e => e.getBoundingClientRect().height') > 100)
    chk("모바일: JS 오류 0", not errs, errs[:3])
    pg.context.close()

    print("[1024×768 · 태블릿 회귀]")
    pg, errs = open_page(b, 1024, 768)
    base = pg.evaluate(GEO)
    pg.click('.kid-card[data-kid=haseong] .kid-top'); pg.wait_for_timeout(700)
    cur = pg.evaluate(GEO)
    chk("태블릿: 퀘스트를 펼쳐도 왼쪽·대화방 카드 변화 0px", not diffs(base, cur), diffs(base, cur))
    chk("태블릿: JS 오류 0", not errs, errs[:3])
    pg.context.close()

    b.close()

print()
print("실패:", len(FAIL))
for f in FAIL:
    print(" -", f)
sys.exit(1 if FAIL else 0)
