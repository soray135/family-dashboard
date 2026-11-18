from playwright.sync_api import sync_playwright
from seed_v7 import FILE, SEED

with sync_playwright() as p:
    b = p.chromium.launch()
    for W, H in [(1366, 768), (1280, 800)]:
        pg = b.new_page(viewport={"width": W, "height": H})
        pg.goto(FILE); pg.wait_for_timeout(300)
        pg.evaluate(SEED); pg.reload(); pg.wait_for_timeout(1200)
        pg.click('.kid-card[data-kid=haseong] .kid-top'); pg.wait_for_timeout(800)
        pg.screenshot(path=f"/workspace/downloads/대시보드_플로팅퀘스트_{W}x{H}.png")
        pg.close()
    b.close()
