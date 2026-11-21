"""미리보기 스크린샷 생성 — 샘플 데이터만 넣은 깨끗한 화면(모바일 390×844 전체 화면)."""
import json
import threading
import functools
import http.server
import socketserver

from playwright.sync_api import sync_playwright

ROOT = "/workspace/work-famdash"
PORT = 8796

SEED = {
    "v": 1, "activeYear": 2026,
    "years": {"2026": {"kids": {
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
    }}},
    "meta": {"updatedAt": 0, "by": ""},
}


def main():
    socketserver.ThreadingTCPServer.allow_reuse_address = True
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=ROOT)
    httpd = socketserver.ThreadingTCPServer(("127.0.0.1", PORT), handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    base = "http://127.0.0.1:%d/" % PORT
    with sync_playwright() as p:
        b = p.chromium.launch()
        for vw, vh, dsf, tag in [(390, 844, 2, "mobile"), (1200, 900, 1, "desktop")]:
            ctx = b.new_context(viewport={"width": vw, "height": vh}, device_scale_factor=dsf)
            pg = ctx.new_page()
            pg.add_init_script("localStorage.setItem('sora-home-dashboard-sync-v2', JSON.stringify({off:true}));")
            pg.goto(base + "progress.html")
            pg.evaluate("d => localStorage.setItem('sora-progress-v1', JSON.stringify(d))", SEED)
            pg.reload()
            pg.wait_for_timeout(600)
            if tag == "mobile":
                pg.screenshot(path="/workspace/downloads/진도표_하성_탭.png", full_page=True)
            else:
                pg.screenshot(path="/workspace/work-famdash/_p_desktop.png", full_page=True)
            pg.click(".tab[data-tab=all]")
            pg.wait_for_timeout(500)
            if tag == "mobile":
                pg.screenshot(path="/workspace/downloads/진도표_함께보기_탭.png", full_page=True)
            else:
                pg.screenshot(path="/workspace/work-famdash/_p_desktop_all.png", full_page=True)
            pg.click(".tab[data-tab=hayun]")
            pg.wait_for_timeout(400)
            if tag == "mobile":
                pg.screenshot(path="/workspace/work-famdash/_p_hayun.png", full_page=True)
            else:
                pg.screenshot(path="/workspace/work-famdash/_p_desktop_hayun.png", full_page=True)
            ctx.close()
        b.close()
    httpd.shutdown()
    print("shots done")


main()
