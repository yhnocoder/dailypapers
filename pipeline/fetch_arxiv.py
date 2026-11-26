"""Fetch one arXiv announcement batch for a topic.

Usage: python3 pipeline/fetch_arxiv.py topics/search-rec.json 2026-11-24 out.json

arXiv announces on Sun–Thu evenings (US/Eastern); the batch shown on weekday D
contains submissions from the previous announcement cutoff (14:00 ET) up to D 14:00 ET.
Monday's batch therefore covers Fri 14:00 → Mon 14:00. Holidays are not handled.
"""
import json, re, sys, time, urllib.parse, urllib.request
import xml.etree.ElementTree as ET
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

ET_TZ = ZoneInfo("America/New_York")
NS = {"a": "http://www.w3.org/2005/Atom", "x": "http://arxiv.org/schemas/atom"}
API = "https://export.arxiv.org/api/query"


def window(d: date):
    prev = d - timedelta(days=3 if d.weekday() == 0 else 1)
    to_utc = lambda x: datetime(x.year, x.month, x.day, 14, tzinfo=ET_TZ).astimezone(timezone.utc).strftime("%Y%m%d%H%M")
    return to_utc(prev), to_utc(d)


def query(q: str):
    url = API + "?" + urllib.parse.urlencode({"search_query": q, "max_results": 2000, "sortBy": "submittedDate"})
    with urllib.request.urlopen(url, timeout=120) as r:
        root = ET.fromstring(r.read())
    time.sleep(3)  # arXiv API etiquette
    clean = lambda s: re.sub(r"\s+", " ", s or "").strip()
    for e in root.findall("a:entry", NS):
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


def main(topic_path, day, out_path):
    t = json.load(open(topic_path))
    a, b = window(date.fromisoformat(day))
    w = f"submittedDate:[{a} TO {b}]"
    papers = {}
    full = " OR ".join(f"cat:{c}" for c in t["full_categories"])
    for p in query(f"({full}) AND {w}"):
        papers[p["id"]] = p
    for cat, phrases in t.get("phrase_categories", {}).items():
        ph = " OR ".join(f'abs:"{x}"' if " " in x else f"abs:{x}" for x in phrases)
        for p in query(f"cat:{cat} AND ({ph}) AND {w}"):
            papers.setdefault(p["id"], p)
    json.dump(list(papers.values()), open(out_path, "w"), ensure_ascii=False, indent=0)
    print(f"{day}: window {a}–{b} UTC, {len(papers)} papers")


if __name__ == "__main__":
    main(*sys.argv[1:4])
