"""Boost a paper of a published issue: move it into the shown papers, or make it a ⭐.

  python3 pipeline/boost.py prepare <topic> <key> <arxiv_id> <shown|star> WORK
                                    [--direction X] [--note-file F] [--issue N] [--comment ID]
  python3 pipeline/boost.py apply WORK

One WORK directory per issue (topic + key); run prepare once per paper, then apply once.
An issue's WORK directory is gone once it is published, so a boost patches
site/data/<topic>/<key>.json in place instead of re-running assemble.py. The paper must be in the
issue already (shown, folded under「其他相关」, or「未收录」), i.e. in the pool of the issue's batches.

prepare  checks the request and writes
  WORK/boost.json          the issue and its requests: id, level, where the paper was, direction, score, note
  WORK/abstract_in.json    [{id, title, abstract}] when the paper has no Chinese abstract yet (prompts/abstract.md)
  WORK/star/<id>.in.json   level star: input of the full-read agent (prompts/writing.md); `reader_note` is
                           what the reader said about the paper when asking for the boost
apply    reads, next to boost.json,
  WORK/abstracts.json      [{id, abstract_zh}]              (when abstract_in.json was written)
  WORK/star/<id>.out.json  the ⭐ write-up                  (level star)
  WORK/translations.json   pipeline/upload_translations.py  (optional)
  WORK/overview.json       {"guide": [...]}: the rewritten guide (optional; the old one stays without it)
and updates the issue file, site/data/glossary.json and the boost log data/boosts.jsonl.

A paper without a tag for the topic (it was「未收录」because nobody tagged it) has no direction:
pass --direction with one of the topic's direction codes. Its score is the topic's `min_score`.
"""
import argparse, json, os, sys
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from assemble import ROOT, dump, funnel, load, merge_glossary, record  # noqa: E402
from heat import latest  # noqa: E402

MIN_SCORE = 0.45  # default of the topic config's `min_score`, as in select.py
LOG = os.path.join(ROOT, "data", "boosts.jsonl")


def issue_path(tid, key):
    return os.path.join(ROOT, "site", "data", tid, f"{key}.json")


def load_issue(tid, key):
    issue = load(issue_path(tid, key)) or sys.exit(f"no issue {tid} {key}")
    issue.setdefault("batches", [key])  # issues published before an issue could span batches
    return issue


def find(issue, pid):
    for where in ("papers", "others", "excluded"):
        for i, p in enumerate(issue.get(where, [])):
            if p["id"] == pid:
                return where, i
    return None, None


def pool_paper(issue, pid):
    for b in issue["batches"]:
        for p in load(os.path.join(ROOT, "data", "papers", f"{b}.json"))["papers"]:
            if p["id"] == pid:
                return {**p, "batch": b}
    sys.exit(f"{pid} is not in the pool of {issue['batches']}")


def prepare(a):
    topic = load(os.path.join(ROOT, "topics", f"{a.topic}.json")) or sys.exit(f"no topic {a.topic}")
    tid = topic["id"]
    issue = load_issue(tid, a.key)
    bp = os.path.join(a.work, "boost.json")
    job = load(bp, {"topic": tid, "key": a.key, "requests": []})
    if (job["topic"], job["key"]) != (tid, a.key):
        sys.exit(f"{a.work} already holds boosts for {job['topic']} {job['key']}: use one WORK per issue")
    where, i = find(issue, a.id)
    if not where:
        sys.exit(f"{a.id} is not in {tid} {a.key}: only papers of the issue's batches {issue['batches']} can be boosted")
    cur = issue[where][i] if where == "papers" else None
    if cur and (a.level == "shown" or cur["star"]):
        sys.exit(f"{a.id} is already {'a ⭐' if cur['star'] else 'shown'} in {tid} {a.key}: nothing to do")
    p = pool_paper(issue, a.id)
    tag = p["tags"].get(tid)
    direction = a.direction or (tag or {}).get("direction")
    if direction not in [d["code"] for d in topic["directions"]]:
        sys.exit(f"{a.id} has no direction for {tid}: pass --direction, one of "
                 + ", ".join(f"{d['code']} {d['name']}" for d in topic["directions"]))
    req = {"id": a.id, "level": a.level, "from": {"papers": "shown"}.get(where, where),
           "direction": direction, "score": tag["score"] if tag else topic.get("min_score", MIN_SCORE),
           "note": open(a.note_file, encoding="utf-8").read().strip() if a.note_file else "",
           "issue": a.issue, "comment": a.comment}
    job["requests"] = [r for r in job["requests"] if r["id"] != a.id] + [req]
    os.makedirs(os.path.join(a.work, "star"), exist_ok=True)
    dump(job, bp)
    ins = [x for x in load(os.path.join(a.work, "abstract_in.json"), []) if x["id"] != a.id]
    if not cur:
        ins.append({k: p[k] for k in ("id", "title", "abstract")})
    dump(ins, os.path.join(a.work, "abstract_in.json"))
    sp = os.path.join(a.work, "star", f"{a.id}.in.json")
    if a.level == "star":
        name = next(d["name"] for d in topic["directions"] if d["code"] == direction)
        dump({**{k: v for k, v in p.items() if k != "tags"}, "abstract_zh": (cur or {}).get("abstract_zh", ""),
              "direction": f"{direction} {name}", "headline": False, "reader_note": req["note"]}, sp)
    elif os.path.exists(sp):
        os.remove(sp)
    print(f"{tid} {a.key} {a.id}: {req['from']} → {a.level}, direction {direction}, score {req['score']:.2f}"
          + ("" if cur else "; needs abstract_zh (abstract_in.json)")
          + (f"; full read star/{a.id}.in.json" if a.level == "star" else ""))
    print(f"  {p['title']}")
    print(f"  the issue has {len(issue['papers'])} shown, {sum(r['star'] for r in issue['papers'])} ⭐ "
          f"(config: cap {topic['issue_cap']}, ⭐ {topic['stars']}); {len(job['requests'])} boost(s) prepared in {a.work}")


def apply(a):
    job = load(os.path.join(a.work, "boost.json")) or sys.exit("no boost.json: run prepare first")
    tid, key = job["topic"], job["key"]
    topic = load(os.path.join(ROOT, "topics", f"{tid}.json"))
    issue = load_issue(tid, key)
    abstracts = {x["id"]: x["abstract_zh"] for x in load(os.path.join(a.work, "abstracts.json"), [])}
    translations = load(os.path.join(a.work, "translations.json"), {})
    heat = latest().get("papers", {})
    log = [json.loads(x) for x in open(LOG, encoding="utf-8")] if os.path.exists(LOG) else []
    new_terms, done = [], []
    for req in job["requests"]:  # check everything before the issue file is touched
        pid = req["id"]
        where, i = find(issue, pid)
        cur = issue[where][i] if where == "papers" else None
        s = load(os.path.join(a.work, "star", f"{pid}.out.json"))
        if req["level"] == "star" and not s:
            sys.exit(f"no star/{pid}.out.json: the ⭐ write-up is missing (to give up on this ⭐, prepare it again as shown)")
        if req["level"] == "shown" and s:
            sys.exit(f"star/{pid}.out.json exists but {pid} was prepared as shown")
        p = pool_paper(issue, pid)
        rec = record(p, tid, s, (cur or {}).get("abstract_zh") or abstracts.get(pid, ""), heat.get(pid),
                     translations.get(pid, {}), tag={"direction": req["direction"], "score": req["score"]})
        if not rec["abstract_zh"]:
            sys.exit(f"{pid}: no abstract_zh (WORK/abstracts.json)")
        rec["boosted"] = req["level"]
        done.append((where, pid, rec))
        new_terms += (s or {}).get("glossary_new", [])
        log = [x for x in log if (x["topic"], x["key"], x["id"], x["level"]) != (tid, key, pid, req["level"])]
        log.append({"date": date.today().isoformat(), "topic": tid, "key": key, **req, "title": p["title"]})
    for where, pid, rec in done:
        issue[where] = [x for x in issue[where] if x["id"] != pid]
        issue["papers"].append(rec)
    issue["papers"].sort(key=lambda r: (-r["star"], -r["score"]))
    ov = load(os.path.join(a.work, "overview.json"))
    if ov:
        issue["overview"] = ov
    else:
        print("WARNING no overview.json: the guide is unchanged and does not mention the boosted papers")
    funnel(issue, topic["name"])
    dump(issue, issue_path(tid, key))
    added = merge_glossary(new_terms)
    with open(LOG, "w", encoding="utf-8") as f:
        f.writelines(json.dumps(x, ensure_ascii=False) + "\n" for x in log)
    for where, pid, rec in done:
        print(f"{tid} {key} {pid}: {'shown' if where == 'papers' else where} → {rec['boosted']}"
              + ("" if not rec["star"] else "; translation" if rec.get("translation") else "; no translation"))
    print(f"{tid} {key}: " + ", ".join(f"{n} {v}" for n, v in issue["funnel"][1:]) + f"; +{len(added)} glossary terms")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    x = sub.add_parser("prepare")
    x.add_argument("topic"), x.add_argument("key"), x.add_argument("id")
    x.add_argument("level", choices=["shown", "star"]), x.add_argument("work")
    x.add_argument("--direction"), x.add_argument("--note-file")
    x.add_argument("--issue", type=int, help="number of the GitHub issue the request came from")
    x.add_argument("--comment", type=int, help="id of the GitHub comment the request came from")
    x = sub.add_parser("apply")
    x.add_argument("work")
    a = ap.parse_args()
    {"prepare": prepare, "apply": apply}[a.cmd](a)
