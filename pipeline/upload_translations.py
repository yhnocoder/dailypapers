"""Upload tongtu output for the starred papers to Cloudflare R2 (via the dailypapers-upload Worker).

Usage: python3 pipeline/upload_translations.py topics/search-rec.json WORK <arxiv_id> [<arxiv_id> ...]

For each paper it finds tongtu's work directory (`tongtu status <id> --json`), uploads
  papers/<idv>/<idv>.zh.pdf   and   papers/<idv>/<idv>_out.zip  (the whole out/ folder)
and records the public-facing (Access-protected) URLs in WORK/translations.json, which
pipeline/assemble.py reads. Papers whose translation failed are recorded with an "error".

The upload token is never stored here: the session's network proxy injects it into the
Authorization header for the upload host. Outside a session, set DAILYPAPERS_UPLOAD_TOKEN.
"""
import io, json, os, subprocess, sys, urllib.request, zipfile


def tongtu_workdir(pid):
    out = subprocess.run(["tongtu", "status", pid, "--json"], capture_output=True, text=True)
    if out.returncode:
        return None
    return json.loads(out.stdout).get("workdir")


def put(url, data, ctype):
    token = os.environ.get("DAILYPAPERS_UPLOAD_TOKEN", "injected-by-proxy")
    req = urllib.request.Request(url, data=data, method="PUT",
                                 headers={"Authorization": f"Bearer {token}", "Content-Type": ctype})
    with urllib.request.urlopen(req, timeout=300) as r:
        return json.load(r)


def main(topic_path, work, *ids):
    cfg = json.load(open(topic_path))["translations"]
    up, files = cfg["upload_base"].rstrip("/"), cfg["files_base"].rstrip("/")
    if not up or not files:
        print("translations.upload_base / files_base not configured; skipping upload")
        return
    path = os.path.join(work, "translations.json")
    result = json.load(open(path)) if os.path.exists(path) else {}
    for pid in ids:
        wd = tongtu_workdir(pid)
        idv = os.path.basename(wd) if wd else None
        pdf = os.path.join(wd, "out", f"{idv}.zh.pdf") if wd else None
        if not pdf or not os.path.exists(pdf):
            result[pid] = {"error": "tongtu produced no PDF"}
            print(f"{pid}: no PDF, skipped")
            continue
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
            for name in sorted(os.listdir(os.path.join(wd, "out"))):
                z.write(os.path.join(wd, "out", name), f"{idv}/{name}")
        put(f"{up}/papers/{idv}/{idv}.zh.pdf", open(pdf, "rb").read(), "application/pdf")
        put(f"{up}/papers/{idv}/{idv}_out.zip", buf.getvalue(), "application/zip")
        result[pid] = {"pdf": f"{files}/papers/{idv}/{idv}.zh.pdf", "zip": f"{files}/papers/{idv}/{idv}_out.zip"}
        print(f"{pid}: uploaded {idv}")
    json.dump(result, open(path, "w"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main(*sys.argv[1:])
