"""Step 1 — collect public r/technology posts & comments via reddit's RSS/Atom feeds.

No auth required (reddit's .json endpoints 403 without OAuth). We pull a mix of
listings, search seeds, and comment threads so the dataset spans analyses, hot
takes, reactions and general discussion (not just top posts of one type).
Feeds carry no score or flair, so those fields are always None.

Output: data/raw_posts.json  (list of {id, type, text, subreddit, flair, score})
Re-runnable: existing entries are kept and only new ids are appended.
"""

from __future__ import annotations

import html
import json
import re
import sys
import time
import xml.etree.ElementTree as ET
from pathlib import Path

import requests

SUBREDDIT = "technology"
BASE = f"https://www.reddit.com/r/{SUBREDDIT}"
# reddit's API rules want a unique, non-spoofed UA: <platform>:<app>:<version> (by /u/<user>)
USER_AGENT = "python:takemeter:v0.1 (class project)"

OUT_PATH = Path(__file__).resolve().parents[1] / "data" / "raw_posts.json"

MIN_LEN = 15          # drop empty / extremely short items
MAX_LEN = 1000        # keep items as single concise posts/comments
TARGET = 500          # submissions; comments are collected on top (see COMMENT_THREADS)
REQUEST_DELAY = 5     # seconds between requests; unauthenticated feeds 429 quickly

# (listing, params, pages) — top is split by time window for variety.
LISTINGS = [
    ("hot", {}, 3),
    ("new", {}, 3),
    ("top", {"t": "week"}, 2),
    ("top", {"t": "month"}, 2),
]
SEARCH_SEEDS = ["AI", "layoffs", "privacy", "antitrust", "regulation", "Apple", "Tesla", "data breach", "social media", "Microsoft", "Google", "Facebook", "Twitter", "cybersecurity", "blockchain", "5G", "quantum computing", "cloud computing", "semiconductors", "renewable energy", "autonomous vehicles", "robotics", "virtual reality", "augmented reality", "internet of things", "machine learning", "deep learning", "natural language processing", "computer vision", "edge computing"]

COMMENT_THREADS = 40       # number of submissions to also pull comments from
COMMENTS_PER_THREAD = 15   # top-level comments per thread


def make_session() -> requests.Session:
    s = requests.Session()
    s.headers.update({"User-Agent": USER_AGENT})
    return s


ATOM = {"a": "http://www.w3.org/2005/Atom"}


def strip_html(raw: str) -> str:
    return html.unescape(re.sub(r"<[^>]+>", " ", raw))


def parse_feed(xml_text: str) -> list[dict]:
    """Atom entries -> {fullname, title, body, subreddit}. Link posts have an empty body."""
    out = []
    for e in ET.fromstring(xml_text).findall("a:entry", ATOM):
        content = e.findtext("a:content", "", ATOM)
        m = re.search(r'<div class="md">(.*?)</div>', content, re.S)
        cat = e.find("a:category", ATOM)
        out.append({
            "fullname": e.findtext("a:id", "", ATOM),
            "title": e.findtext("a:title", "", ATOM),
            "body": strip_html(m.group(1)) if m else "",
            "subreddit": cat.get("term") if cat is not None else SUBREDDIT,
        })
    return out


def get_feed(session: requests.Session, url: str, params: dict | None = None) -> list[dict] | None:
    """GET an Atom feed with backoff on 429/5xx. Returns entries or None on give-up."""
    delay = REQUEST_DELAY
    for attempt in range(5):
        try:
            resp = session.get(url, params=params, timeout=20)
        except requests.RequestException as e:
            print(f"  request error ({e}); retrying...", file=sys.stderr)
            time.sleep(delay)
            delay *= 2
            continue
        if resp.status_code == 200:
            time.sleep(REQUEST_DELAY)
            try:
                return parse_feed(resp.text)
            except ET.ParseError:
                print(f"  non-XML response from {url}", file=sys.stderr)
                return None
        if resp.status_code in (429, 500, 502, 503, 504):
            print(f"  HTTP {resp.status_code} from {url}; backing off {delay:.0f}s", file=sys.stderr)
            time.sleep(delay)
            delay *= 2
            continue
        print(f"  HTTP {resp.status_code} from {url}; skipping", file=sys.stderr)
        return None
    print(f"  gave up on {url}", file=sys.stderr)
    return None


def norm(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().lower()


def clean_text(raw: str) -> str | None:
    text = (raw or "").strip()
    if text in ("[deleted]", "[removed]", ""):
        return None
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) < MIN_LEN or len(text) > MAX_LEN:
        return None
    return text


def submission_text(entry: dict) -> str | None:
    """Prefer a substantive self-text body; otherwise the title (link posts)."""
    return clean_text(entry["body"]) or clean_text(entry["title"])


def add_item(items: dict, seen_text: set, _id: str, _type: str, text: str | None, data: dict) -> None:
    if text is None:
        return
    key = norm(text)
    if not key or key in seen_text or _id in items:
        return
    seen_text.add(key)
    items[_id] = {
        "id": _id,
        "type": _type,
        "text": text,
        "subreddit": data["subreddit"],
        "flair": None,
        "score": None,
    }


def add_submissions(items, seen_text, submission_ids, entries):
    for e in entries:
        if not e["fullname"].startswith("t3_"):
            continue
        sid = e["fullname"][3:]
        submission_ids.append(sid)
        add_item(items, seen_text, sid, "submission", submission_text(e), e)


def collect_listing(session, items, seen_text, submission_ids, listing, params, pages):
    after = None
    for page in range(pages):
        p = {"limit": 100, **params}
        if after:
            p["after"] = after
        print(f"[{listing} {params or ''} page {page + 1}]")
        entries = get_feed(session, f"{BASE}/{listing}.rss", p)
        if not entries:
            break
        add_submissions(items, seen_text, submission_ids, entries)
        after = entries[-1]["fullname"]


def collect_search(session, items, seen_text, submission_ids, seed):
    print(f"[search '{seed}']")
    entries = get_feed(
        session,
        f"{BASE}/search.rss",
        {"q": seed, "restrict_sr": 1, "sort": "new", "limit": 100},
    )
    if entries:
        add_submissions(items, seen_text, submission_ids, entries)


def collect_comments(session, items, seen_text, submission_id):
    entries = get_feed(session, f"{BASE}/comments/{submission_id}.rss", {"limit": 100})
    taken = 0
    # ponytail: feed has no depth, so replies are taken as well as top-level comments
    for e in entries or []:
        if taken >= COMMENTS_PER_THREAD:
            break
        if not e["fullname"].startswith("t1_"):
            continue
        text = clean_text(e["body"])
        before = len(items)
        add_item(items, seen_text, e["fullname"][3:], "comment", text, e)
        if len(items) > before:
            taken += 1


def main() -> None:
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    items: dict = {}
    seen_text: set = set()
    if OUT_PATH.exists():
        for it in json.loads(OUT_PATH.read_text(encoding="utf-8")):
            items[it["id"]] = it
            seen_text.add(norm(it["text"]))
        print(f"Resuming: {len(items)} existing items loaded.")

    session = make_session()
    submission_ids: list[str] = []

    for listing, params, pages in LISTINGS:
        collect_listing(session, items, seen_text, submission_ids, listing, params, pages)
        if len(items) >= TARGET:
            break

    if len(items) < TARGET:
        for seed in SEARCH_SEEDS:
            collect_search(session, items, seen_text, submission_ids, seed)
            if len(items) >= TARGET:
                break

    # de-dup submission ids while preserving order, then pull comment threads.
    unique_ids = list(dict.fromkeys(submission_ids))
    # ponytail: comments aren't capped by TARGET — headlines alone are almost all one label
    for sid in unique_ids[:COMMENT_THREADS]:
        print(f"[comments {sid}]")
        collect_comments(session, items, seen_text, sid)

    out = list(items.values())
    OUT_PATH.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")

    n_sub = sum(1 for x in out if x["type"] == "submission")
    n_com = sum(1 for x in out if x["type"] == "comment")
    print(f"\nSaved {len(out)} items to {OUT_PATH}  (submissions={n_sub}, comments={n_com})")


if __name__ == "__main__":
    main()
