"""가족 방 동기화 경로 검증 — 실제 Firebase/실제 방은 쓰지 않습니다.
127.0.0.1 에 가짜 Firebase REST 서버(더미 방 'testroom')를 띄워
  · 대시보드(index.html)가 방 전체를 PUT 할 때 progress 가 지워지지 않는지
  · 진도표(progress.html)가 /rooms/{room}/progress 만 읽고 쓰는지
만 확인합니다.
"""
import json
import threading
import functools
import http.server
import socketserver

from playwright.sync_api import sync_playwright

ROOT = "/workspace/work-famdash"
WEB = 8771
DB = 8772

STATE = {
    "room": {},              # /rooms/testroom
    "puts": [],               # (path, body) 기록
}
PROGRESS_SEED = {
    "v": 1,
    "years": {
        "2026": {"kids": {
            "haseong": {
                "subjects": [{"id": "k1", "name": "국어", "tone": "rose"}],
                "items": [{"id": "x1", "subject": "k1", "title": "서버에서 온 과정", "start": 2, "end": 5, "status": "doing"}],
            },
            "hayun": {
                "subjects": [{"id": "y1", "name": "한글", "tone": "rose"}],
                "items": [{"id": "z1", "subject": "y1", "title": "하윤 과정", "start": 1, "end": 3, "status": "done"}],
            },
        }}
    },
    "meta": {"updatedAt": 1000, "by": "other-device"},
}


class DbHandler(http.server.BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, *a):
        pass

    def _log(self, extra=""):
        print("DB", self.command, self.path, extra, flush=True)

    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, PUT, PATCH, POST, OPTIONS")

    def _json(self, code, obj):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self._cors()
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self._log()
        self.send_response(204)
        self._cors()
        self.send_header("Content-Length", "0")
        self.end_headers()

    def do_GET(self):
        path = self.path.split("?")[0]
        if "text/event-stream" in (self.headers.get("Accept") or ""):
            self.send_response(200)
            self._cors()
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            try:
                payload = STATE["room"].get("progress") if path.endswith("/progress.json") else STATE["room"]
                self.wfile.write(('event: put\ndata: ' + json.dumps({"path": "/", "data": payload}) + '\n\n').encode())
                self.wfile.flush()
            except Exception:
                pass
            return
        if path == "/rooms/testroom.json":
            return self._json(200, STATE["room"])
        if path == "/rooms/testroom/progress.json":
            _p = STATE["room"].get("progress")
            print("DEBUG_PROGRESS_GET", json.dumps(_p, ensure_ascii=False)[:150], flush=True)
            return self._json(200, _p)
        if path.startswith("/rooms/testroom/"):
            key = path[len("/rooms/testroom/"):].replace(".json", "")
            return self._json(200, STATE["room"].get(key))
        return self._json(200, None)

    def do_PUT(self):
        path = self.path.split("?")[0]
        self._log()
        n = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(n) if n else b""
        try:
            body = json.loads(raw or b"null")
        except Exception:
            body = None
        STATE["puts"].append({"path": path, "body": body})
        if path == "/rooms/testroom.json":
            STATE["room"] = body or {}
        elif path == "/rooms/testroom/progress.json":
            STATE["room"]["progress"] = body
        return self._json(200, body)

    def do_PATCH(self):
        return self.do_PUT()


def serve(port, handler):
    socketserver.ThreadingTCPServer.allow_reuse_address = True
    socketserver.ThreadingTCPServer.daemon_threads = True
    httpd = socketserver.ThreadingTCPServer(("127.0.0.1", port), handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd


def main():
    STATE["room"] = {
        "v": 1, "title": "우리가족 대시보드",
        "kids": {"haseong": {"name": "하성", "xp": 10, "quests": []}, "hayun": {"name": "하윤", "xp": 0, "quests": []}},
        "events": {}, "ddays": [], "wishes": [], "chat": {"me": "엄마", "msgs": {}},
        "progress": json.loads(json.dumps(PROGRESS_SEED)),
        "meta": {"updatedAt": 5000, "by": "other-device"},
    }
    web = serve(WEB, functools.partial(http.server.SimpleHTTPRequestHandler, directory=ROOT))
    db = serve(DB, DbHandler)
    out = {}
    cfg = json.dumps({"url": "http://127.0.0.1:%d" % DB, "room": "testroom"})
    with sync_playwright() as p:
        b = p.chromium.launch()
        ctx = b.new_context(viewport={"width": 390, "height": 844})
        pg = ctx.new_page()
        errs = []
        pg.on("pageerror", lambda e: errs.append("pageerror:" + str(e)))
        pg.on("console", lambda m: errs.append("console:" + m.text) if m.type == "error" else None)
        pg.add_init_script("localStorage.setItem('sora-home-dashboard-sync-v2', %s);" % json.dumps(cfg))
        ctx.add_init_script("""
          window.__FETCH = [];
          const of = window.fetch;
          window.fetch = async function(u, o) {
            const rec = { url: String(u), method: (o && o.method) || 'GET' };
            window.__FETCH.push(rec);
            try { const r = await of(u, o); rec.status = r.status; return r; }
            catch (e) { rec.err = String(e); throw e; }
          };
        """)

        # ── 대시보드: 방 문서 PUT 에 progress 가 남아 있는지 ──
        pg.goto("http://127.0.0.1:%d/index.html" % WEB)
        pg.wait_for_timeout(2500)
        out["대시보드_연결"] = pg.inner_text("#syncLabel")
        out["진도표버튼"] = pg.eval_on_selector("#progressBtn", "e=>({text:e.textContent.trim(), href:e.getAttribute('href'), target:e.getAttribute('target')})")
        # 퀘스트를 체크해 저장을 일으킨다
        pg.evaluate("() => { state.title = '우리가족 대시보드'; save(); }")
        pg.wait_for_timeout(1500)
        room_puts = [x for x in STATE["puts"] if x["path"] == "/rooms/testroom.json"]
        out["방PUT_수"] = len(room_puts)
        out["방PUT_progress보존"] = bool(room_puts and isinstance(room_puts[-1]["body"], dict) and room_puts[-1]["body"].get("progress"))
        out["방PUT_progress값"] = (room_puts[-1]["body"].get("progress") or {}).get("years", {}).get("2026", {}).get("kids", {}).get("haseong", {}).get("items") if room_puts else None
        out["방PUT_키"] = sorted((room_puts[-1]["body"] or {}).keys()) if room_puts else None

        # ── 진도표: 서버 값을 읽어 오는지 ──
        pg2 = ctx.new_page()
        e2 = []
        pg2.on("pageerror", lambda e: e2.append("pageerror:" + str(e)))
        pg2.on("console", lambda m: e2.append("console:" + m.text) if m.type == "error" else None)
        pg2.goto("http://127.0.0.1:%d/progress.html" % WEB)
        pg2.wait_for_timeout(2000)
        out["진도표_연결"] = pg2.inner_text("#syncText")
        out["진도표_서버값"] = pg2.eval_on_selector_all("#view-haseong .bar .bt", "ns=>ns.map(n=>n.textContent)")
        out["진도표_서버pct"] = pg2.inner_text("#view-haseong .rate-pct")

        # 서버 값이 화면에 있으면 진도 추가 → progress leaf 로만 PUT 되는지
        print("DEBUG_LOAD", pg2.evaluate("()=>document.querySelectorAll('#view-hayun .srow').length"), pg2.evaluate("()=>[...document.querySelectorAll('#view-hayun .chip')].map(c=>c.textContent)"), pg2.inner_text("#syncText"), flush=True)
        print("DEBUG_FETCH", pg2.evaluate("()=>window.__FETCH"), flush=True)
        print("DEBUG_LS", pg2.evaluate("()=>localStorage.getItem('sora-progress-v1')?.slice(0,120)"), flush=True)
        out["디버그_로드후"] = pg2.evaluate("()=>{const s=JSON.parse(localStorage.getItem('sora-progress-v1')||'{}');const y=(s.years||{})['2026'];return y? Object.fromEntries(Object.entries(y.kids).map(([k,v])=>[k,v.subjects.map(x=>x.id+':'+x.name)])) : null}")
        out["디버그_로드후_초기fetch"] = pg2.evaluate("()=>window.__FETCH")
        pg2.click(".tab[data-tab=hayun]")
        pg2.wait_for_timeout(200)
        pg2.click("#view-hayun .srow[data-subject=y1] .gcell[data-month='7']")
        pg2.wait_for_selector("#itemModal.open")
        pg2.fill("#itemName", "서버 동기화 확인용")
        out["디버그_모달"] = pg2.locator("#itemModal.open").count()
        out["디버그_과목옵션"] = pg2.eval_on_selector("#itemSubject", "e=>[e.value,[...e.options].map(o=>o.value)]")
        pg2.click("#itemSave")
        pg2.wait_for_timeout(1500)
        out["디버그_저장후"] = pg2.evaluate("()=>{const s=JSON.parse(localStorage.getItem('sora-progress-v1')||'{}');return (s.years&&s.years['2026'].kids.hayun.items||[]).map(i=>i.title)}")
        out["디버그_바"] = pg2.locator("#view-hayun .bar").count()
        out["디버그_SYNC"] = pg2.evaluate("()=>window.__PD && window.__PD()")
        out["디버그_FETCH"] = pg2.evaluate("()=>window.__FETCH")
        prog_puts = [x for x in STATE["puts"] if x["path"] == "/rooms/testroom/progress.json"]
        out["진도표PUT_수"] = len(prog_puts)
        out["진도표PUT_경로들"] = sorted(set(x["path"] for x in STATE["puts"]))
        body = prog_puts[-1]["body"] if prog_puts else None
        out["진도표PUT_하윤항목"] = [i["title"] for i in (body or {}).get("years", {}).get("2026", {}).get("kids", {}).get("hayun", {}).get("items", [])]
        out["진도표_쓰기후_pill"] = pg2.inner_text("#syncText")
        # 방 전체 문서가 다시 PUT 되면서 진도가 지워지지 않았는지
        out["서버_progress_하윤"] = [i["title"] for i in STATE["room"].get("progress", {}).get("years", {}).get("2026", {}).get("kids", {}).get("hayun", {}).get("items", [])]
        out["오류"] = errs
        out["진도표_오류"] = e2
        ctx.close()
        b.close()
    web.shutdown()
    db.shutdown()
    print(json.dumps(out, ensure_ascii=False, indent=2))


main()
