"""Daily ingest: build the shared paper pool for one arXiv batch.

  python3 pipeline/ingest.py plan  [--now YYYY-MM-DDTHH:MM]   batches still missing a pool (oldest first)
  python3 pipeline/ingest.py fetch <date> WORK                 arXiv union of every topic's categories
                                                               + recent HF Daily / HN papers not in any pool
  python3 pipeline/ingest.py split WORK                        WORK/batches/b<i>.json for the tagging agents
  python3 pipeline/ingest.py build <date> WORK                 WORK/out/*.json → data/papers/<date>.json

A batch is identified by its arXiv cutoff date (US/Eastern). The pool keeps, for every
candidate: arXiv metadata, the English abstract, `title_zh`, `summary_zh`, `affiliation`,
where it came from (`src`), and per-topic `tags` ({direction, score, star_candidate, star_why}).
Full Chinese abstracts are NOT written here; the issue stage writes them for shown papers only.
"""
import glob, json, os, re, sys, time, urllib.parse, urllib.request
from datetime import date, datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from batch_date import ET, is_batch, latest_batch  # noqa: E402
from fetch_arxiv import query, window  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POOL = os.path.join(ROOT, "data", "papers")
UA = {"User-Agent": "dailypapers-pipeline/1.0"}


def cfg():
    return json.load(open(os.path.join(ROOT, "topics", "_ingest.json")))


def topics():
    out = []
    for p in sorted(glob.glob(os.path.join(ROOT, "topics", "*.json"))):
        if not os.path.basename(p).startswith("_"):
            out.append(json.load(open(p)))
    return out


def pool_dates():
    return sorted(os.path.basename(p)[:-5] for p in glob.glob(os.path.join(POOL, "*.json")))


def plan(now):
    c = cfg()
    last = latest_batch(now)
    start = max(date.fromisoformat(c["start_date"]), last - timedelta(days=c["lookback_days"]))
    have = set(pool_dates())
    d, out = start, []
    while d <= last:
        if is_batch(d) and d.isoformat() not in have:
            out.append(d.isoformat())
        d += timedelta(days=1)
    return out


def get_json(url, tries=4):
    for i in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
                return json.load(r)
        except Exception:
            if i == tries - 1:
                raise
            time.sleep(10 * (i + 1))


ARXIV_ID = re.compile(r"arxiv\.org/(?:abs|pdf|html)/(\d{4}\.\d{4,5})", re.I)


def recent_pool_ids(days=30):
    ids, cut = set(), (date.today() - timedelta(days=days)).isoformat()
    for d in pool_dates():
        if d >= cut:
            ids |= {p["id"] for p in json.load(open(os.path.join(POOL, d + ".json")))["papers"]}
    return ids


def hot_extras(batch):
    """arXiv ids that are on HF Daily (batch day and the day before) or were posted to HN in the
    last 2 days. They are added to the pool even if outside our categories or from older batches."""
    b = date.fromisoformat(batch)
    found = {}
    for d in (b - timedelta(days=1), b):
        try:
            for x in get_json(f"https://huggingface.co/api/daily_papers?date={d}&limit=100"):
                found.setdefault(x["paper"]["id"], set()).add("hf")
        except Exception as e:
            print(f"HF daily {d}: {e}", file=sys.stderr)
    since = int(time.time()) - 2 * 86400
    try:
        q = urllib.parse.urlencode({"query": "arxiv.org", "tags": "story", "hitsPerPage": 1000,
                                    "numericFilters": f"created_at_i>{since}"})
        for h in get_json(f"https://hn.algolia.com/api/v1/search_by_date?{q}")["hits"]:
            m = ARXIV_ID.search(h.get("url") or "")
            if m:
                found.setdefault(m.group(1), set()).add("hn")
    except Exception as e:
        print(f"HN: {e}", file=sys.stderr)
    return found


def fetch(batch, work):
    c, ts = cfg(), topics()
    cats = sorted({x for t in ts for x in t["categories"]})
    a, b = window(date.fromisoformat(batch))
    w = f"submittedDate:[{a} TO {b}]"
    papers = {}
    # arXiv's query string gets long with many OR terms; split into chunks of 6 categories
    for i in range(0, len(cats), 6):
        q = " OR ".join(f"cat:{x}" for x in cats[i:i + 6])
        for p in query(f"({q}) AND {w}"):
            p["src"] = ["arxiv"]
            papers.setdefault(p["id"], p)
    n_arxiv = len(papers)
    extras = hot_extras(batch)
    known = recent_pool_ids()
    missing = [i for i in extras if i not in papers and i not in known]
    for i in range(0, len(missing), 50):
        for p in query("", id_list=",".join(missing[i:i + 50])):
            p["src"] = sorted(extras.get(p["id"], set()))
            papers.setdefault(p["id"], p)
    for pid, s in extras.items():  # mark arXiv papers that are already hot
        if pid in papers and papers[pid]["src"][0] == "arxiv":
            papers[pid]["src"] = ["arxiv"] + sorted(s)
    os.makedirs(work, exist_ok=True)
    json.dump({"date": batch, "window_utc": [a, b], "categories": cats, "n_arxiv": n_arxiv,
               "papers": list(papers.values())}, open(os.path.join(work, "all.json"), "w"), ensure_ascii=False)
    ok = n_arxiv >= c["min_candidates"]
    print(f"{batch}: window {a}–{b} UTC, {n_arxiv} arXiv candidates + {len(papers) - n_arxiv} hot extras"
          + ("" if ok else f"  → below min_candidates ({c['min_candidates']}): batch probably not announced yet, SKIP"))
    return ok


def split(work):
    c = cfg()
    P = json.load(open(os.path.join(work, "all.json")))["papers"]
    for sub in ("batches", "out"):  # never mix in files from another batch
        for f in glob.glob(os.path.join(work, sub, "*.json")):
            os.remove(f)
    os.makedirs(os.path.join(work, "batches"), exist_ok=True)
    os.makedirs(os.path.join(work, "out"), exist_ok=True)
    k = c["batch_size"]
    for i in range(0, len(P), k):
        json.dump([{x: p[x] for x in ("id", "title", "cat", "cats", "comment", "abstract")} for p in P[i:i + k]],
                  open(os.path.join(work, "batches", f"b{i // k}.json"), "w"), ensure_ascii=False)
    print(f"{(len(P) + k - 1) // k} batches of ≤{k}; write each result to WORK/out/b<i>.json as a JSON array")


def build(batch, work):
    A = json.load(open(os.path.join(work, "all.json")))
    out = {x["id"]: x for f in sorted(glob.glob(os.path.join(work, "out", "*.json"))) for x in json.load(open(f))}
    tids = {t["id"]: {d["code"] for d in t["directions"]} for t in topics()}
    missing = [p["id"] for p in A["papers"] if p["id"] not in out]
    if missing:
        sys.exit(f"{len(missing)} candidates have no tagging result, e.g. {missing[:3]}")
    papers, warn = [], []
    for p in A["papers"]:
        o = out[p["id"]]
        tags = {}
        for tid, t in (o.get("tags") or {}).items():
            if tid not in tids:
                warn.append(f"{p['id']}: unknown topic {tid}")
                continue
            if t.get("direction") not in tids[tid]:
                warn.append(f"{p['id']}: {tid} direction {t.get('direction')} → Z")
                t["direction"] = "Z"
            tags[tid] = {"direction": t["direction"], "score": float(t.get("score") or 0),
                         "star_candidate": bool(t.get("star_candidate")), "star_why": t.get("star_why", "")}
        if not o.get("summary_zh") or not o.get("title_zh"):
            warn.append(f"{p['id']}: missing title_zh/summary_zh")
        papers.append({**{k: p[k] for k in ("id", "title", "authors", "cat", "cats", "comment", "abstract", "code", "src")},
                       "title_zh": o.get("title_zh", ""), "summary_zh": o.get("summary_zh", ""),
                       "affiliation": o.get("affiliation", ""), "tags": tags})
    os.makedirs(POOL, exist_ok=True)
    with open(os.path.join(POOL, batch + ".json"), "w", encoding="utf-8") as f:
        json.dump({"date": batch, "window_utc": A["window_utc"], "categories": A["categories"],
                   "n_arxiv": A["n_arxiv"], "papers": papers}, f, ensure_ascii=False, indent=0)
        f.write("\n")
    for w in warn[:20]:
        print("WARNING", w)
    per = {tid: sum(tid in p["tags"] for p in papers) for tid in tids}
    print(f"{batch}: pool {len(papers)} papers ({A['n_arxiv']} arXiv); tagged per topic {per}; {len(warn)} warnings")


if __name__ == "__main__":
    cmd, args = sys.argv[1], sys.argv[2:]
    if cmd == "plan":
        now = datetime.fromisoformat(args[1]).replace(tzinfo=ET) if args[:1] == ["--now"] else datetime.now(ET)
        print("\n".join(plan(now)))
    elif cmd == "fetch":
        sys.exit(0 if fetch(args[0], args[1]) else 3)
    elif cmd == "split":
        split(args[0])
    elif cmd == "build":
        build(args[0], args[1])
    else:
        sys.exit(__doc__)
