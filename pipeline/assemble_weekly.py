"""Assemble one week's digest JSON for the site, from dailies that are already in site/data.

Usage:
  python3 pipeline/assemble_weekly.py topics/search-rec.json 2026-W48 WORKDIR

WORKDIR/weekly.json (written by the main session, rules in prompts/writing.md 「周报」):
  {"lede": "…",
   "picks":  [{"id", "why"}],                       ⭐ papers only, 3–5
   "themes": [{"title", "body": ["…"], "papers": [id, …]}],   ≥2 papers each
   "gems":   [{"id", "note"}]}                      non-⭐ papers

Writes site/data/<topic>/weekly/<week>.json and adds the week to site/data/topics.json.
Nothing is fetched and no paper is re-read: every paper record is copied from its daily.
"""
import json, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from week import DATA, ROOT, load, load_days, topic_entry, week_of, weekly_path  # noqa: E402

REF = re.compile(r"\[\[@([\w.-]+)\|[^\]]*?\]\]")
TERM = re.compile(r"\[\[([\w.-]+)(?:\|[^\]]*?)?\]\]")
INDEX_KEYS = ("id", "title", "title_zh", "direction", "star", "score", "affiliation", "summary_zh")


def dump(obj, p):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1)
        f.write("\n")


def texts(p):
    """All rich-text strings of a ⭐ paper record (where glossary terms can appear)."""
    return [*p.get("analysis", []), p.get("abstract_zh", ""), *(f.get("caption_zh", "") for f in p.get("figures", []))]


def terms_in(strs):
    return {m.group(1) for s in strs for m in TERM.finditer(REF.sub("", s))}


def day_stats(d):
    by = {}
    for p in d["papers"]:
        by[p["direction"]] = by.get(p["direction"], 0) + 1
    return {"date": d["date"], "total": d["funnel"][0][1], "relevant": len(d["papers"]),
            "stars": sum(bool(p.get("star")) for p in d["papers"]), "by_direction": by}


def summed(days):
    by = {}
    for s in days:
        for k, n in s["by_direction"].items():
            by[k] = by.get(k, 0) + n
    return {"days": len(days), "total": sum(s["total"] for s in days), "relevant": sum(s["relevant"] for s in days),
            "stars": sum(s["stars"] for s in days), "by_direction": by}


def main(topic_path, week, work):
    topic = load(os.path.join(ROOT, topic_path))
    tid = topic["id"]
    days = load_days(tid, week)
    if not days:
        sys.exit(f"no dailies for {week}")
    w = load(os.path.join(work, "weekly.json"))
    by = {p["id"]: (d["date"], p) for d in days for p in d["papers"]}
    glossary = {t["id"] for t in load(os.path.join(DATA, "glossary.json"), {"terms": []})["terms"]}

    # ── validation: the weekly may only talk about this week's papers ──
    err = []
    picks, gems, themes = w.get("picks", []), w.get("gems", []), w.get("themes", [])
    for x in picks:
        if x["id"] not in by:
            err.append(f"pick {x['id']} is not in {week}")
        elif not by[x["id"]][1].get("star"):
            err.append(f"pick {x['id']} is not a ⭐ paper")
    pick_ids = {x["id"] for x in picks}
    for x in gems:
        if x["id"] not in by:
            err.append(f"gem {x['id']} is not in {week}")
        elif by[x["id"]][1].get("star"):
            err.append(f"gem {x['id']} is a ⭐ paper (gems are non-⭐)")
    for t in themes:
        refs = {m.group(1) for s in t["body"] for m in REF.finditer(s)}
        if len(set(t["papers"])) < 2:
            err.append(f"theme 「{t['title']}」 needs at least 2 papers")
        if refs != set(t["papers"]):
            err.append(f"theme 「{t['title']}」: papers {sorted(t['papers'])} ≠ papers linked in body {sorted(refs)}")
    own = [w.get("lede", ""), *(x["why"] for x in picks), *(x["note"] for x in gems), *(s for t in themes for s in t["body"])]
    for s in own:
        for m in REF.finditer(s):
            if m.group(1) not in by:
                err.append(f"[[@{m.group(1)}]] is not in {week}")
    for g in sorted(terms_in(own) - glossary):
        err.append(f"[[{g}]] is not in the glossary")
    if err:
        sys.exit("weekly.json rejected:\n  " + "\n  ".join(err))

    # ── glossary terms first used this week ──
    earlier = set()
    for dt in topic_entry(tid)["dates"]:
        if dt < days[0]["date"]:
            d0 = load(os.path.join(DATA, tid, f"{dt}.json"))
            earlier |= terms_in(s for p in d0["papers"] for s in texts(p)) | terms_in(d0.get("overview", {}).get("guide", []))
    used = terms_in(s for d in days for p in d["papers"] for s in texts(p)) | terms_in(g for d in days for g in d.get("overview", {}).get("guide", []))
    new_terms = sorted((used & glossary) - earlier)

    # ── numbers ──
    stats = summed([day_stats(d) for d in days])
    stats["per_day"] = [day_stats(d) for d in days]
    weeks = sorted({week_of(dt) for dt in topic_entry(tid)["dates"]})
    prev = weeks[weeks.index(week) - 1] if weeks.index(week) > 0 else None
    if prev:
        stats["prev"] = {"week": prev, **summed([day_stats(d) for d in load_days(tid, prev)])}

    def pick(x):
        dt, p = by[x["id"]]
        return {"date": dt, "why": x["why"], "paper": {k: v for k, v in p.items() if k != "abstract_en"}}

    out = {
        "topic": tid, "week": week, "dates": [d["date"] for d in days],
        "overview": {"lede": w.get("lede", "")},
        "picks": [pick(x) for x in picks],
        "themes": themes,
        "gems": [{"id": x["id"], "note": x["note"]} for x in gems],
        "stats": stats,
        "glossary_new": new_terms,
        # compact index of every relevant paper of the week: enough to list, link and colour it
        "papers": sorted(({**{k: p.get(k) for k in INDEX_KEYS}, "date": dt} for dt, p in by.values()),
                         key=lambda r: (r["date"], -bool(r["star"]), -(r["score"] or 0))),
    }
    dump(out, weekly_path(tid, week))

    tp = os.path.join(DATA, "topics.json")
    topics = load(tp)
    entry = next(t for t in topics["topics"] if t["id"] == tid)
    entry["weeks"] = sorted(set(entry.get("weeks", [])) | {week}, reverse=True)
    dump(topics, tp)

    for name, s, lim in [("lede", w.get("lede", ""), 260)] + [(f"theme 「{t['title']}」", "".join(t["body"]), 420) for t in themes]:
        n = len(REF.sub("X", TERM.sub("X", s)))
        if n > lim:
            print(f"WARNING: {name} is about {n} chars (limit {lim})")
    if not 3 <= len(picks) <= 5:
        print(f"note: {len(picks)} picks (usual range 3–5)")
    print(f"{week}: {len(days)} dailies, {stats['relevant']} relevant, {stats['stars']} ⭐ → "
          f"{len(picks)} picks, {len(themes)} themes, {len(gems)} gems; {len(new_terms)} new glossary terms")


if __name__ == "__main__":
    main(*sys.argv[1:4])
