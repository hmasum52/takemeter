"""Step 1 (offline) — normalize browser-saved reddit JSON into the clean schema.

Because reddit's WAF blocks unauthenticated programmatic fetches from some
networks, the reliable path is: save raw reddit `.json` responses from your
browser into `data/raw/`, then run this to parse + clean them.

Accepts, for every `*.json` file under data/raw/:
  - a listing page  {"kind":"Listing","data":{"children":[{"kind":"t3"|"t1",...}]}}
  - a comment thread [ <listing of t3>, <listing of t1 comments> ]
(both shapes, in any mix, are handled.)

Output: data/raw_posts.json  (list of {id, type, text, subreddit, flair, score})
Merges with any existing output and de-dups, so it is safe to re-run as you add files.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
OUT_PATH = ROOT / "data" / "raw_posts.json"

MIN_LEN = 15
MAX_LEN = 1000


def norm(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().lower()


def clean_text(raw: str | None) -> str | None:
    text = (raw or "").strip()
    if text in ("[deleted]", "[removed]", ""):
        return None
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) < MIN_LEN or len(text) > MAX_LEN:
        return None
    return text


def submission_text(d: dict) -> str | None:
    selftext = clean_text(d.get("selftext", ""))
    return selftext if selftext else clean_text(d.get("title", ""))


def iter_children(payload):
    """Yield child nodes from a listing dict or a comment-thread list."""
    if isinstance(payload, dict) and payload.get("kind") == "Listing":
        yield from payload.get("data", {}).get("children", [])
    elif isinstance(payload, list):
        for part in payload:
            if isinstance(part, dict) and part.get("kind") == "Listing":
                yield from part.get("data", {}).get("children", [])


def add(items: dict, seen: set, _id: str, _type: str, text: str | None, d: dict) -> None:
    if text is None:
        return
    key = norm(text)
    if not key or key in seen or _id in items:
        return
    seen.add(key)
    items[_id] = {
        "id": _id,
        "type": _type,
        "text": text,
        "subreddit": d.get("subreddit", "soccer"),
        "flair": d.get("link_flair_text"),
        "score": d.get("score"),
    }


def main() -> None:
    if not RAW_DIR.exists():
        print(f"Create {RAW_DIR} and drop browser-saved reddit .json files there.", file=sys.stderr)
        sys.exit(1)

    items: dict = {}
    seen: set = set()
    if OUT_PATH.exists():
        existing = json.loads(OUT_PATH.read_text(encoding="utf-8"))
        # ignore a raw listing accidentally left at the output path
        if isinstance(existing, list) and all(isinstance(x, dict) and "text" in x for x in existing):
            for x in existing:
                items[x["id"]] = x
                seen.add(norm(x["text"]))

    files = sorted(RAW_DIR.glob("*.json"))
    if not files:
        print(f"No .json files in {RAW_DIR}.", file=sys.stderr)
        sys.exit(1)

    for f in files:
        try:
            payload = json.loads(f.read_text(encoding="utf-8"))
        except (ValueError, OSError) as e:
            print(f"  skip {f.name}: {e}", file=sys.stderr)
            continue
        before = len(items)
        for child in iter_children(payload):
            kind = child.get("kind")
            d = child.get("data", {})
            if not d:
                continue
            if kind == "t3" and not d.get("stickied"):
                add(items, seen, d["id"], "submission", submission_text(d), d)
            elif kind == "t1":
                add(items, seen, d["id"], "comment", clean_text(d.get("body", "")), d)
        print(f"  {f.name}: +{len(items) - before} new")

    out = list(items.values())
    OUT_PATH.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")

    n_sub = sum(1 for x in out if x["type"] == "submission")
    n_com = sum(1 for x in out if x["type"] == "comment")
    print(f"\nWrote {len(out)} cleaned items to {OUT_PATH}  (submissions={n_sub}, comments={n_com})")
    if len(out) < 200:
        print(f"NOTE: {len(out)} < 200 target — add more saved pages/threads to data/raw/ and re-run.")


if __name__ == "__main__":
    main()
