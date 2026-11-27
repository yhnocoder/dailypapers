"""Print the arXiv batch (cutoff date, US/Eastern) the daily run should process.

The daily task fires at 21:07 America/New_York, Sun–Thu, about an hour after arXiv's
20:00 ET announcement. Mon–Thu evenings announce that day's batch; Sunday evening
announces Friday's batch.

Usage: python3 pipeline/batch_date.py [YYYY-MM-DDTHH:MM]   (default: now)
"""
import sys
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

ET = ZoneInfo("America/New_York")


def batch_for(now_et: datetime):
    d = now_et.date()
    wd = d.weekday()  # Mon=0 … Sun=6
    if wd == 6:
        return d - timedelta(days=2)  # Sunday evening → Friday's batch
    if wd in (4, 5):
        raise SystemExit(f"{d} is a {now_et:%A}: arXiv announces nothing on Friday/Saturday evenings")
    return d


if __name__ == "__main__":
    now = datetime.fromisoformat(sys.argv[1]).replace(tzinfo=ET) if len(sys.argv) > 1 else datetime.now(ET)
    print(batch_for(now).isoformat())
