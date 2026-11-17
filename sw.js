/* 우리가족 대시보드 서비스 워커
   · 홈 화면에 추가했을 때 앱처럼 뜨게 하고(오프라인에서도 마지막 화면은 열려요)
   · 휴대폰 푸시(VAPID) 알림을 받아 띄우고, 누르면 대시보드로 들어와요 */
const VERSION = 'v4-hayun-pts';
const CACHE = 'family-dashboard-' + VERSION;
const PRECACHE = [
  './',
  'manifest.webmanifest',
  'icons/icon-192.png',
  'icons/icon-512.png',
  'icons/apple-touch-icon.png'
];

/* ── 설치: 필요한 파일만 담아 두고 바로 새 버전으로 넘어가요 ── */
self.addEventListener('install', event => {
  event.waitUntil((async () => {
    try {
      const cache = await caches.open(CACHE);
      await Promise.all(PRECACHE.map(url => cache.add(new Request(url, { cache: 'reload' })).catch(() => {})));
    } catch (e) { /* 저장 공간이 없어도 설치는 계속해요 */ }
    await self.skipWaiting();
  })());
});

/* ── 활성화: 예전 캐시를 지우고 바로 화면을 맡아요 ── */
self.addEventListener('activate', event => {
  event.waitUntil((async () => {
    try {
      const keys = await caches.keys();
      await Promise.all(keys.filter(k => k !== CACHE && k.startsWith('family-dashboard-')).map(k => caches.delete(k)));
    } catch (e) {}
    await self.clients.claim();
  })());
});

/* ── 화면 요청: 인터넷이 되면 새 화면, 안 되면 마지막 화면 ── */
self.addEventListener('fetch', event => {
  const req = event.request;
  if (req.method !== 'GET') return;
  const url = new URL(req.url);
  if (url.origin !== self.location.origin) return;   /* Firebase·날씨 등은 그대로 지나가게 */

  if (req.mode === 'navigate') {
    event.respondWith((async () => {
      try {
        const fresh = await fetch(req);
        const cache = await caches.open(CACHE);
        cache.put(req, fresh.clone()).catch(() => {});
        return fresh;
      } catch (e) {
        const cache = await caches.open(CACHE);
        const hit = (await cache.match(req)) || (await cache.match('./')) || (await cache.match('index.html'));
        if (hit) return hit;
        return new Response('인터넷이 끊겨 있어요. 연결되면 다시 열어 주세요.', {
          status: 503, headers: { 'Content-Type': 'text/plain; charset=utf-8' }
        });
      }
    })());
    return;
  }

  /* 아이콘·매니페스트 같은 고정 파일: 있는 건 바로, 없으면 받아 와서 저장 */
  event.respondWith((async () => {
    const cache = await caches.open(CACHE);
    const hit = await cache.match(req);
    if (hit) return hit;
    try {
      const res = await fetch(req);
      if (res && res.ok) cache.put(req, res.clone()).catch(() => {});
      return res;
    } catch (e) {
      return hit || Response.error();
    }
  })());
});

/* ── 푸시 알림 표시 ── */
self.addEventListener('push', event => {
  let data = {};
  try { data = event.data ? event.data.json() : {}; } catch (e) {
    try { data = { body: event.data ? event.data.text() : '' }; } catch (e2) { data = {}; }
  }
  const title = data.title || '💬 우리가족 대화방';
  const options = {
    body: data.body || '새 메시지가 도착했어요',
    icon: data.icon || 'icons/icon-192.png',
    badge: 'icons/icon-192.png',
    tag: data.tag || 'family-chat',
    renotify: true,
    data: { url: data.url || '/family-dashboard/' },
    vibrate: [80, 40, 80]
  };
  event.waitUntil(self.registration.showNotification(title, options));
});

/* ── 알림을 누르면: 켜져 있는 대시보드 창을 앞으로, 없으면 새로 열기 ── */
self.addEventListener('notificationclick', event => {
  event.notification.close();
  const target = (event.notification.data && event.notification.data.url) || '/family-dashboard/';
  event.waitUntil((async () => {
    const list = await self.clients.matchAll({ type: 'window', includeUncontrolled: true });
    for (const client of list) {
      if (client.url.indexOf('/family-dashboard/') >= 0) {
        try { await client.focus(); } catch (e) {}
        if (client.navigate && target && client.url.indexOf(target) < 0) {
          try { await client.navigate(target); } catch (e) {}
        }
        return;
      }
    }
    if (self.clients.openWindow) await self.clients.openWindow(target);
  })());
});
