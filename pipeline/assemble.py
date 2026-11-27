"""Assemble one day's digest JSON for the site.

Usage:
  python3 pipeline/assemble.py topics/search-rec.json 2026-11-24 WORKDIR

WORKDIR layout (produced by the daily run):
  all.json            fetched candidates (pipeline/fetch_arxiv.py)
  out/*.json          per-batch classification results (prompts/classify.md)
  star/<id>.out.json  full-read write-ups for ⭐ papers (prompts/writing.md)
  overview.json       {"guide": ["paragraph", ...]}   (optional)

Writes site/data/<topic>/<date>.json, adds the date to site/data/topics.json,
and merges new glossary entries into site/data/glossary.json.
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


def main(topic_path, day, work):
    topic = load(os.path.join(ROOT, topic_path))
    cands = {p["id"]: p for p in load(os.path.join(work, "all.json"))}
    cls = {x["id"]: x for f in sorted(glob.glob(os.path.join(work, "out", "*.json"))) for x in load(f)}
    missing = set(cands) - set(cls)
    if missing:
        sys.exit(f"{len(missing)} candidates have no classification, e.g. {sorted(missing)[:3]}")
    stars = {s["id"]: s for f in glob.glob(os.path.join(work, "star", "*.out.json")) for s in [load(f)]}
    translations = load(os.path.join(work, "translations.json"), {})

    papers, excluded, new_terms = [], [], []
    for pid, p in cands.items():
        c = cls[pid]
        if not c["relevant"]:
            excluded.append({"id": pid, "title": p["title"], "title_zh": c.get("title_zh", ""), "cat": p["cat"],
                             "summary_zh": c.get("summary_zh", ""), "reason": c.get("exclude_reason", "")})
            continue
        s = stars.get(pid)
        rec = {
            "id": pid, "title": p["title"], "title_zh": c["title_zh"],
            "affiliation": (s or {}).get("affiliation") or c.get("affiliation", ""),
            "primary_cat": p["cat"], "direction": c["direction"] or "Z",
            "star": bool(s), "score": c.get("score") or 0,
            "links": {"abs": f"https://arxiv.org/abs/{pid}", "pdf": f"https://arxiv.org/pdf/{pid}",
                      "code": (s or {}).get("code") or p.get("code")},
            "summary_zh": c.get("summary_zh", ""),
            "abstract_zh": (s or {}).get("abstract_zh") or c.get("abstract_zh", ""),
            "abstract_en": p["abstract"],
        }
        if s:
            rec.update(title_zh=s["title_zh"], analysis=s["analysis"], star_reasons=s.get("star_reasons", []))
            if s.get("figures"):
                rec["figures"] = s["figures"]
            t = translations.get(pid, {})
            if t.get("pdf"):
                rec["translation"] = {"pdf": t["pdf"], "zip": t.get("zip")}
            new_terms += s.get("glossary_new", [])
        papers.append(rec)

    papers.sort(key=lambda r: (-r["star"], -r["score"]))
    d = date.fromisoformat(day)
    src = " / ".join(c.replace("cs.", "") if i else c for i, c in enumerate(topic["full_categories"]))
    phr = " + ".join(f"{c} 短语过滤" for c in topic.get("phrase_categories", {}))
    out = {
        "topic": topic["id"], "date": day, "batch": f"arXiv 公布批次 {day}（周{WK[d.weekday()]}）",
        "rules_version": topic["rules_version"],
        "overview": load(os.path.join(work, "overview.json"), {}),
        "funnel": [[f"当日公布新论文（{src} 全量{' + ' + phr if phr else ''}）", len(cands)],
                   [f"判定{topic['name']}相关", len(papers)], ["⭐ 精读", sum(r["star"] for r in papers)]],
        "papers": papers, "excluded": excluded,
    }
    dump(out, os.path.join(ROOT, "site", "data", topic["id"], f"{day}.json"))

    tp = os.path.join(ROOT, "site", "data", "topics.json")
    topics = load(tp, {"topics": []})
    entry = next((t for t in topics["topics"] if t["id"] == topic["id"]), None)
    if not entry:
        entry = {"id": topic["id"], "dates": []}
        topics["topics"].append(entry)
    entry.update(name=topic["name"], taxonomy_version=topic["taxonomy_version"], directions=topic["directions"])
    entry["dates"] = sorted(set(entry["dates"]) | {day}, reverse=True)
    dump(topics, tp)

    gp = os.path.join(ROOT, "site", "data", "glossary.json")
    g = load(gp, {"terms": []})
    have = {t["id"] for t in g["terms"]}
    added = [t for t in new_terms if t.get("id") and t["id"] not in have]
    g["terms"] += added
    dump(g, gp)
    miss_sum = [e["id"] for e in excluded if not e["summary_zh"]] + [r["id"] for r in papers if not r["summary_zh"]]
    miss_abs = [r["id"] for r in papers if not r["abstract_zh"]]
    if miss_sum or miss_abs:
        print(f"WARNING: missing summary_zh {miss_sum}; missing abstract_zh {miss_abs} — fill them in WORK/out and re-run")
    print(f"{day}: {len(cands)} candidates → {len(papers)} relevant → {sum(r['star'] for r in papers)} ⭐; "
          f"{len(excluded)} excluded; +{len(added)} glossary terms")


if __name__ == "__main__":
    main(*sys.argv[1:4])
