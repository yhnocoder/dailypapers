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
papers of these batches that are not in the topic: one line each), funnel, overview.
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


def main(topic_path, key, work):
    topic = load(os.path.join(ROOT, topic_path))
    tid = topic["id"]
    sel = load(os.path.join(work, "selection.json"))
    batches = sel["batches"]
    if key != batches[-1]:
        sys.exit(f"key {key} must be the last batch of the issue ({batches[-1]})")
    pool, n_new, cats = {}, 0, set()
    for b in batches:
        P = load(os.path.join(ROOT, "data", "papers", f"{b}.json"))
        n_new += len(P["papers"])
        cats |= set(P["categories"])
        for p in P["papers"]:
            pool.setdefault(p["id"], {**p, "batch": b})
    abstracts = {x["id"]: x["abstract_zh"] for x in load(os.path.join(work, "abstracts.json"), [])}
    stars = {s["id"]: s for f in glob.glob(os.path.join(work, "star", "*.out.json")) for s in [load(f)]}
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
        p, s = pool[pid], stars.get(pid)
        tag = p["tags"][tid]
        rec = {"id": pid, "title": p["title"], "title_zh": p["title_zh"],
               "affiliation": (s or {}).get("affiliation") or p["affiliation"], "primary_cat": p["cat"],
               "direction": tag["direction"], "star": bool(s), "score": tag["score"],
               "links": {"abs": f"https://arxiv.org/abs/{pid}", "pdf": f"https://arxiv.org/pdf/{pid}",
                         "code": (s or {}).get("code") or p.get("code")},
               "summary_zh": p["summary_zh"], "abstract_zh": (s or {}).get("abstract_zh") or abstracts.get(pid, ""),
               "abstract_en": p["abstract"], "batch": p["batch"]}
        h = heat.get(pid)
        if h:
            rec["heat"] = {"hf": (h.get("hf") or {}).get("upvotes", 0),
                           "hn": max((x.get("points", 0) for x in h.get("hn", [])), default=0)}
        if s:
            rec.update(title_zh=s["title_zh"], analysis=s["analysis"], star_reasons=s.get("star_reasons", []))
            if s.get("figures"):
                rec["figures"] = s["figures"]
            t = translations.get(pid, {})
            if t.get("pdf"):
                rec["translation"] = {"pdf": t["pdf"], "zip": t.get("zip")}
            new_terms += s.get("glossary_new", [])
        if not rec["abstract_zh"]:
            warn.append(f"{pid}: no abstract_zh")
        papers.append(rec)
    papers.sort(key=lambda r: (-r["star"], -r["score"]))
    shown = set(sel["shown"])
    others = [line(pool[i]) for i in sel["others"]]
    excluded = [line(p) for p in pool.values() if tid not in p["tags"]]
    n_rel = len(shown) + len(others)
    span = label(batches[0]) if len(batches) == 1 else f"{batches[0]} – {batches[-1]}（{len(batches)} 批）"
    out = {
        "topic": tid, "date": key, "batches": batches, "batch": f"arXiv 公布批次 {span}",
        "rules_version": topic["rules_version"], "overview": load(os.path.join(work, "overview.json"), {}),
        "funnel": [[f"新论文（{len(cats)} 个 arXiv 分类全量 + HF / HN 热门补充）", n_new],
                   [f"判定{topic['name']}相关", n_rel], ["入选", len(papers)], ["⭐ 精读", sum(r["star"] for r in papers)]],
        "papers": papers, "others": others, "excluded": excluded,
    }
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

    gp = os.path.join(ROOT, "site", "data", "glossary.json")
    g = load(gp, {"terms": []})
    have, added = {t["id"] for t in g["terms"]}, []
    for t in new_terms:  # two write-ups may define the same new term
        if t.get("id") and t["id"] not in have:
            have.add(t["id"])
            added.append(t)
    g["terms"] += added
    dump(g, gp)
    for w in warn:
        print("WARNING", w)
    print(f"{tid} {key} ({len(batches)} batch): {n_new} new → {n_rel} related → {len(papers)} shown, "
          f"{sum(r['star'] for r in papers)} ⭐; {len(others)} folded; {len(excluded)} excluded; +{len(added)} glossary terms")


if __name__ == "__main__":
    main(*sys.argv[1:4])
