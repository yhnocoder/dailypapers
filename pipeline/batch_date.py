"""Which arXiv batches (cutoff dates, US/Eastern) the daily run should process.

The daily task fires at 21:07 America/New_York, Sun–Thu, about an hour after arXiv's
20:00 ET announcement. Mon–Thu evenings announce that day's batch; Sunday evening
announces Friday's batch.

  python3 pipeline/batch_date.py                 latest batch that should be announced by now
  python3 pipeline/batch_date.py --pending       every weekday batch from the last 7 days that is
                                                 not in site/data/topics.json yet, oldest first
                                                 (catches up batches skipped for holidays or failed runs)
  … [--now YYYY-MM-DDTHH:MM] [--topic search-rec]
"""
import argparse, json, os
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

ET = ZoneInfo("America/New_York")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOOKBACK_DAYS = 7


def latest_batch(now_et: datetime) -> date:
    """Newest batch whose 20:00 ET announcement has passed (holidays aside)."""
    d = now_et.date()
    if now_et.time() < time(20, 0):
        d -= timedelta(days=1)  # tonight's announcement hasn't happened yet
    # announcements happen Sun–Thu evenings; Sunday's carries Friday's batch
    while True:
        wd = d.weekday()  # Mon=0 … Sun=6
        if wd in (0, 1, 2, 3):
            return d
        if wd == 6:
            return d - timedelta(days=2)
        d -= timedelta(days=1)  # Fri/Sat evening: nothing new, step back


def pending(now_et: datetime, done: set) -> list:
    last = latest_batch(now_et)
    out, d = [], last - timedelta(days=LOOKBACK_DAYS)
    newest_done = max((date.fromisoformat(x) for x in done), default=None)
    while d <= last:
        if d.weekday() < 5 and d.isoformat() not in done and (newest_done is None or d > newest_done):
            out.append(d)
        d += timedelta(days=1)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pending", action="store_true")
    ap.add_argument("--now")
    ap.add_argument("--topic", default="search-rec")
    a = ap.parse_args()
    now = datetime.fromisoformat(a.now).replace(tzinfo=ET) if a.now else datetime.now(ET)
    if not a.pending:
        print(latest_batch(now).isoformat())
        return
    topics = json.load(open(os.path.join(ROOT, "site", "data", "topics.json")))
    t = next((t for t in topics["topics"] if t["id"] == a.topic), {"dates": []})
    for d in pending(now, set(t["dates"])):
        print(d.isoformat())


if __name__ == "__main__":
    main()
