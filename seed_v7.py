"""3칼럼 개편 테스트·미리보기 공용 더미 시드 (실제 가족 방은 쓰지 않아요)"""
FILE = "file:///workspace/work-famdash/index.html"
SEED = r"""
() => {
  const raw = localStorage.getItem('sora-home-dashboard-v1');
  const st = JSON.parse(raw);
  const now = Date.now();
  const mk = (who, text, min, rx) => ({ id: 'm' + Math.random().toString(36).slice(2, 9), who, text, at: now - min * 60000, reactions: rx || {} });
  st.kids.haseong.name = '하성이'; st.kids.haseong.tag = '9살';
  st.kids.hayun.name = '하윤이';   st.kids.hayun.tag = '7살';
  st.kids.haseong.level = 7; st.kids.haseong.xp = 128;
  st.kids.hayun.level = 5;     st.kids.hayun.xp = 72;
  st.kids.haseong.quests.forEach((q, i) => { q.done = i < 4; });
  st.kids.hayun.quests.forEach((q, i) => { q.done = i < 2; });
  st.chat.msgs = [
    mk('엄마', '우리 가족 대시보드에 온 걸 환영해요 🙂', 150, { '❤️': ['하성', '하윤'] }),
    mk('하성', '엄마 오늘 리딩앤 다 했어요!', 138),
    mk('하윤', '나도 한글 2장 끝냈어!!', 126, { '👏': ['엄마'] }),
    mk('엄마', '우와 둘 다 최고 👏 오늘 간식은 아이스크림!', 112),
    mk('아빠', '오늘 저녁은 뭐 먹지?', 96),
    mk('하성', '로봇 숙제도 끝냈어요 🤖', 84),
    mk('엄마', '다들 오늘도 수고했어 ❤️', 72),
    mk('하윤', '내일 소풍 가는 날이야~', 60),
    mk('아빠', '소풍 가방 미리 싸 두자', 48),
    mk('하성', '나는 과자 사 갈래요 🍪', 36),
    mk('엄마', '물통이랑 돗자리도 챙기고!', 24),
    mk('하윤', '응! 내일 아침에 같이 싸자 😊', 8)
  ];
  st.wishes = [
    { id: 'w1', name: '색연필 세트', who: '하윤', memo: '12색 · 8,000원', done: false },
    { id: 'w2', name: '리딩앤 연장', who: '하성', memo: '3개월', done: false },
    { id: 'w3', name: '실내화', who: '하성', memo: '240mm', done: false }
  ];
  st.ddays = [
    { id: 'd1', title: '하성 리딩앤 시험', date: '2026-11-20', icon: '📚' },
    { id: 'd2', title: '후쿠오카 가족여행', date: '2026-12-19', icon: '✈️' },
    { id: 'd3', title: '크리스마스', date: '2026-12-25', icon: '🎄' },
    { id: 'd4', title: '하윤 생일', date: '2027-01-08', icon: '🎂' },
    { id: 'd5', title: '겨울방학', date: '2026-12-29', icon: '⛄' }
  ];
  localStorage.setItem('sora-home-dashboard-v1', JSON.stringify(st));
  localStorage.setItem('sora-home-dashboard-sync-v2', JSON.stringify({ off: true }));
}
"""
