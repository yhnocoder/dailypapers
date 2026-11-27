// dailypapers-files: serves tongtu translations from R2, only to viewers that passed Cloudflare Access.
//
// Access sits in front of this Worker (workers.dev → Cloudflare Access). The Worker re-checks the
// Access JWT itself, so the files stay private even if Access is switched off by mistake.
// GET /papers/<id>/<file>  → PDF inline (opens in the browser), anything else as a download.

const KEY = /^papers\/[\w.-]+\/[\w.-]+$/;
const TYPES = { pdf: "application/pdf", zip: "application/zip", json: "application/json" };

export default {
  async fetch(req, env) {
    if (req.method !== "GET" && req.method !== "HEAD") return new Response("method not allowed", { status: 405 });
    if (!(await accessOk(req, env))) return new Response("forbidden", { status: 403 });
    const key = decodeURIComponent(new URL(req.url).pathname.slice(1));
    if (!KEY.test(key)) return new Response("not found", { status: 404 });
    const obj = await env.BUCKET.get(key);
    if (!obj) return new Response("not found", { status: 404 });
    const name = key.split("/").pop(), ext = name.split(".").pop();
    return new Response(req.method === "HEAD" ? null : obj.body, {
      headers: {
        "content-type": TYPES[ext] || "application/octet-stream",
        "content-disposition": `${ext === "pdf" ? "inline" : "attachment"}; filename="${name}"`,
        "cache-control": "private, max-age=3600",
        etag: obj.httpEtag,
      },
    });
  },
};

const b64url = (s) => Uint8Array.from(atob(s.replace(/-/g, "+").replace(/_/g, "/")), (c) => c.charCodeAt(0));
const json = (s) => JSON.parse(new TextDecoder().decode(b64url(s)));

async function accessOk(req, env) {
  const jwt = req.headers.get("cf-access-jwt-assertion");
  if (!jwt || !env.ACCESS_TEAM_DOMAIN || !env.ACCESS_AUD) return false;
  const [h, p, s] = jwt.split(".");
  if (!s) return false;
  let header, claims;
  try { header = json(h); claims = json(p); } catch { return false; }
  const aud = Array.isArray(claims.aud) ? claims.aud : [claims.aud];
  if (!aud.includes(env.ACCESS_AUD)) return false;
  if (claims.iss !== `https://${env.ACCESS_TEAM_DOMAIN}`) return false;
  if (!claims.exp || claims.exp * 1000 < Date.now()) return false;
  const certs = await fetch(`https://${env.ACCESS_TEAM_DOMAIN}/cdn-cgi/access/certs`, { cf: { cacheTtl: 3600 } }).then((r) => r.json());
  const jwk = (certs.keys || []).find((k) => k.kid === header.kid);
  if (!jwk) return false;
  const key = await crypto.subtle.importKey("jwk", jwk, { name: "RSASSA-PKCS1-v1_5", hash: "SHA-256" }, false, ["verify"]);
  return crypto.subtle.verify("RSASSA-PKCS1-v1_5", key, b64url(s), new TextEncoder().encode(`${h}.${p}`));
}
