"""arXiv batch dates (cutoff dates, US/Eastern).

arXiv announces Sun–Thu at 20:00 ET. Mon–Thu evenings announce that day's batch; Sunday
evening announces Friday's batch. A batch dated D holds submissions from the previous
batch's cutoff (14:00 ET) up to D 14:00 ET.

On arXiv holidays (`no_announce` in topics/_ingest.json, e.g. Thanksgiving) there is no
announcement that evening; arXiv rolls those submissions into the next batch. We do the same:
a holiday is never a batch, and the next batch's window starts at the previous real batch.

  python3 pipeline/batch_date.py [--now YYYY-MM-DDTHH:MM]     latest batch announced by now
"""
import argparse, json, os
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

ET = ZoneInfo("America/New_York")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def holidays():
    p = os.path.join(ROOT, "topics", "_ingest.json")
    return set(json.load(open(p)).get("no_announce", [])) if os.path.exists(p) else set()


def is_batch(d: date) -> bool:
    return d.weekday() < 5 and d.isoformat() not in holidays()


def prev_batch(d: date) -> date:
    d -= timedelta(days=1)
    while not is_batch(d):
        d -= timedelta(days=1)
    return d


def latest_batch(now_et: datetime) -> date:
    """Newest batch whose 20:00 ET announcement has passed."""
    d = now_et.date()
    if now_et.time() < time(20, 0):
        d -= timedelta(days=1)  # tonight's announcement hasn't happened yet
    if d.weekday() == 6:
        d -= timedelta(days=2)  # Sunday evening announces Friday's batch
    while not is_batch(d):  # Fri/Sat evening, holidays: nothing new
        d -= timedelta(days=1)
    return d


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--now")
    a = ap.parse_args()
    now = datetime.fromisoformat(a.now).replace(tzinfo=ET) if a.now else datetime.now(ET)
    print(latest_batch(now).isoformat())
