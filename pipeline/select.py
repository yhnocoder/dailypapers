"""Pick what an issue shows: the top `issue_cap` related papers, the rest folded.

  python3 pipeline/select.py topics/<topic>.json WORK <batch> [<batch> ...]

Writes WORK/selection.json:
  shown        ids shown in full (Chinese abstract), at most `issue_cap`, best first
  others       related papers that did not make the cut (shown folded, one line each)
  star_hint    shown papers Sonnet nominated for ⭐ (the main session decides)
and WORK/abstract_in.json: [{id, title, abstract}] of the shown papers, for the abstract agents.

Ranking = topic score + a small heat bonus (HF upvotes, HN points from the latest heat snapshot,
capped at +0.15). Diversity: first the best paper of each direction that scores ≥ 0.45 (at most
half of the slots), then the remaining slots by ranking.
"""
import json, math, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from heat import latest  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def heat_bonus(h):
    if not h:
        return 0.0
    hf = (h.get("hf") or {}).get("upvotes", 0)
    hn = max((x.get("points", 0) for x in h.get("hn", [])), default=0)
    return min(0.15, 0.04 * math.log2(1 + hf / 5) + 0.04 * math.log2(1 + hn / 20))


def main(topic_path, work, *batches):
    t = json.load(open(os.path.join(ROOT, topic_path)))
    tid, cap = t["id"], t["issue_cap"]
    heat = latest().get("papers", {})
    rel, seen = [], set()
    for b in batches:
        for p in json.load(open(os.path.join(ROOT, "site", "data", "papers", f"{b}.json")))["papers"]:
            if tid in p["tags"] and p["id"] not in seen:
                seen.add(p["id"])
                tag = p["tags"][tid]
                rel.append({"id": p["id"], "title": p["title"], "abstract": p["abstract"], "dir": tag["direction"],
                            "score": tag["score"], "star": tag["star_candidate"],
                            "rank": tag["score"] + heat_bonus(heat.get(p["id"]))})
    rel.sort(key=lambda x: -x["rank"])
    pick, dirs = [], set()
    for x in rel:
        if len(pick) >= cap // 2:
            break
        if x["dir"] not in dirs and x["dir"] != "Z" and x["score"] >= 0.45:
            dirs.add(x["dir"])
            pick.append(x)
    for x in rel:
        if len(pick) >= cap:
            break
        if x not in pick:
            pick.append(x)
    pick.sort(key=lambda x: -x["rank"])
    shown = [x["id"] for x in pick]
    sel = {"topic": tid, "batches": list(batches), "shown": shown,
           "others": [x["id"] for x in rel if x["id"] not in shown],
           "star_hint": [x["id"] for x in pick if x["star"]]}
    os.makedirs(work, exist_ok=True)
    json.dump(sel, open(os.path.join(work, "selection.json"), "w"), ensure_ascii=False, indent=1)
    json.dump([{k: x[k] for k in ("id", "title", "abstract")} for x in pick],
              open(os.path.join(work, "abstract_in.json"), "w"), ensure_ascii=False, indent=1)
    print(f"{tid} {batches}: {len(rel)} related → {len(shown)} shown, {len(sel['others'])} folded; "
          f"star hints {sel['star_hint']}")
    for x in pick:
        print(f"  {x['rank']:.2f} ({x['score']:.2f}) {x['dir']} {'★' if x['star'] else ' '} {x['id']} {x['title'][:70]}")


if __name__ == "__main__":
    main(*sys.argv[1:])
