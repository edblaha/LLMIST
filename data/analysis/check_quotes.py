"""Check that every quote in the analysis JSON files appears word for word in its policy text.

Usage: python3 data/analysis/check_quotes.py [JSON ...]
       (default: data/analysis/findings/*.json and data/analysis/scores.json if present)

A quote record is any JSON object with a "quote" key. Its source file is the record's own
"file" key, or the nearest enclosing object's "file". eBay change records use
"old_quote"/"new_quote", checked against ebay_previous.txt and ebay.txt.

Results per quote:
  OK         exact substring of the stated line
  OK-MOVED   exact substring of the file, but not on the stated line (line number is wrong)
  NEAR       only matches after normalizing whitespace / curly quotes / dashes (not exact)
  MISSING    not in the file at all
Exit status is 1 if any quote is not OK.
"""
import glob
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
EBAY_CHANGE_FILES = {"old_quote": "data/text/ebay_previous.txt", "new_quote": "data/text/ebay.txt"}

_texts = {}


def text(path):
    if path not in _texts:
        with open(os.path.join(ROOT, path), encoding="utf-8") as f:
            _texts[path] = f.read()
    return _texts[path]


def normalize(s):
    s = s.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    s = s.replace("–", "-").replace("—", "-").replace(" ", " ")
    return re.sub(r"\s+", " ", s).strip()


def records(obj, src, inherited_file=None, path="$"):
    """Yield (source_json, record_path, id, file, quote, line) for every quote in obj."""
    if isinstance(obj, dict):
        file = obj.get("file", inherited_file)
        rid = obj.get("id", path)
        if isinstance(obj.get("quote"), str):
            yield src, path, rid, file, obj["quote"], obj.get("line")
        for key, tfile in EBAY_CHANGE_FILES.items():
            if isinstance(obj.get(key), str):
                yield src, path + "." + key, rid, tfile, obj[key], obj.get(key.replace("quote", "line"))
        for k, v in obj.items():
            if isinstance(v, (dict, list)):
                yield from records(v, src, file, f"{path}.{k}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from records(v, src, inherited_file, f"{path}[{i}]")


def check(file, quote, line):
    t = text(file)
    lines = t.split("\n")
    if isinstance(line, int) and 1 <= line <= len(lines) and quote in lines[line - 1]:
        return "OK", line
    if quote in t:
        return "OK-MOVED", t[: t.index(quote)].count("\n") + 1
    if normalize(quote) in normalize(t):
        return "NEAR", None
    return "MISSING", None


def main(paths):
    if not paths:
        paths = sorted(glob.glob(os.path.join(ROOT, "data/analysis/findings/*.json")))
        scores = os.path.join(ROOT, "data/analysis/scores.json")
        if os.path.exists(scores):
            paths.append(scores)
    counts, problems = {}, []
    for p in paths:
        with open(p, encoding="utf-8") as f:
            data = json.load(f)
        for src, rpath, rid, file, quote, line in records(data, os.path.relpath(p, ROOT)):
            if not file:
                status, found = "MISSING", None
                problems.append((src, rid, "(no file)", status, line, None, quote))
            else:
                status, found = check(file, quote, line)
                if status != "OK":
                    problems.append((src, rid, file, status, line, found, quote))
            counts[status] = counts.get(status, 0) + 1
    total = sum(counts.values())
    print(f"Checked {total} quotes in {len(paths)} files: " + ", ".join(f"{k}={v}" for k, v in sorted(counts.items())))
    for src, rid, file, status, line, found, quote in problems:
        where = f"stated line {line}" + (f", found at line {found}" if found else "")
        print(f"\n{status}  {src}  {rid}  {file}  ({where})\n    {quote[:200]}")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
