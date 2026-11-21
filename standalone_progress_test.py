"""단독 실행 파일 검증(file://) — 대시보드의 📅 진도표 버튼이 새 창으로 진도표를 열고,
그 창에서 저장한 기록이 이 파일의 저장소에 남는지 확인합니다. (네트워크·실제 방 없음)"""
import json
from playwright.sync_api import sync_playwright

FILE = "file:///workspace/downloads/우리집_가족_대시보드.html"
out = {}
with sync_playwright() as p:
    b = p.chromium.launch()
    ctx = b.new_context(viewport={"width": 390, "height": 844}, device_scale_factor=2)
    pg = ctx.new_page()
    errs = []
    pg.on("pageerror", lambda e: errs.append("pageerror:" + str(e)))
    pg.on("console", lambda m: errs.append("console:" + m.text) if m.type == "error" else None)
    pg.add_init_script("localStorage.setItem('sora-home-dashboard-sync-v2', JSON.stringify({off:true}));")
    pg.goto(FILE)
    pg.wait_for_timeout(1500)
    if pg.locator("#gateModal.open").count():
        pg.click("#gateSkip")
        pg.wait_for_timeout(400)
    out["버튼"] = pg.eval_on_selector("#progressBtn", "e=>e.textContent.trim()")
    out["템플릿_길이"] = pg.eval_on_selector("#progressPageB64", "e=>e.textContent.trim().length")
    out["대시보드_카드"] = pg.locator(".kid-card").count()

    with ctx.expect_page() as newp:
        pg.click("#progressBtn")
    pr = newp.value
    perr = []
    pr.on("pageerror", lambda e: perr.append("pageerror:" + str(e)))
    pr.on("console", lambda m: perr.append("console:" + m.text) if m.type == "error" else None)
    pr.wait_for_load_state()
    pr.wait_for_timeout(700)
    out["새창_URL"] = pr.url
    out["새창_제목"] = pr.title()
    out["새창_탭"] = pr.locator(".tab").count()
    out["새창_과목"] = pr.eval_on_selector_all("#view-haseong .chip", "ns=>ns.map(n=>n.textContent)")
    out["새창_저장소"] = pr.evaluate("()=>{try{localStorage.setItem('__t','1');return 'ok'}catch(e){return 'fail:'+e.name}}")
    out["안내문"] = pr.locator(".local-warn").count()

    # 과정 추가 → 저장 확인
    pr.click("#view-haseong .srow:nth-of-type(2) .gcell[data-month='3']")
    pr.wait_for_selector("#itemModal.open")
    pr.fill("#itemName", "단독파일 확인")
    pr.click("#itemStatusSeg button[data-status=doing]")
    pr.click("#itemSave")
    pr.wait_for_timeout(500)
    out["추가_바"] = pr.locator("#view-haseong .bar").count()
    out["저장됨"] = pr.evaluate("()=>{const s=JSON.parse(localStorage.getItem('sora-progress-v1')||'{}');const y=(s.years||{})['2026']||{}; return (y.kids&&y.kids.haseong?y.kids.haseong.items:[]).map(i=>i.title)}")
    pr.screenshot(path="/workspace/downloads/진도표_단독파일_확인.png", full_page=True)

    # 대시보드 쪽에서도 같은 저장소를 보는지
    out["대시보드_저장소"] = pg.evaluate("()=>!!localStorage.getItem('sora-progress-v1')")
    out["오류"] = errs
    out["진도표_오류"] = perr
    ctx.close()
    b.close()
print(json.dumps(out, ensure_ascii=False, indent=2))
