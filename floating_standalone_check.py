"""단독 실행 파일(downloads)에서도 플로팅 확장이 동작·퀘스트가 다 보이는지 확인 (로컬 파일만)."""
import sys
from playwright.sync_api import sync_playwright

FILE = "file:///workspace/downloads/우리집_가족_대시보드.html"
SEED = """
(() => { if (localStorage.getItem('fx-standalone-seed') === '1') return;
  localStorage.clear();
  localStorage.setItem('sora-home-dashboard-sync-v2', JSON.stringify({off:true}));
  const mk = (n, pre) => Array.from({length:n}, (_, i) => ({id: pre + i, text: pre + ' 퀘스트 ' + (i+1), xp: 10, done: i < 3}));
  localStorage.setItem('sora-home-dashboard-v1', JSON.stringify({v:1, kids:{
    haseong:{name:'하성이',tag:'9살',partner:'charmander',level:7,xp:128,dexOpen:['charmander','pichu','cinnamoroll','mymelody'],quests:mk(10,'하성')},
    hayun:{name:'하윤이',tag:'7살',partner:'pichu',level:5,xp:72,dexOpen:['charmander','pichu','cinnamoroll','mymelody'],quests:mk(5,'하윤')}},
    events:{},ddays:[],wishes:[],chat:{me:'엄마',msgs:[]}}));
  localStorage.setItem('fx-standalone-seed','1');
})();
"""

fail = []


def chk(name, cond, extra=""):
    print(("  OK   " if cond else "  FAIL ") + name + ("" if cond else f"   {extra}"))
    if not cond:
        fail.append(name)


with sync_playwright() as p:
    b = p.chromium.launch()
    for W, H in [(1600, 1000), (1366, 768)]:
        ctx = b.new_context(viewport={"width": W, "height": H})
        ctx.route("**/*", lambda r: r.abort() if r.request.url.startswith("http") else r.continue_())
        pg = ctx.new_page()
        errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.add_init_script(SEED)
        pg.goto(FILE); pg.wait_for_timeout(1200)
        before = pg.evaluate("""() => { const r = s => { const x = document.querySelector(s).getBoundingClientRect();
            return [+x.top.toFixed(1), +x.left.toFixed(1), +x.width.toFixed(1), +x.height.toFixed(1)]; };
            return {timer:r('.timer-card'), chat:r('.chat-card'), left:r('.col-left')}; }""")
        pg.click('.kid-card[data-kid=haseong] .kid-top'); pg.wait_for_timeout(700)
        out = pg.evaluate("""() => { const c = document.querySelector('.kid-card[data-kid=haseong]');
            const ul = c.querySelector('[data-quests]'); const x = c.getBoundingClientRect();
            const r = s => { const y = document.querySelector(s).getBoundingClientRect();
              return [+y.top.toFixed(1), +y.left.toFixed(1), +y.width.toFixed(1), +y.height.toFixed(1)]; };
            return {fx:c.classList.contains('fx'), n:ul.children.length, over:ul.scrollHeight - ul.clientHeight,
                    card:[+x.top.toFixed(1), +x.bottom.toFixed(1), +x.height.toFixed(1)],
                    timer:r('.timer-card'), chat:r('.chat-card'), left:r('.col-left'), innerH:innerHeight}; }""")
        chk(f"{W}×{H} 단독 파일: 플로팅으로 뜸", out["fx"])
        chk(f"{W}×{H} 단독 파일: 퀘스트 10개 스크롤 없이 다 보임", out["n"] == 10 and out["over"] <= 1,
            (out["n"], out["over"]))
        chk(f"{W}×{H} 단독 파일: 왼쪽·대화방·타이머 0px", out["timer"] == before["timer"]
            and out["chat"] == before["chat"] and out["left"] == before["left"], (before, out))
        chk(f"{W}×{H} 단독 파일: 화면 아래로 안 넘침", out["card"][1] <= out["innerH"] - 8, (out["card"], out["innerH"]))
        chk(f"{W}×{H} 단독 파일: 오류 없음", not errs, errs[:2])
        ctx.close()

    b.close()
print("실패:", len(fail))
sys.exit(1 if fail else 0)
