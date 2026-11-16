'use strict';
/* 우리가족 대시보드 — 웹 푸시 발송 서버 (Vercel 서버리스 함수)
 *
 * 쓰는 법
 *  1) Vercel 프로젝트 환경변수에 아래 세 개를 넣어요
 *       VAPID_PUBLIC_KEY  : 대시보드 index.html 에 들어 있는 공개키와 같은 값
 *       VAPID_PRIVATE_KEY : 비밀키 (공개 금지)
 *       VAPID_SUBJECT     : mailto:... 또는 https://... 주소 (없으면 기본값)
 *  2) 배포되면  https://<프로젝트>.vercel.app/api/push  로 POST 하면 돼요.
 *     본문: { subscriptions: [{ id, endpoint, keys }], title, body, url }
 *  응답: { ok, total, sent, failed, expired: [만료된 구독 id...] }
 *        expired 에 들어온 id 는 클라이언트가 Firebase 에서 지워요 (404/410 = 이미 만료)
 */

const webpush = require('web-push');

const DEFAULT_VAPID_PUBLIC = 'BL5p_98asNkagVDnRvKAJl0WF2pOU0NSriVqDKKFXi2Cnfhb_dy6F1QqPDpOymq71xwIGztfxY_-XX1c0qmRBJY';
const _envPub = (process.env.VAPID_PUBLIC_KEY || '').replace(/\s+/g, '');
const VAPID_PUBLIC_KEY = _envPub.length === 87 ? _envPub : DEFAULT_VAPID_PUBLIC;
const VAPID_PRIVATE_KEY = (process.env.VAPID_PRIVATE_KEY || '').replace(/\s+/g, '');
const VAPID_SUBJECT = (process.env.VAPID_SUBJECT || 'mailto:soray135@example.com').trim();
const MAX_SUBSCRIPTIONS = 40;

function sendJson(res, status, body) {
  res.statusCode = status;
  res.setHeader('Content-Type', 'application/json; charset=utf-8');
  res.setHeader('Cache-Control', 'no-store');
  res.end(JSON.stringify(body));
}

function readStream(req) {
  return new Promise(resolve => {
    let raw = '';
    let done = false;
    const finish = value => { if (!done) { done = true; resolve(value); } };
    req.on('data', chunk => {
      raw += chunk;
      if (raw.length > 200000) { finish(null); req.destroy(); }   /* 너무 큰 본문은 무시 */
    });
    req.on('end', () => {
      if (!raw) return finish(null);
      try { finish(JSON.parse(raw)); } catch (e) { finish(null); }
    });
    req.on('error', () => finish(null));
  });
}

async function readBody(req) {
  if (req.body && typeof req.body === 'object') return req.body;
  if (typeof req.body === 'string' && req.body) {
    try { return JSON.parse(req.body); } catch (e) { return null; }
  }
  return readStream(req);
}

/* web-push 는 endpoint/keys 만 보므로 id 같은 여분 필드가 섞여도 괜찮아요 */
function cleanSub(sub) {
  if (!sub || typeof sub.endpoint !== 'string' || !sub.endpoint) return null;
  const keys = sub.keys && typeof sub.keys === 'object'
    ? { p256dh: String(sub.keys.p256dh || ''), auth: String(sub.keys.auth || '') }
    : null;
  if (!keys || !keys.p256dh || !keys.auth) return null;
  return {
    id: sub.id != null ? String(sub.id) : sub.endpoint,
    endpoint: sub.endpoint,
    keys
  };
}

module.exports = async function handler(req, res) {
  /* 어느 화면에서든 부를 수 있게 CORS 를 열어 둬요 (비밀 값은 응답에 담지 않아요) */
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
  res.setHeader('Access-Control-Max-Age', '86400');

  if (req.method === 'OPTIONS') {
    res.statusCode = 204;
    res.setHeader('Content-Length', '0');
    res.end();
    return;
  }
  if (req.method === 'GET') {
    /* 브라우저에서 열어 봤을 때 상태를 알 수 있게 */
    sendJson(res, 200, {
      ok: true,
      service: 'family-dashboard-push',
      ready: !!(VAPID_PUBLIC_KEY && VAPID_PRIVATE_KEY),
      hint: 'POST { subscriptions: [...], title, body } 로 알림을 보내요'
    });
    return;
  }
  if (req.method !== 'POST') {
    sendJson(res, 405, { ok: false, error: 'method_not_allowed' });
    return;
  }

  if (!VAPID_PUBLIC_KEY || !VAPID_PRIVATE_KEY) {
    sendJson(res, 500, {
      ok: false,
      error: 'missing_vapid_keys',
      message: 'Vercel 환경변수 VAPID_PUBLIC_KEY / VAPID_PRIVATE_KEY 를 넣어 주세요'
    });
    return;
  }

  let payload = null;
  try { payload = await readBody(req); } catch (e) { payload = null; }
  if (!payload || typeof payload !== 'object') {
    sendJson(res, 400, { ok: false, error: 'bad_body' });
    return;
  }

  const incoming = Array.isArray(payload.subscriptions) ? payload.subscriptions : [];
  const subs = incoming.slice(0, MAX_SUBSCRIPTIONS).map(cleanSub).filter(Boolean);
  if (!subs.length) {
    sendJson(res, 400, { ok: false, error: 'no_subscriptions' });
    return;
  }

  const title = typeof payload.title === 'string' && payload.title.trim()
    ? payload.title.trim().slice(0, 80) : '💬 우리가족 대화방';
  const body = typeof payload.body === 'string' ? payload.body.slice(0, 200) : '새 메시지가 도착했어요';
  const url = typeof payload.url === 'string' && payload.url ? payload.url.slice(0, 300) : '/family-dashboard/';
  const message = JSON.stringify({ title, body, url, tag: 'family-chat' });

  try {
    webpush.setVapidDetails(VAPID_SUBJECT, VAPID_PUBLIC_KEY, VAPID_PRIVATE_KEY);
  } catch (e) {
    sendJson(res, 500, { ok: false, error: 'bad_vapid_keys', message: String((e && e.message) || e) });
    return;
  }

  const expired = [];
  let sent = 0;
  let failed = 0;

  const results = await Promise.allSettled(subs.map(sub =>
    webpush.sendNotification({ endpoint: sub.endpoint, keys: sub.keys }, message, { TTL: 600, urgency: 'high' })
      .then(r => ({ id: sub.id, status: (r && r.statusCode) || 201 }))
  ));

  results.forEach((r, i) => {
    const id = subs[i].id;
    if (r.status === 'fulfilled') {
      sent += 1;
      return;
    }
    const err = r.reason || {};
    const code = err.statusCode || err.status || 0;
    if (code === 404 || code === 410) expired.push(id);   /* 더 이상 없는 기기 → 클라이언트가 정리 */
    else failed += 1;
  });

  sendJson(res, 200, {
    ok: true,
    total: subs.length,
    sent,
    failed,
    expired
  });
};
