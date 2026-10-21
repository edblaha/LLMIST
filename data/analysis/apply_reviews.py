"""Merge claim-review verdicts (data/analysis/review/<key>.json) into the findings files.

For each reviewed finding: records `review_verdict` and `review_reason`; replaces `claim` with
`corrected_claim` (keeping the old text as `claim_original`); adds reviewer `context`
(appended to any existing context); adds `extra_quotes`; drops the finding if `remove` is true
(recorded in the file's `removed` list). eBay change entries are matched by list index.
Idempotent: running it twice gives the same result.
"""
import glob
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FIND = os.path.join(ROOT, "data/analysis/findings")
REV = os.path.join(ROOT, "data/analysis/review")


def merge(item, r, claim_key):
    item["review_verdict"] = r["verdict"]
    item["review_reason"] = r.get("reason", "")
    if r.get("corrected_claim"):
        item.setdefault(f"{claim_key}_original", item[claim_key])
        item[claim_key] = r["corrected_claim"]
    ctx = (r.get("context") or "").strip()
    if ctx and ctx not in (item.get("context") or ""):
        item["context"] = ((item.get("context") or "").strip() + " " + ctx).strip()
    if r.get("extra_quotes"):
        item["extra_quotes"] = r["extra_quotes"]


def main():
    stats = {}
    for rp in sorted(glob.glob(os.path.join(REV, "*.json"))):
        key = os.path.splitext(os.path.basename(rp))[0]
        fp = os.path.join(FIND, key + ".json")
        with open(rp, encoding="utf-8") as f:
            rev = json.load(f)
        with open(fp, encoding="utf-8") as f:
            doc = json.load(f)
        if key == "ebay_changes":
            items = doc if isinstance(doc, list) else doc.get("changes", [])
            for r in rev["reviews"]:
                merge(items[int(r["id"])], r, "change")
                stats[r["verdict"]] = stats.get(r["verdict"], 0) + 1
        else:
            by_id = {f["id"]: f for f in doc["findings"]}
            for r in rev["reviews"]:
                if r["id"] not in by_id:
                    raise SystemExit(f"{key}: review for unknown id {r['id']}")
                merge(by_id[r["id"]], r, "claim")
                stats[r["verdict"]] = stats.get(r["verdict"], 0) + 1
                if r.get("remove"):
                    doc.setdefault("removed", []).append({"id": r["id"], "reason": r.get("reason", "")})
            gone = {x["id"] for x in doc.get("removed", [])}
            doc["findings"] = [f for f in doc["findings"] if f["id"] not in gone]
        with open(fp, "w", encoding="utf-8") as f:
            json.dump(doc, f, ensure_ascii=False, indent=2)
    print("applied reviews:", dict(sorted(stats.items())), "total", sum(stats.values()))


if __name__ == "__main__":
    main()
