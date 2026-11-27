"""Heat snapshot: community attention for recent arXiv papers (data only; not shown on the site yet).

  python3 pipeline/heat.py [--date YYYY-MM-DD]      writes site/data/heat/<date>.json (date = today, US/Eastern)

Heat keeps growing for a while after a paper appears, so we never overwrite older numbers:
each run stores a full snapshot of everything the sources show inside a rolling window
(`heat.window_days` in topics/_ingest.json, 14 days). A paper that leaves the window keeps
the numbers of its last snapshot. Comparing two snapshots gives the heat gained in between
(what a "this week's hot papers" view should rank by).

Sources (both public, no key):
  hf  Hugging Face Daily Papers, one request per day: upvotes, comments, the HF listing date
  hn  Hacker News via Algolia: stories linking to arxiv.org: points, comments, story id/url/time
"""
import json, os, re, sys, time, urllib.parse, urllib.request
from datetime import date, datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from batch_date import ET  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UA = {"User-Agent": "dailypapers-pipeline/1.0"}
ARXIV_ID = re.compile(r"arxiv\.org/(?:abs|pdf|html)/(\d{4}\.\d{4,5})", re.I)


def get_json(url, tries=4):
    for i in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
                return json.load(r)
        except Exception:
            if i == tries - 1:
                raise
            time.sleep(10 * (i + 1))


def snapshot(day: date):
    win = json.load(open(os.path.join(ROOT, "topics", "_ingest.json")))["heat"]["window_days"]
    papers, errors = {}, []
    for k in range(win):
        d = day - timedelta(days=k)
        try:
            for x in get_json(f"https://huggingface.co/api/daily_papers?date={d}&limit=100"):
                pid = x["paper"]["id"]
                papers.setdefault(pid, {})["hf"] = {"date": d.isoformat(), "upvotes": x["paper"].get("upvotes", 0),
                                                     "comments": x.get("numComments", 0)}
        except Exception as e:
            errors.append(f"hf {d}: {e}")
    since = int(datetime(day.year, day.month, day.day, tzinfo=ET).timestamp()) - (win - 1) * 86400
    page = 0
    while True:
        q = urllib.parse.urlencode({"query": "arxiv.org", "tags": "story", "hitsPerPage": 1000, "page": page,
                                    "numericFilters": f"created_at_i>{since}"})
        try:
            r = get_json(f"https://hn.algolia.com/api/v1/search_by_date?{q}")
        except Exception as e:
            errors.append(f"hn page {page}: {e}")
            break
        for h in r["hits"]:
            m = ARXIV_ID.search(h.get("url") or "")
            if not m:
                continue
            papers.setdefault(m.group(1), {}).setdefault("hn", []).append(
                {"id": h["objectID"], "points": h.get("points") or 0, "comments": h.get("num_comments") or 0,
                 "title": h.get("title", ""), "created_at": h.get("created_at", "")})
        page += 1
        if page >= r.get("nbPages", 0):
            break
    out = {"date": day.isoformat(), "taken_at": datetime.now(ET).isoformat(timespec="minutes"),
           "window_days": win, "errors": errors, "papers": papers}
    path = os.path.join(ROOT, "site", "data", "heat", f"{day}.json")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=0)
        f.write("\n")
    n_hf = sum("hf" in v for v in papers.values())
    n_hn = sum("hn" in v for v in papers.values())
    print(f"heat {day}: {len(papers)} papers (hf {n_hf}, hn {n_hn}); {len(errors)} source errors")
    return out


def latest():
    """Most recent snapshot, or {} when there is none."""
    d = os.path.join(ROOT, "site", "data", "heat")
    files = sorted(f for f in os.listdir(d) if f.endswith(".json")) if os.path.isdir(d) else []
    return json.load(open(os.path.join(d, files[-1]))) if files else {}


if __name__ == "__main__":
    day = date.fromisoformat(sys.argv[2]) if sys.argv[1:2] == ["--date"] else datetime.now(ET).date()
    snapshot(day)
