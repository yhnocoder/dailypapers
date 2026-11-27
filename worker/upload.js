// dailypapers-upload: lets the daily Claude session write tongtu output into R2.
// PUT /papers/<id>/<file> with "Authorization: Bearer <UPLOAD_TOKEN>". No reads, no deletes.

const KEY = /^papers\/[\w.-]+\/[\w.-]+$/;
const MAX = 100 * 1024 * 1024;

export default {
  async fetch(req, env) {
    if (req.method !== "PUT") return new Response("method not allowed", { status: 405 });
    if (!env.UPLOAD_TOKEN || !(await same(req.headers.get("authorization") || "", `Bearer ${env.UPLOAD_TOKEN}`)))
      return new Response("unauthorized", { status: 401 });
    const key = decodeURIComponent(new URL(req.url).pathname.slice(1));
    if (!KEY.test(key)) return new Response("bad key", { status: 400 });
    const len = Number(req.headers.get("content-length") || 0);
    if (!len || len > MAX) return new Response("bad length", { status: 413 });
    await env.BUCKET.put(key, req.body);
    return Response.json({ ok: true, key, bytes: len });
  },
};

// constant-time comparison via HMAC of both sides
async function same(a, b) {
  const k = await crypto.subtle.importKey("raw", crypto.getRandomValues(new Uint8Array(32)), { name: "HMAC", hash: "SHA-256" }, false, ["sign"]);
  const [x, y] = await Promise.all([a, b].map((s) => crypto.subtle.sign("HMAC", k, new TextEncoder().encode(s))));
  const u = new Uint8Array(x), v = new Uint8Array(y);
  let d = 0;
  for (let i = 0; i < u.length; i++) d |= u[i] ^ v[i];
  return d === 0;
}
