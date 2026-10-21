"""Score, rank and stress-test the platforms.

Reads data/analysis/scoring_spec.json (hand-assigned 0-3 scores citing finding ids) and the
findings files; writes
  data/analysis/scores.json  - every score with its evidence quotes (checked by check_quotes.py)
  data/analysis/ranking.md   - ranking table, dominance pairs, random-weights test, tiers
Weighted total = sum(weight * score) / (3 * sum(weights)) * 100, so 0 = least aggressive, 100 = most.
"""
import json
import os
import random

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
A = os.path.join(ROOT, "data/analysis")
N_RANDOM = 1000
SEED = 20261021


def load_findings(key):
    with open(os.path.join(A, "findings", key + ".json"), encoding="utf-8") as f:
        d = json.load(f)
    return d, {x["id"]: x for x in d["findings"]}


def total(scores, weights):
    return sum(weights[c] * s for c, s in scores.items()) / (3 * sum(weights.values())) * 100


def rank(platforms, weights, score_of):
    # alphabetical within ties only to make the order deterministic; tie_groups() undoes it
    return sorted(platforms, key=lambda p: (-total(score_of[p], weights), p))


def tie_groups(order, weights, score_of):
    """Split an ordered list into groups of platforms with equal totals: [(first_pos, last_pos, [platforms])]."""
    groups, i = [], 0
    while i < len(order):
        j = i
        t = round(total(score_of[order[i]], weights), 9)
        while j + 1 < len(order) and round(total(score_of[order[j + 1]], weights), 9) == t:
            j += 1
        groups.append((i, j, order[i:j + 1]))
        i = j + 1
    return groups


def thirds_shares(order, weights, score_of):
    """Fraction of each platform in the top/middle/bottom third. Tied platforms share the positions
    their tie group occupies equally, so a tie straddling a cut-off is split instead of broken arbitrarily."""
    n = len(order)
    cut1, cut2 = round(n / 3), round(2 * n / 3)
    band = ["top" if i < cut1 else "middle" if i < cut2 else "bottom" for i in range(n)]
    out = {}
    for a, b, ps in tie_groups(order, weights, score_of):
        k = b - a + 1
        share = {t: sum(band[i] == t for i in range(a, b + 1)) / k for t in ("top", "middle", "bottom")}
        for p in ps:
            out[p] = (share, (a + b) / 2 + 1)  # (third shares, average rank)
    return out


def main():
    with open(os.path.join(A, "scoring_spec.json"), encoding="utf-8") as f:
        spec = json.load(f)
    crit = [c["key"] for c in spec["criteria"]]
    weights = {c["key"]: c["weight"] for c in spec["criteria"]}
    names = {c["key"]: c["name"] for c in spec["criteria"]}

    out, score_of, display = [], {}, {}
    for key, cells in spec["scores"].items():
        doc, by_id = load_findings(key)
        display[key] = doc["platform"].replace(" (notice in force until Nov 25, 2026)", "")
        score_of[key] = {}
        rec = {"key": key, "platform": display[key], "file": doc["file"], "scores": {}}
        for c in crit:
            cell = cells[c]
            ev = []
            for fid in cell["evidence"]:
                fnd = by_id[fid]  # KeyError = spec cites a finding that doesn't exist
                ev.append({"id": fid, "claim": fnd["claim"], "quote": fnd["quote"], "line": fnd["line"],
                           "extra_quotes": fnd.get("extra_quotes", []), "context": fnd.get("context", "")})
            rec["scores"][c] = {"score": cell["score"], "why": cell["why"], "evidence": ev,
                                "not_stated_parts": cell.get("not_stated_parts", [])}
            score_of[key][c] = cell["score"]
        rec["total"] = round(total(score_of[key], weights), 1)
        out.append(rec)
    platforms = list(score_of)
    order = rank(platforms, weights, score_of)
    out.sort(key=lambda r: order.index(r["key"]))
    for a, b, ps in tie_groups(order, weights, score_of):  # tied platforms share the same rank
        for r in out:
            if r["key"] in ps:
                r["rank"] = a + 1
                r["tied"] = len(ps) > 1

    # (1) dominance: A >= B on every criterion and > on at least one -> A ranks above B under any weights
    dom = []
    for a in platforms:
        for b in platforms:
            if a != b and all(score_of[a][c] >= score_of[b][c] for c in crit) and any(score_of[a][c] > score_of[b][c] for c in crit):
                dom.append((a, b))
    identical = sorted({tuple(sorted((a, b))) for a in platforms for b in platforms
                        if a < b and score_of[a] == score_of[b]})

    # (2) random weights: uniform over the simplex (normalized exponentials)
    rng = random.Random(SEED)
    counts = {p: {"top": 0.0, "middle": 0.0, "bottom": 0.0} for p in platforms}
    rank_sum = {p: 0 for p in platforms}
    for _ in range(N_RANDOM):
        w = {c: rng.expovariate(1.0) for c in crit}
        o = rank(platforms, w, score_of)
        for p, (share, avg_rank) in thirds_shares(o, w, score_of).items():
            for t in share:
                counts[p][t] += share[t]
            rank_sum[p] += avg_rank

    def tier(p):
        c = counts[p]
        if c["top"] >= 0.6 * N_RANDOM:
            return "Highest"
        if c["bottom"] >= 0.6 * N_RANDOM:
            return "Lowest"
        return "Middle"

    # (3) alternative silence rules. No criterion is entirely unstated for any platform, so the
    # "not stated = 1 vs 0" rule changes nothing; instead test the parts that are silent on AI training.
    silent_ai = [k for k, cells in spec["scores"].items() if "AI training" in cells["uses"].get("not_stated_parts", [])]
    alt = {p: dict(s) for p, s in score_of.items()}
    for k in silent_ai:  # worst case: assume silence on AI training means they do it
        ads_personal = alt[k]["uses"] >= 2
        alt[k]["uses"] = 3 if ads_personal else 2
    alt_order = rank(platforms, weights, alt)
    fully_unstated = [(k, c) for k, cells in spec["scores"].items() for c in crit if cells[c].get("not_stated")]

    with open(os.path.join(A, "scores.json"), "w", encoding="utf-8") as f:
        json.dump({"weights": weights, "criteria": spec["criteria"], "not_stated_rule": spec["not_stated_rule"],
                   "platforms": out,
                   "stability": {"dominance": [{"higher": a, "lower": b} for a, b in dom],
                                 "identical_scores": [list(x) for x in identical],
                                 "random_weights": {"n": N_RANDOM, "seed": SEED,
                                                    "thirds": {p: {t: round(v, 1) for t, v in c.items()} for p, c in counts.items()},
                                                    "mean_rank": {p: round(rank_sum[p] / N_RANDOM, 2) for p in platforms}},
                                 "tiers": {p: tier(p) for p in platforms},
                                 "silent_ai_worst_case": {"platforms": silent_ai,
                                                          "order": alt_order,
                                                          "totals": {p: round(total(alt[p], weights), 1) for p in platforms}},
                                 "fully_unstated_cells": fully_unstated}},
                  f, ensure_ascii=False, indent=2)

    L = ["# Platform ranking: how aggressive is each privacy policy?", "",
         "Generated by `data/analysis/build_scores.py` from `data/analysis/scoring_spec.json`. "
         "Scores are 0-3 per criterion; weighted total is 0-100. Evidence quotes are in `data/analysis/scores.json`.", "",
         "## Criteria and weights", ""]
    for c in spec["criteria"]:
        L.append(f"- **{c['name']}** ({c['weight']}%): " + "; ".join(f"{k} = {v}" for k, v in c["rubric"].items()))
    L += ["", f"Not-stated rule: {spec['not_stated_rule']}", "", "## Ranking", "",
          "| Rank | Platform | Weighted total | " + " | ".join(f"{names[c]} ({weights[c]}%)" for c in crit) + " | Tier |",
          "|---|---|---|" + "---|" * len(crit) + "---|"]
    for r in out:
        L.append(f"| {r['rank']}{'=' if r['tied'] else ''} | {r['platform']} | {r['total']} | " + " | ".join(str(r['scores'][c]['score']) for c in crit)
                 + f" | {tier(r['key'])} |")
    L += ["", "## Stability", "", f"### Pairs that hold under any weights ({len(dom)})", "",
          "Platform on the left scores at least as high on every criterion and higher on at least one.", ""]
    by_hi = {}
    for a, b in dom:
        by_hi.setdefault(a, []).append(display[b])
    for a in order:
        if a in by_hi:
            L.append(f"- **{display[a]}** ≥ " + ", ".join(sorted(by_hi[a])))
    if identical:
        L += ["", "Identical scores on every criterion (always tied): " + "; ".join(" = ".join(display[x] for x in t) for t in identical)]
    L += ["", f"### {N_RANDOM} random weightings (seed {SEED})", "",
          "Share of weightings in which each platform lands in the top / middle / bottom third. Tied platforms split the positions they jointly occupy.", "",
          "| Platform | Top third | Middle third | Bottom third | Mean rank | Tier |", "|---|---|---|---|---|---|"]
    for p in sorted(platforms, key=lambda p: rank_sum[p]):
        c = counts[p]
        L.append(f"| {display[p]} | {c['top']/10:.1f}% | {c['middle']/10:.1f}% | {c['bottom']/10:.1f}% | {rank_sum[p]/N_RANDOM:.2f} | {tier(p)} |")
    L += ["", "Tier rule (relative to these 14 policies only): Highest if in the top third in at least 60% of weightings; Lowest if in the "
          "bottom third in at least 60%; otherwise Middle.", "",
          "### Silence checks", "",
          f"- Criteria a policy says nothing about at all: {len(fully_unstated)} cells, so scoring silence as 1 or 0 changes nothing.",
          f"- Silent on AI training: {', '.join(display[k] for k in silent_ai)}. Worst case (assume silence means they do it): "
          + ", ".join(f"{display[p]} {round(total(alt[p], weights), 1)}" for p in alt_order)]
    with open(os.path.join(A, "ranking.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(L) + "\n")
    print("\n".join(L[L.index("## Ranking"):]))


if __name__ == "__main__":
    main()
