"""진도표 페이지 로컬 검증 — 실제 가족 방/라이브 URL은 절대 건드리지 않습니다.
로컬 HTTP 서버(127.0.0.1)로만 열고, 동기화는 꺼 둔 상태(로컬 모드)로 봅니다."""
import json
import threading
import functools
import http.server
import socketserver
import sys

from playwright.sync_api import sync_playwright

ROOT = "/workspace/work-famdash"
PORT = 8765

SEED = {
    "v": 1, "activeYear": 2026,
    "years": {
        "2026": {"kids": {
            "haseong": {
                "subjects": [
                    {"id": "k1", "name": "국어", "tone": "rose"},
                    {"id": "k2", "name": "독서", "tone": "peach"},
                    {"id": "k3", "name": "영어", "tone": "sky"},
                    {"id": "k4", "name": "수학1", "tone": "indigo"},
                    {"id": "k5", "name": "수학2", "tone": "violet"},
                    {"id": "k6", "name": "과학1", "tone": "teal"},
                    {"id": "k7", "name": "과학2", "tone": "mint"},
                ],
                "items": [
                    {"id": "a1", "subject": "k1", "title": "원화1", "start": 1, "end": 3, "status": "doing"},
                    {"id": "a2", "subject": "k1", "title": "원화2", "start": 4, "end": 6, "status": "planned"},
                    {"id": "a3", "subject": "k1", "title": "한자 2급", "start": 9, "end": 12, "status": "planned"},
                    {"id": "a4", "subject": "k2", "title": "책 한 권 깊게", "start": 1, "end": 12, "status": "doing"},
                    {"id": "a5", "subject": "k3", "title": "파닉스", "start": 1, "end": 2, "status": "done"},
                    {"id": "a6", "subject": "k3", "title": "리딩앤", "start": 3, "end": 11, "status": "doing"},
                    {"id": "a7", "subject": "k4", "title": "기적의 계산법 2", "start": 3, "end": 6, "status": "done"},
                    {"id": "a8", "subject": "k4", "title": "디딤돌 2-2", "start": 7, "end": 12, "status": "doing"},
                    {"id": "a9", "subject": "k5", "title": "팩토 3", "start": 7, "end": 9, "status": "planned"},
                    {"id": "a10", "subject": "k6", "title": "과학탐구", "start": 5, "end": 6, "status": "planned"},
                ],
            },
            "hayun": {
                "subjects": [
                    {"id": "y1", "name": "한글", "tone": "rose"},
                    {"id": "y2", "name": "독서", "tone": "peach"},
                    {"id": "y3", "name": "영어", "tone": "sky"},
                    {"id": "y4", "name": "수학1", "tone": "indigo"},
                    {"id": "y5", "name": "수학2", "tone": "violet"},
                    {"id": "y6", "name": "과학", "tone": "teal"},
                ],
                "items": [
                    {"id": "b1", "subject": "y1", "title": "한글 2장", "start": 1, "end": 12, "status": "doing"},
                    {"id": "b2", "subject": "y1", "title": "받아쓰기", "start": 5, "end": 8, "status": "planned"},
                    {"id": "b3", "subject": "y2", "title": "독서 기록장", "start": 2, "end": 12, "status": "doing"},
                    {"id": "b4", "subject": "y3", "title": "토도영어", "start": 1, "end": 6, "status": "done"},
                    {"id": "b5", "subject": "y4", "title": "수학 2장", "start": 3, "end": 9, "status": "doing"},
                    {"id": "b6", "subject": "y6", "title": "자연관찰", "start": 10, "end": 12, "status": "planned"},
                ],
            },
        }}
    },
    "meta": {"updatedAt": 0, "by": ""},
}


def serve():
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=ROOT)
    socketserver.TCPServer.allow_reuse_address = True
    httpd = socketserver.TCPServer(("127.0.0.1", PORT), handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd


def main():
    httpd = serve()
    out = {}
    base = "http://127.0.0.1:%d/" % PORT
    with sync_playwright() as p:
        b = p.chromium.launch()
        ctx = b.new_context(viewport={"width": 390, "height": 844}, device_scale_factor=2)
        pg = ctx.new_page()
        errs = []
        pg.on("pageerror", lambda e: errs.append("pageerror:" + str(e)))
        pg.on("console", lambda m: errs.append("console:" + m.text) if m.type == "error" else None)

        # 1) 로컬 모드, 빈 상태
        pg.add_init_script("localStorage.setItem('sora-home-dashboard-sync-v2', JSON.stringify({off:true}));")
        pg.goto(base + "progress.html")
        pg.wait_for_timeout(500)
        out["빈상태_카드수"] = pg.locator("#view-haseong .card").count()
        out["빈상태_안내"] = pg.locator("#view-haseong .empty").count()
        out["탭수"] = pg.locator(".tab").count()
        out["연도"] = pg.inner_text("#yearLabel").strip()
        out["현재월강조"] = pg.eval_on_selector_all("#view-haseong .ghead .gcell.cur span", "ns=>ns.map(n=>n.textContent)")
        out["체크"] = pg.locator("#view-haseong .gcell[data-act=cell]").count()
        pg.screenshot(path="/workspace/work-famdash/_p_empty.png", full_page=True)

        # 2) 샘플 데이터 → 하성 탭 스크린샷
        pg.evaluate("d => localStorage.setItem('sora-progress-v1', JSON.stringify(d))", SEED)
        pg.reload()
        pg.wait_for_timeout(500)
        out["샘플_바수"] = pg.locator("#view-haseong .bar").count()
        out["샘플_달성률"] = pg.inner_text("#view-haseong .rate-pct")
        out["샘플_카운트"] = pg.inner_text("#view-haseong .count-pill")
        pg.screenshot(path="/workspace/work-famdash/_p_haseong.png", full_page=True)

        # 3) 빈 칸 클릭 → 모달 자동 선택
        pg.click("#view-haseong .srow[data-subject=k5] .gcell[data-act=cell][data-month='3']")
        pg.wait_for_selector("#itemModal.open")
        out["모달_과목"] = pg.eval_on_selector("#itemSubject", "e=>e.options[e.selectedIndex].text")
        out["모달_시작"] = pg.input_value("#itemStart")
        out["모달_종료"] = pg.input_value("#itemEnd")
        out["모달_상태"] = pg.inner_text("#itemStatusSeg .on")
        pg.fill("#itemName", "초등 과학 3")
        pg.click("#itemStatusSeg button[data-status=doing]")
        pg.click("#itemSave")
        pg.wait_for_timeout(300)
        out["추가후_바수"] = pg.locator("#view-haseong .bar").count()
        out["추가후_토스트"] = pg.inner_text("#toast")

        # 4) 한눈에 보기 탭
        pg.click(".tab[data-tab=all]")
        pg.wait_for_timeout(350)
        out["함께_타일"] = pg.locator("#view-all .tile").count()
        out["함께_차트기둥"] = pg.locator("#view-all .chart .kb").count()
        out["함께_미니표"] = pg.locator("#view-all .kidblock").count()
        pg.wait_for_timeout(2600)
        pg.screenshot(path="/workspace/work-famdash/_p_all.png", full_page=True)

        # 5) 함께보기에서 상태 클릭 → 하성 탭 즉시 반영
        first = pg.locator("#view-all .kidblock[data-kid=haseong] .bar").first
        before = first.get_attribute("class")
        pg.evaluate("""() => { const b=document.querySelector("#view-all .kidblock[data-kid=haseong] .bar");
            window.__bid=b.dataset.id; window.__bt=b.title; }""")
        pg.evaluate("""() => { const id=window.__bid;
            [...document.querySelectorAll("#view-all .kidblock[data-kid=haseong] .bar")].find(x=>x.dataset.id===id).click(); }""")
        pg.wait_for_timeout(300)
        after = pg.eval_on_selector("#view-all .kidblock[data-kid=haseong] .bar", "e=>e.className")
        out["상태변경_전"] = before
        out["상태변경_후"] = after
        out["상태변경_토스트"] = pg.inner_text("#toast")
        pg.click(".tab[data-tab=haseong]")
        pg.wait_for_timeout(300)
        out["하성탭_반영"] = pg.eval_on_selector_all("#view-haseong .bar", "ns=>ns.map(n=>n.className.split(' ').find(c=>c.startsWith('st-')))")

        # 6) 과목 편집
        pg.click("#subjBtn")
        pg.wait_for_selector("#subjectModal.open")
        out["과목행수"] = pg.locator("#subjList .subj-row").count()
        pg.click("#subjAdd")
        pg.wait_for_timeout(200)
        out["과목추가후"] = pg.locator("#subjList .subj-row").count()
        pg.fill("#subjList .subj-row:last-child input[data-name]", "코딩")
        pg.wait_for_timeout(250)
        pg.click("#subjList .subj-row:last-child .swatch[data-tone=mint]")
        pg.wait_for_timeout(250)
        pg.click("#subjectModal [data-close]")
        pg.wait_for_timeout(250)
        out["과목요약_코딩"] = pg.locator("#view-haseong .subbox", has_text="코딩").count()

        # 7) 모바일 가로 넘침
        out["가로넘침"] = pg.evaluate("() => ({doc: document.documentElement.scrollWidth, win: innerWidth})")
        out["표_넘침"] = pg.evaluate("""() => [...document.querySelectorAll('.card')].filter(c=>c.scrollWidth>c.clientWidth+1).length""")

        # 8) 새로고침 후 유지
        pg.reload()
        pg.wait_for_timeout(400)
        out["저장유지_바수"] = pg.locator("#view-haseong .bar").count()

        out["오류"] = errs
        ctx.close()

        # 9) 데스크톱
        ctx2 = b.new_context(viewport={"width": 1200, "height": 900})
        pg2 = ctx2.new_page()
        e2 = []
        pg2.on("pageerror", lambda e: e2.append("pageerror:" + str(e)))
        pg2.add_init_script("localStorage.setItem('sora-home-dashboard-sync-v2', JSON.stringify({off:true}));")
        pg2.goto(base + "progress.html")
        pg2.evaluate("d => localStorage.setItem('sora-progress-v1', JSON.stringify(d))", SEED)
        pg2.reload()
        pg2.wait_for_timeout(500)
        pg2.screenshot(path="/workspace/work-famdash/_p_desktop.png", full_page=True)
        pg2.click(".tab[data-tab=all]")
        pg2.wait_for_timeout(400)
        pg2.screenshot(path="/workspace/work-famdash/_p_desktop_all.png", full_page=True)
        out["데스크톱_오류"] = e2
        out["데스크톱_넘침"] = pg2.evaluate("() => ({doc: document.documentElement.scrollWidth, win: innerWidth})")
        ctx2.close()
        b.close()
    httpd.shutdown()
    print(json.dumps(out, ensure_ascii=False, indent=2))


main()
