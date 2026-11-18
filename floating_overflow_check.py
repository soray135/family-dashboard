"""많은 퀘스트(20개)일 때 max-height 안전선 확인 — 카드가 화면 아래로 넘치지 않고 목록만 안에서 스크롤."""
import sys
from playwright.sync_api import sync_playwright

FILE = "file:///workspace/work-famdash/index.html"
SEED = """
(() => {
  const d = new Date();
  const today = d.getFullYear() + '-' + String(d.getMonth()+1).padStart(2,'0') + '-' + String(d.getDate()).padStart(2,'0');
  localStorage.clear();
  localStorage.setItem('sora-home-dashboard-sync-v2', JSON.stringify({off:true}));
  const mk = n => Array.from({length:n}, (_, i) => ({id:'m'+i, text:'퀘스트 ' + (i+1), xp:10, done:false}));
  localStorage.setItem('sora-home-dashboard-v1', JSON.stringify({v:1, questDate:today, kids:{
    haseong:{name:'하성이',tag:'9살',partner:'charmander',level:7,xp:128,dexOpen:[],quests:mk(20)},
    hayun:{name:'하윤이',tag:'7살',partner:'pichu',level:5,xp:72,dexOpen:[],quests:mk(5)}},
    events:{},ddays:[],wishes:[],chat:{me:'엄마',msgs:[]}}));
})();
"""
fail = []


def chk(name, cond, extra=""):
    print(("  OK   " if cond else "  FAIL ") + name + ("" if cond else f"   {extra}"))
    if not cond:
        fail.append(name)


with sync_playwright() as p:
    b = p.chromium.launch()
    for W, H in [(1600, 1000), (1366, 768), (1280, 720)]:
        ctx = b.new_context(viewport={"width": W, "height": H})
        pg = ctx.new_page()
        errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.add_init_script(SEED)
        pg.goto(FILE); pg.wait_for_timeout(1000)
        pg.click('.kid-card[data-kid=haseong] .kid-top'); pg.wait_for_timeout(700)
        out = pg.evaluate("""() => { const c = document.querySelector('.kid-card[data-kid=haseong]');
            const ul = c.querySelector('[data-quests]'); const x = c.getBoundingClientRect();
            return {bottom:+x.bottom.toFixed(1), h:+x.height.toFixed(1), innerH:innerHeight,
                    n:ul.children.length, ulH:+ul.clientHeight.toFixed(1),
                    over: ul.scrollHeight - ul.clientHeight,
                    form: !!c.querySelector('[data-qform]').getBoundingClientRect().height}; }""")
        chk(f"{W}×{H} 20개: 카드가 화면 아래로 안 넘침", out["bottom"] <= out["innerH"] - 8,
            (out["bottom"], out["innerH"]))
        chk(f"{W}×{H} 20개: 넘칠 때만 목록 안에서 스크롤", out["over"] > 0 and out["ulH"] > 80, out)
        chk(f"{W}×{H} 20개: 추가 입력창도 보임", out["form"])
        chk(f"{W}×{H} 20개: 오류 없음", not errs, errs[:2])
        ctx.close()
    b.close()
print("실패:", len(fail))
sys.exit(1 if fail else 0)
