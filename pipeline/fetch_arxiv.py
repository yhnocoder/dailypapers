"""arXiv API helpers for pipeline/ingest.py.

window(D): submission window of batch D, from the previous batch's cutoff (14:00 ET) to D 14:00 ET.
Monday's batch covers Fri 14:00 → Mon 14:00; the batch after an arXiv holiday also covers the holiday.
"""
import os, re, sys, time, urllib.error, urllib.parse, urllib.request
import xml.etree.ElementTree as ET
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from batch_date import prev_batch  # noqa: E402

ET_TZ = ZoneInfo("America/New_York")
NS = {"a": "http://www.w3.org/2005/Atom", "x": "http://arxiv.org/schemas/atom"}
API = "https://export.arxiv.org/api/query"


MAX_RESULTS = 2000


def window(d: date):
    prev = prev_batch(d)
    to_utc = lambda x: datetime(x.year, x.month, x.day, 14, tzinfo=ET_TZ).astimezone(timezone.utc).strftime("%Y%m%d%H%M")
    return to_utc(prev), to_utc(d)


def query(q: str, id_list: str = ""):
    params = {"search_query": q, "max_results": MAX_RESULTS, "sortBy": "submittedDate"} if q else {"id_list": id_list, "max_results": 200}
    url = API + "?" + urllib.parse.urlencode(params)
    for attempt, wait in enumerate((15, 45, 90, 180, None)):
        try:
            with urllib.request.urlopen(url, timeout=120) as r:
                root = ET.fromstring(r.read())
            break
        except urllib.error.HTTPError as e:  # arXiv rate-limits bursts (429) and sometimes 503s
            if e.code not in (429, 503) or wait is None:
                raise
            print(f"arXiv API {e.code}, retrying in {wait}s", file=sys.stderr)
            time.sleep(wait)
    time.sleep(3)  # arXiv API etiquette
    clean = lambda s: re.sub(r"\s+", " ", s or "").strip()
    entries = root.findall("a:entry", NS)
    if q and len(entries) >= MAX_RESULTS:  # no paging: a full page means the result was cut off
        raise RuntimeError(f"arXiv query returned {len(entries)} results (the max): split the query further")
    for e in entries:
        aid = re.sub(r"v\d+$", "", e.find("a:id", NS).text.split("/abs/")[-1])
        c = e.find("x:comment", NS)
        comment = clean(c.text) if c is not None else ""
        abstract = clean(e.find("a:summary", NS).text)
        code = re.findall(r"https?://github\.com/[^\s,;)]+", comment + " " + abstract)
        yield {
            "id": aid,
            "title": clean(e.find("a:title", NS).text),
            "authors": [a.find("a:name", NS).text for a in e.findall("a:author", NS)][:6],
            "cat": e.find("x:primary_category", NS).get("term"),
            "cats": [x.get("term") for x in e.findall("a:category", NS)],
            "comment": comment,
            "abstract": abstract,
            "code": code[0].rstrip(".") if code else None,
        }

