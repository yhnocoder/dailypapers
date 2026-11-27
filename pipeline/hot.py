"""Today's hot papers: what gained the most attention since the previous heat snapshot.

  python3 pipeline/hot.py [--date YYYY-MM-DD]

Reads the two latest heat snapshots (data/heat/, see heat.py; --date picks the newer one) and writes
  site/data/hot/<date>.json   the two boards shown on the site, `hf` and `hn`, up to `hot.keep` papers each
  site/data/hot/index.json    {"dates": [...]}: the days that have a board, newest first
then prints the boosts the hot run should make (one JSON object per line, as issue_plan.py does).

Hot = gain, not total: a paper with 500 HN points would otherwise sit on top for two weeks. A paper's
gain is its HF upvotes (or the HN points of all its stories) now minus those of the previous snapshot;
what the previous snapshot does not have counts from 0. HN needs a gain of `heat.hn_min_points`.
One slot per board goes to the paper that keeps being discussed (`reign`): the highest total among the
papers that gained in each of the last `hot.reign_snapshots` snapshots. It leads the board.

Every paper gets a `home` when the site has a place for it:
  shown in an issue                → that issue (preferring the one where it is a ⭐)
  in the pool, tagged for a topic  → the issue of that topic that covers its batch, once it is published;
                                     there it is folded or not listed, and a boost brings it in
  otherwise                        → no home: the board links to arXiv
The boosts: per board, the highest paper of the top `hot.show` that belongs to a topic and has no ⭐
becomes a ⭐ (picked once per day and kept in the board file as `picked`); the other papers of the top
that are not shown yet become shown. Run it again after the boosts are applied, so that the boards link
to the boosted papers; that run prints no boosts.
"""
import argparse, glob, json, os, sys
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from assemble import ROOT, dump, load  # noqa: E402

HEAT = os.path.join(ROOT, "data", "heat")
OUT = os.path.join(ROOT, "site", "data", "hot")
DEFAULTS = {"show": 10, "keep": 30, "reign_snapshots": 3}


def value(p, src):
    if src == "hf":
        return (p.get("hf") or {}).get("upvotes", 0)
    return sum(s.get("points", 0) for s in p.get("hn", []))


def snapshots(day=None):
    days = sorted(os.path.basename(f)[:-5] for f in glob.glob(os.path.join(HEAT, "*.json")))
    if day:
        days = [d for d in days if d <= day]
    if not days or (day and days[-1] != day):
        sys.exit(f"no heat snapshot for {day or 'any day'}: run pipeline/heat.py first")
    return [(d, load(os.path.join(HEAT, d + ".json"))["papers"]) for d in days]


def pool():
    """id → the pool record (first batch that has it), with its batch."""
    found = {}
    for f in sorted(glob.glob(os.path.join(ROOT, "data", "papers", "*.json"))):
        b = os.path.basename(f)[:-5]
        for p in load(f)["papers"]:
            found.setdefault(p["id"], {**p, "batch": b})
    return found


def published(ids):
    """id → where the site has the paper: [{topic, key, where, star}]."""
    topics = load(os.path.join(ROOT, "site", "data", "topics.json"), {"topics": []})["topics"]
    found = {}
    for t in topics:
        for key in t.get("dates", []):
            issue = load(os.path.join(ROOT, "site", "data", t["id"], key + ".json"))
            if not issue:
                continue
            for where in ("papers", "others", "excluded"):
                for p in issue.get(where, []):
                    if p["id"] in ids:
                        found.setdefault(p["id"], []).append(
                            {"topic": t["id"], "key": key, "where": where, "star": bool(p.get("star"))})
    return found


def arxiv_titles(ids):
    """Titles of papers that never entered the pool (older, or outside our categories)."""
    if not ids:
        return {}
    try:
        from fetch_arxiv import query
        return {p["id"]: p["title"] for i in range(0, len(ids), 50) for p in query("", id_list=",".join(ids[i:i + 50]))}
    except Exception as e:  # the board still works without them: the row shows the arXiv id
        print(f"WARNING arXiv titles: {e}", file=sys.stderr)
        return {}


def board(src, snaps, cfg, min_gain):
    """Papers by gain since the previous snapshot, the reigning one first."""
    cur, prev = snaps[-1][1], (snaps[-2][1] if len(snaps) > 1 else {})
    rows = []
    for pid, p in cur.items():
        total = value(p, src)
        gain = total - value(prev.get(pid, {}), src)
        if total and gain >= min_gain:
            streak = 1  # snapshots in a row, ending now, in which it gained
            for k in range(len(snaps) - 2, 0, -1):
                if value(snaps[k][1].get(pid, {}), src) - value(snaps[k - 1][1].get(pid, {}), src) <= 0:
                    break
                streak += 1
            rows.append({"id": pid, "gain": gain, "total": total, "streak": streak})
    rows.sort(key=lambda r: (-r["gain"], -r["total"], r["id"]))
    reign = max((r for r in rows if r["streak"] >= cfg["reign_snapshots"]), key=lambda r: r["total"], default=None)
    if reign:
        reign["reign"] = True
        start = date.fromisoformat(snaps[len(snaps) - 1 - reign["streak"]][0])
        reign["days"] = (date.fromisoformat(snaps[-1][0]) - start).days
        rows = [reign] + [r for r in rows if r is not reign]
    rows = rows[:cfg["keep"]]
    for r in rows:
        if src == "hn":
            top = max(cur[r["id"]]["hn"], key=lambda s: s.get("points", 0))
            r["url"], r["hn_title"] = f"https://news.ycombinator.com/item?id={top['id']}", top.get("title", "")
        else:
            r["url"] = f"https://huggingface.co/papers/{r['id']}"
    return rows


def place(row, pl, pub, topics):
    """Fill title, topics and home; return the boost this paper can get (topic, key) or None."""
    p, where = pl.get(row["id"]), pub.get(row["id"], [])
    tags = sorted(((p or {}).get("tags") or {}).items(), key=lambda kv: -kv[1]["score"])
    row["topics"] = [t for t, _ in tags]
    if p:
        row["title"], row["title_zh"] = p["title"], p.get("title_zh", "")
    shown = sorted((w for w in where if w["where"] == "papers"),
                   key=lambda w: (not w["star"], row["topics"].index(w["topic"]) if w["topic"] in row["topics"] else 99))
    if shown:
        row["home"], row["star"] = {"topic": shown[0]["topic"], "key": shown[0]["key"]}, shown[0]["star"]
        return (shown[0]["topic"], shown[0]["key"]) if not shown[0]["star"] else None
    if not tags:
        return None
    best = tags[0][0]
    key = next((k for k in topics[best].get("dates", [])
                if p["batch"] in topics[best].get("issues", {}).get(k, [k])), None)
    return (best, key) if key else None  # no issue yet: the paper competes there as usual


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date")
    a = ap.parse_args()
    ing = load(os.path.join(ROOT, "topics", "_ingest.json"))
    cfg = {**DEFAULTS, **ing.get("hot", {})}
    snaps = snapshots(a.date)
    day, since = snaps[-1][0], (snaps[-2][0] if len(snaps) > 1 else None)
    boards = {"hf": board("hf", snaps, cfg, 1), "hn": board("hn", snaps, cfg, ing["heat"].get("hn_min_points", 10))}
    ids = {r["id"] for rows in boards.values() for r in rows}
    pl, pub = pool(), published(ids)
    topics = {t["id"]: t for t in load(os.path.join(ROOT, "site", "data", "topics.json"))["topics"]}
    titles = arxiv_titles(sorted(i for i in ids if i not in pl))
    # The ⭐ of each board is picked once per day and remembered in the board file: after it is boosted the
    # next run must not hand the ⭐ to the paper below it.
    picked = dict((load(os.path.join(OUT, day + ".json")) or {}).get("picked", {}))
    plan = {}
    for src, rows in boards.items():
        for n, r in enumerate(rows):
            target = place(r, pl, pub, topics)
            r.setdefault("title", titles.get(r["id"]) or r.get("hn_title") or r["id"])
            r.pop("hn_title", None)
            if not target or n >= cfg["show"]:
                continue
            if src not in picked and not r.get("star"):
                picked[src] = r["id"]
            level = "star" if picked.get(src) == r["id"] else "shown"
            if r.get("star") or (level == "shown" and "home" in r):
                continue  # nothing left to do for this paper
            old = plan.get(r["id"])
            if not old or (level == "star" and old["level"] == "shown"):
                plan[r["id"]] = {"topic": target[0], "key": target[1], "id": r["id"], "level": level,
                                 "why": f"{src.upper()} +{r['gain']}", "title": r["title"]}
    os.makedirs(OUT, exist_ok=True)
    dump({"date": day, "since": since, "picked": picked, **boards}, os.path.join(OUT, day + ".json"))
    days = sorted({os.path.basename(f)[:-5] for f in glob.glob(os.path.join(OUT, "2*.json"))}, reverse=True)
    dump({"dates": days}, os.path.join(OUT, "index.json"))
    print(f"hot {day} (since {since}): hf {len(boards['hf'])}, hn {len(boards['hn'])}; "
          f"{sum('home' in r for rows in boards.values() for r in rows)} with a page; {len(plan)} boost(s)", file=sys.stderr)
    for b in sorted(plan.values(), key=lambda b: (b["topic"], b["key"], b["level"] != "star")):
        print(json.dumps(b, ensure_ascii=False))


if __name__ == "__main__":
    main()
