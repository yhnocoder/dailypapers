"""Assemble one issue of a topic from the paper pool.

  python3 pipeline/assemble.py topics/<topic>.json <key> WORK

`key` is the issue's last batch date. WORK holds (produced by the issue run):
  selection.json      pipeline/select.py: batches, shown / others ids
  abstracts.json      [{id, abstract_zh}] for the shown papers (prompts/abstract.md)
  star/<id>.out.json  full-read write-ups for ⭐ papers (prompts/writing.md)
  overview.json       {"guide": [...]}                     (optional)
  translations.json   tongtu uploads (pipeline/upload_translations.py, optional)

Writes site/data/<topic>/<key>.json, records the issue (key → batches) in site/data/topics.json,
and merges new glossary terms into site/data/glossary.json.

Issue file: papers (shown, full), others (related but folded: one line each), excluded (pool
papers of these batches that are not related, i.e. untagged or below `min_score`: one line each), funnel, overview.
"""
import glob, json, os, sys
from datetime import date

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WK = "一二三四五六日"


def load(p, default=None):
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else default


def dump(obj, p):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1)
        f.write("\n")


def label(d):
    x = date.fromisoformat(d)
    return f"{d}（周{WK[x.weekday()]}）"


def record(p, tid, s, abstract_zh, h, t, tag=None):
    """One shown paper of an issue. p: pool paper (with `batch`); s: its ⭐ write-up (star/<id>.out.json) or None;
    h: its entry in the heat snapshot; t: its tongtu upload; tag: overrides the pool's tag for this topic (boost.py)."""
    pid, tag = p["id"], tag or p["tags"][tid]
    rec = {"id": pid, "title": p["title"], "title_zh": p["title_zh"],
           "affiliation": (s or {}).get("affiliation") or p["affiliation"], "primary_cat": p["cat"],
           "direction": tag["direction"], "star": bool(s), "score": tag["score"],
           "links": {"abs": f"https://arxiv.org/abs/{pid}", "pdf": f"https://arxiv.org/pdf/{pid}",
                     "code": (s or {}).get("code") or p.get("code")},
           "summary_zh": p["summary_zh"], "abstract_zh": (s or {}).get("abstract_zh") or abstract_zh,
           "abstract_en": p["abstract"], "batch": p["batch"]}
    if h:
        rec["heat"] = {"hf": (h.get("hf") or {}).get("upvotes", 0),
                       "hn": max((x.get("points", 0) for x in h.get("hn", [])), default=0)}
    if s:
        rec.update(title_zh=s["title_zh"], analysis=s["analysis"], star_reasons=s.get("star_reasons", []))
        if s.get("figures"):
            rec["figures"] = s["figures"]
        if t.get("pdf"):
            rec["translation"] = {"pdf": t["pdf"], "zip": t.get("zip")}
    return rec


def merge_glossary(new_terms):
    """Add the terms that are not in site/data/glossary.json yet; returns the ones added."""
    gp = os.path.join(ROOT, "site", "data", "glossary.json")
    g = load(gp, {"terms": []})
    have, added = {t["id"] for t in g["terms"]}, []
    for t in new_terms:  # two write-ups may define the same new term
        if t.get("id") and t["id"] not in have:
            have.add(t["id"])
            added.append(t)
    g["terms"] += added
    dump(g, gp)
    return added


def funnel(out, topic_name):
    """Refresh the counts of the related / shown / ⭐ rows from the issue's lists (row 0, the pool, stays)."""
    ps = out["papers"]
    out["funnel"][1:] = [[f"判定{topic_name}相关", len(ps) + len(out.get("others", []))], ["入选", len(ps)],
                         ["⭐ 精读", sum(r["star"] for r in ps)]]


def main(topic_path, key, work):
    topic = load(os.path.join(ROOT, topic_path))
    tid = topic["id"]
    sel = load(os.path.join(work, "selection.json"))
    batches = sel["batches"]
    if key != batches[-1]:
        sys.exit(f"key {key} must be the last batch of the issue ({batches[-1]})")
    pool, n_new, n_arxiv, cats = {}, 0, 0, set()
    for b in batches:
        P = load(os.path.join(ROOT, "data", "papers", f"{b}.json"))
        n_new += len(P["papers"])
        n_arxiv += P["n_arxiv"]
        cats |= set(P["categories"])
        for p in P["papers"]:
            pool.setdefault(p["id"], {**p, "batch": b})
    abstracts = {x["id"]: x["abstract_zh"] for x in load(os.path.join(work, "abstracts.json"), [])}
    stars = {s["id"]: s for f in glob.glob(os.path.join(work, "star", "*.out.json")) for s in [load(f)]}
    for i in stars:
        if i not in sel["shown"]:
            print(f"WARNING star/{i}.out.json is not a shown paper of this issue: ignored")
    translations = load(os.path.join(work, "translations.json"), {})
    heat = {}
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from heat import latest  # noqa: E402
    heat = latest().get("papers", {})

    def line(p):
        r = {"id": p["id"], "title": p["title"], "title_zh": p["title_zh"], "cat": p["cat"], "summary_zh": p["summary_zh"]}
        if tid in p["tags"]:
            r["direction"] = p["tags"][tid]["direction"]
        return r

    papers, new_terms, warn = [], [], []
    for pid in sel["shown"]:
        s = stars.get(pid)
        rec = record(pool[pid], tid, s, abstracts.get(pid, ""), heat.get(pid), translations.get(pid, {}))
        if s:
            new_terms += s.get("glossary_new", [])
        if not rec["abstract_zh"]:
            warn.append(f"{pid}: no abstract_zh")
        papers.append(rec)
    papers.sort(key=lambda r: (-r["star"], -r["score"]))
    shown = set(sel["shown"])
    others = [line(pool[i]) for i in sel["others"]]
    related = shown | set(sel["others"])  # below the topic's min_score counts as excluded
    excluded = [line(p) for p in pool.values() if p["id"] not in related]
    n_rel = len(shown) + len(others)
    span = label(batches[0]) if len(batches) == 1 else f"{batches[0]} – {batches[-1]}"
    out = {
        "topic": tid, "date": key, "batches": batches, "batch": f"arXiv 公布批次 {span}",
        "rules_version": topic["rules_version"], "overview": load(os.path.join(work, "overview.json"), {}),
        "funnel": [[f"新论文（{len(cats)} 个 arXiv 分类 {n_arxiv} 篇 + HF / HN 热门补充 {n_new - n_arxiv} 篇）", n_new]],
        "papers": papers, "others": others, "excluded": excluded,
    }
    funnel(out, topic["name"])
    dump(out, os.path.join(ROOT, "site", "data", tid, f"{key}.json"))

    tp = os.path.join(ROOT, "site", "data", "topics.json")
    topics = load(tp, {"topics": []})
    entry = next((t for t in topics["topics"] if t["id"] == tid), None)
    if not entry:
        entry = {"id": tid, "dates": []}
        topics["topics"].append(entry)
    entry.update(name=topic["name"], taxonomy_version=topic["taxonomy_version"], directions=topic["directions"])
    entry["dates"] = sorted(set(entry["dates"]) | {key}, reverse=True)
    entry.setdefault("issues", {})[key] = batches
    dump(topics, tp)

    added = merge_glossary(new_terms)
    for w in warn:
        print("WARNING", w)
    print(f"{tid} {key} ({len(batches)} batch): {n_new} new → {n_rel} related → {len(papers)} shown, "
          f"{sum(r['star'] for r in papers)} ⭐; {len(others)} folded; {len(excluded)} excluded; +{len(added)} glossary terms")


if __name__ == "__main__":
    main(*sys.argv[1:4])
