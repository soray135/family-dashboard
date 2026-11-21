"""레벨업 선물상자 미리보기 — 로컬 파일 + 더미 데이터만 사용 (실제 가족 방·라이브 URL 접속 없음).

1) 선물상자 도착 화면  2) 상자를 열어 새 친구 소개가 뜬 화면
"""
from playwright.sync_api import sync_playwright

FILE = "file:///workspace/work-famdash/index.html"

SEED = r"""
() => {
  const d = new Date();
  const p = n => String(n).padStart(2, '0');
  const today = d.getFullYear() + '-' + p(d.getMonth() + 1) + '-' + p(d.getDate());
  localStorage.setItem('sora-home-dashboard-sync-v2', JSON.stringify({ off: true }));
  const st = {
    v: 1, xpTune: 1, xpTune2: 1, xpTune3: 1, orderTune1: 1, starterTune1: 1, nameTune1: 1,
    questDate: today,
    title: '우리가족 대시보드',
    kids: {
      haseong: { name: '하성', tag: '9살', partner: 'charmander', level: 8, xp: 195,
        dexOpen: ['charmander','pichu','cinnamoroll','mymelody','squirtle','hellokitty','bulbasaur','pompompurin','eevee','pochacco','pikachu'],
        quests: [
          { id: 'h1', text: '리딩앤', xp: 10, done: false },
          { id: 'h2', text: '연산', xp: 15, done: false },
          { id: 'h3', text: '디딤돌', xp: 15, done: true },
          { id: 'h4', text: '팩토', xp: 15, done: true },
          { id: 'h5', text: '한자', xp: 10, done: true },
          { id: 'h6', text: '영어숙제', xp: 15, done: false },
          { id: 'h7', text: '독서', xp: 10, done: false },
          { id: 'h8', text: '독서록', xp: 15, done: false }
        ] },
      hayun: { name: '하윤', tag: '7살', partner: 'pichu', level: 6, xp: 120,
        dexOpen: ['charmander','pichu','cinnamoroll','mymelody','squirtle','hellokitty','cinderella','bulbasaur','pompompurin'],
        quests: [
          { id: 'y1', text: '한글 2장', xp: 20, done: false },
          { id: 'y2', text: '수학 2장', xp: 20, done: false },
          { id: 'y3', text: '토도영어', xp: 20, done: true },
          { id: 'y4', text: '독서', xp: 15, done: false },
          { id: 'y5', text: '가방정리', xp: 15, done: false }
        ] }
    },
    events: {}, ddays: [], wishes: [],
    chat: { me: '엄마', msgs: [
      { id: 'm1', who: '엄마', text: '오늘도 화이팅! 오늘의 퀘스트도 하나씩 해 보자 🙂', at: Date.now() - 420000, reactions: {} },
      { id: 'm2', who: '하성', text: '엄마 나 리딩앤 거의 다 했어요!', at: Date.now() - 240000, reactions: {'❤️': ['엄마']} },
      { id: 'm3', who: '하윤', text: '나도 한글 끝내고 색종이 접을 거야~', at: Date.now() - 120000, reactions: {} }
    ] }
  };
  localStorage.setItem('sora-home-dashboard-v1', JSON.stringify(st));
}
"""

with sync_playwright() as p:
    b = p.chromium.launch()
    ctx = b.new_context(viewport={"width": 1440, "height": 900}, device_scale_factor=2)
    pg = ctx.new_page()
    errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.on("console", lambda m: errs.append("console:" + m.text) if m.type == "error" else None)

    pg.goto(FILE)
    pg.evaluate(SEED)
    pg.reload()
    pg.wait_for_timeout(1200)

    # 하성 카드를 펼치고 첫 퀘스트(리딩앤 10점)를 체크 → 195+10 = Lv.9
    pg.click('.kid-card[data-kid=haseong] .kid-top')
    pg.wait_for_timeout(700)
    pg.click('.kid-card[data-kid=haseong] .quest[data-id="h1"] .qcheck')
    pg.wait_for_timeout(1100)

    state1 = pg.evaluate("""() => {
      const g = document.getElementById('giftLv');
      return {
        on: g.classList.contains('on'),
        badge: document.getElementById('giftBadge').textContent.trim(),
        title: document.getElementById('giftTitle').textContent.trim(),
        hint: document.getElementById('giftHint').textContent.trim(),
        opened: !document.getElementById('giftOpen').hidden,
        stageHidden: document.getElementById('giftStage').hidden
      };
    }""")
    print("STAGE1", state1)
    pg.screenshot(path="/workspace/downloads/레벨업_선물상자_도착.png")

    # 선물 상자 터치 → 개봉 연출 → 새 친구 소개
    box = pg.locator('#giftBox').bounding_box()
    pg.mouse.click(box['x'] + box['width'] / 2, box['y'] + box['height'] / 2)
    pg.wait_for_timeout(1400)
    state2 = pg.evaluate("""() => {
      const q = id => document.getElementById(id);
      return {
        opened: !q('giftOpen').hidden,
        tag: q('goTag').textContent.trim(),
        name: q('goName').textContent.trim(),
        desc: q('goDesc').textContent.trim(),
        dex: q('goDex').textContent.trim(),
        take: q('giftTake').textContent.trim(),
        takeHidden: q('giftTake').hidden,
        dexCount: document.querySelector('.kid-card[data-kid=haseong] [data-dexcount]').textContent
      };
    }""")
    print("STAGE2", state2)
    pg.screenshot(path="/workspace/downloads/레벨업_캐릭터_소개.png")

    print("ERRORS", errs[:5])
    ctx.close()
    b.close()
