"""Which issues a topic's editor run should publish now.

  python3 pipeline/issue_plan.py --topic llm [--now YYYY-MM-DDTHH:MM] [--force]

Prints one JSON object per issue, oldest first: {"key": <last batch date>, "batches": [...]}.

A batch is "uncovered" for a topic when its pool exists (data/papers/<date>.json), it is
not earlier than the topic's `start_date` (and within the last 14 days), and no published issue
of the topic includes it (site/data/topics.json → issues). Using the set difference, a batch that
arXiv announced late (holidays) is picked up by the next issue instead of falling between ranges.

- daily topics (5 run days): one issue per uncovered batch
- other topics: on a run day (America/New_York weekday in `cadence.run_days`, counted until 06:00
  the next morning; or with --force),
  one issue covering every uncovered batch; nothing on other days
If the latest announced batch has no pool yet, a note goes to stderr (ingest still running or failed).
"""
import argparse, glob, json, os, sys
from datetime import date, datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from batch_date import ET, latest_batch  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def covered(topic_id):
    p = os.path.join(ROOT, "site", "data", "topics.json")
    t = next((t for t in json.load(open(p))["topics"] if t["id"] == topic_id), None) if os.path.exists(p) else None
    if not t:
        return set()
    issues = t.get("issues", {})
    return {b for k in t.get("dates", []) for b in issues.get(k, [k])}


def plan(topic_id, now, force=False):
    cfg = json.load(open(os.path.join(ROOT, "topics", f"{topic_id}.json")))
    last = latest_batch(now)
    lo = max(date.fromisoformat(cfg["start_date"]), last - timedelta(days=14)).isoformat()
    pools = {os.path.basename(p)[:-5] for p in glob.glob(os.path.join(ROOT, "data", "papers", "*.json"))}
    if last.isoformat() not in pools:
        print(f"note: no pool yet for the latest batch {last} (ingest still running or failed)", file=sys.stderr)
    todo = sorted(d for d in pools if lo <= d <= last.isoformat() and d not in covered(topic_id))
    if not todo:
        return []
    run_days = cfg["cadence"]["run_days"]
    if len(run_days) >= 5:
        return [{"key": d, "batches": [d]} for d in todo]
    # the run day is the evening the run was scheduled for: a run that slips past midnight
    # (late start, waiting for the ingest) still counts for that evening
    if force or DAYS[(now - timedelta(hours=6)).weekday()] in run_days:
        return [{"key": todo[-1], "batches": todo}]
    return []


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--topic", required=True)
    ap.add_argument("--now")
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()
    now = datetime.fromisoformat(a.now).replace(tzinfo=ET) if a.now else datetime.now(ET)
    for i in plan(a.topic, now, a.force):
        print(json.dumps(i))
