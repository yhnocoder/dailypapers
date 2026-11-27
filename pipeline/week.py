"""Weekly digest helpers. A week is the Mon–Fri arXiv batches of one ISO week, e.g. 2026-W48.

  python3 pipeline/week.py --pending [--topic search-rec]
      Weeks that are closed and whose weekly is missing or was built from fewer dailies than
      exist now, oldest first. A week is closed once its Friday batch is in topics.json, or a
      batch from a later week is (batch_date.py never backfills behind the newest daily).

  python3 pipeline/week.py collect <YYYY-Www> WORK [--topic search-rec]
      Writes WORK/week.in.json: every relevant paper of the week in compact form (⭐ papers
      carry their analysis), plus per-day funnel numbers. This is what the weekly is written from.

  python3 pipeline/week.py show <YYYY-Www> <id> [<id> …] [--topic search-rec]
      Prints abstract_zh (and analysis, for ⭐) of the given papers, for a closer look.
"""
import argparse, json, os, sys
from datetime import date, timedelta

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "site", "data")


def load(p, default=None):
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else default


def week_of(day: str) -> str:
    y, w, _ = date.fromisoformat(day).isocalendar()
    return f"{y}-W{w:02d}"


def friday(week: str) -> date:
    y, w = week.split("-W")
    return date.fromisocalendar(int(y), int(w), 5)


def topic_entry(topic: str) -> dict:
    topics = load(os.path.join(DATA, "topics.json"), {"topics": []})
    return next((t for t in topics["topics"] if t["id"] == topic), {"id": topic, "dates": []})


def week_dates(topic: str, week: str) -> list:
    return sorted(d for d in topic_entry(topic)["dates"] if week_of(d) == week)


def weekly_path(topic: str, week: str) -> str:
    return os.path.join(DATA, topic, "weekly", f"{week}.json")


def load_days(topic: str, week: str) -> list:
    return [load(os.path.join(DATA, topic, f"{d}.json")) for d in week_dates(topic, week)]


def pending(topic: str) -> list:
    dates = topic_entry(topic)["dates"]
    if not dates:
        return []
    newest = date.fromisoformat(max(dates))
    out = []
    for wk in sorted({week_of(d) for d in dates}):
        if newest < friday(wk):
            continue  # still open
        have = (load(weekly_path(topic, wk)) or {}).get("dates")
        if have != week_dates(topic, wk):
            out.append(wk)
    return out


def collect(topic: str, week: str, work: str):
    days = load_days(topic, week)
    if not days:
        sys.exit(f"no dailies for {week}")
    papers = []
    for d in days:
        for p in d["papers"]:
            rec = {k: p.get(k) for k in ("id", "title", "title_zh", "direction", "star", "score", "affiliation", "summary_zh")}
            rec["date"] = d["date"]
            if p.get("links", {}).get("code"):
                rec["code"] = p["links"]["code"]
            if p.get("star"):
                rec["analysis"] = p.get("analysis", [])
                rec["star_reasons"] = p.get("star_reasons", [])
            papers.append(rec)
    out = {
        "week": week, "dates": [d["date"] for d in days],
        "days": [{"date": d["date"], "funnel": [n for _, n in d["funnel"]], "guide": d.get("overview", {}).get("guide", [])} for d in days],
        "papers": papers,
    }
    os.makedirs(work, exist_ok=True)
    with open(os.path.join(work, "week.in.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print(f"{week}: {len(days)} dailies, {len(papers)} relevant, {sum(bool(p['star']) for p in papers)} ⭐ → {work}/week.in.json")


def show(topic: str, week: str, ids: list):
    by = {p["id"]: (d["date"], p) for d in load_days(topic, week) for p in d["papers"]}
    for i in ids:
        if i not in by:
            print(f"## {i}: not in {week}\n")
            continue
        dt, p = by[i]
        print(f"## {i} · {dt} · {p['direction']} · {'⭐ ' if p.get('star') else ''}{p['title']}\n{p['title_zh']}\n\n{p.get('abstract_zh', '')}\n")
        for t in p.get("analysis", []):
            print(t + "\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pending", action="store_true")
    ap.add_argument("--topic", default="search-rec")
    ap.add_argument("args", nargs="*")
    a = ap.parse_args()
    if a.pending:
        print("\n".join(pending(a.topic)), end="\n" if pending(a.topic) else "")
    elif a.args[:1] == ["collect"] and len(a.args) == 3:
        collect(a.topic, a.args[1], a.args[2])
    elif a.args[:1] == ["show"] and len(a.args) >= 3:
        show(a.topic, a.args[1], a.args[2:])
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
