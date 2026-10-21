"""Build what-your-apps-know.html from the reviewed findings and scores.

Every quote on the page is pulled from data/analysis/findings/*.json (or, for the few
quotes taken straight from a policy, from data/text/ by line), and all of them are written to
data/analysis/page_quotes.json so check_quotes.py verifies the page itself.
"""
import csv
import html
import json
import os
import re
from urllib.parse import quote as urlquote

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
A = os.path.join(ROOT, "data/analysis")
OUT = os.path.join(ROOT, "what-your-apps-know.html")
TITLE = "What Your Apps Know About You (and Didn't Tell You)"

# ---------------------------------------------------------------- page content
# Each item: a plain-language line written for the page, backed by finding ids (their main quote
# and, where listed, specific extra quotes) or by a direct {file, line, quote}.
HEADLINES = [
    {"id": "no-account", "title": "You can be tracked without ever signing up",
     "why": "Most people assume a privacy policy only matters once they create an account.",
     "items": [
         {"text": "Meta gets information from partners and vendors about what you do on other sites and apps, even if you're logged out or don't have an account.",
          "f": "meta-12", "extra": [119]},
         {"text": "X says that when you use it without signing in, it may work out who you are from what it collects.", "f": "x-09"},
         {"text": "Outside Europe and Switzerland, LinkedIn says it collects information about your device even where you haven't used LinkedIn, or relies on others, including Microsoft, to collect it.", "f": "linkedin-05"},
     ]},
    {"id": "unposted", "title": "Things you never posted or searched can still be collected",
     "why": "A draft you deleted, or a search you never ran, feels like it never happened.",
     "items": [
         {"text": "TikTok may collect a video when you create or import it, whether or not you save or publish it.", "f": "tiktok-01"},
         {"text": "X's records can include search terms you typed but didn't submit.", "f": "x-05"},
     ]},
    {"id": "incognito", "title": "Private browsing doesn't hide you from Google",
     "why": "Many people think Incognito mode makes them invisible online. It only hides your history from other people using the same device.",
     "items": [
         {"text": "Google says sites and apps that use its services still send it information when you visit them in Chrome's Incognito mode.", "f": "google-08"},
     ]},
    {"id": "location", "title": "Sharing your location for one thing can feed advertising",
     "why": "People turn on location to get a better forecast. Few expect the same permission to place them in an ad audience.",
     "items": [
         {"text": "The Weather Company asks to use your precise GPS location for better forecasts, and only with your consent.",
          "q": {"file": "data/text/weather.txt", "line": 199, "quote": "For more precise forecasts, we may use your specific GPS location (precise location), but only if you first give us consent."}},
         {"text": "In its California section, it says it may also use that precise location, or give it to data vendors, to sort people into audience groups.", "f": "weather-50"},
         {"text": "In the same section, it says you are opted in to this use by default and have to opt out.", "f": "weather-52"},
         {"text": "It says that in the past year it sold or shared precise location data with its advertising vendors.", "f": "weather-30", "extra": [469], "main": True},
     ]},
    {"id": "guesses", "title": "They guess things about you that you never told them",
     "why": "Your pay, age, gender and money habits can be estimated or bought, then used to pick the ads you see.",
     "items": [
         {"text": "LinkedIn says that to target ads it may use your job title to guess your pay bracket, graduation dates to guess your age, and your first name or pronouns to guess your gender.", "f": "linkedin-07", "extra": [141]},
         {"text": "The Weather Company buys extra details about you from data providers, including your spending and purchases and your home address, and uses them for targeted advertising.", "f": "weather-11", "extra": [185, 188, 189]},
         {"text": "Amazon may get your credit history from credit bureaus.", "f": "amazon-09"},
     ]},
    {"id": "ai", "title": "Your posts, chats and activity can train AI, and few policies say how to stop it",
     "why": "Most people never agreed to help build AI products, and only 2 of these 14 policies describe any way to say no.",
     "items": [
         {"text": "Meta lists developing AI “for Meta Products and for third parties” as a use of your information, and says what you exchange with its AI features can be part of it.", "f": "meta-26", "also": ["meta-28"]},
         {"text": "X says some companies it shares data with may use it to train their own AI models, unless you opt out.", "f": "x-21"},
         {"text": "LinkedIn says it may use your personal data to develop and train AI models.", "f": "linkedin-23"},
     ],
     "more": "ai-table"},
    {"id": "body", "title": "Your face, your voice and how you move in a store can be collected",
     "why": "Faces and voices can identify you for life. You can change a password, but not your face.",
     "items": [
         {"text": "TikTok may collect faceprints and voiceprints from your videos, and says it will ask permission where the law requires it.", "f": "tiktok-39"},
         {"text": "X says it may collect and use your biometric information, with your consent.", "f": "x-44"},
         {"text": "Amazon's physical stores may use cameras and computer vision to gather information about what you do in the store.", "f": "amazon-36", "extra": [23], "extra_only": True},
         {"text": "Google says outside contractors listen to samples of saved audio to improve its speech recognition.", "f": "google-22"},
     ]},
    {"id": "sell", "title": "“We don't sell your data” can still mean your data goes to advertisers",
     "why": "“Sell” has a narrow meaning in these policies. Sharing your data for ads can still happen, and some state laws count that as selling.",
     "items": [
         {"text": "Strava says it does not sell personal information “for monetary value”, then says it may have shared identifiers and online activity for ads in ways some state laws call “selling” or “sharing”, including with ad publishers such as Meta.", "f": "strava-25", "also": ["strava-26", "strava-27"]},
         {"text": "Meta says it never sells your information. It does share your device identifier with marketing vendors to show you its ads.", "f": "meta-34", "also": ["meta-31"]},
         {"text": "The Weather Company lets ad vendors use your information for their own purposes too, and in its California section says you are opted in to the sale or sharing of your data by default.", "f": "weather-29", "also": ["weather-40"]},
     ]},
    {"id": "delete", "title": "Deleting your account doesn't delete everything",
     "why": "People expect “delete account” to mean their posts and activity disappear too.",
     "items": [
         {"text": "On Reddit, your posts, comments and messages stay visible after you delete your account unless you delete each one first.", "f": "reddit-27"},
         {"text": "Wikipedia accounts can't be deleted once created, though you can usually hide what's on your user page.", "f": "wikipedia-24"},
         {"text": "On Strava, public segments and routes you created stay available after you delete your account.", "f": "strava-30"},
     ]},
    {"id": "optout", "title": "Opting out can take many separate steps",
     "why": "One “no” rarely covers everything. Each browser, device, app and partner can need its own.",
     "items": [
         {"text": "Without an account, The Weather Company says you have to opt out separately on every browser and device you use.", "f": "weather-41"},
         {"text": "In its mobile apps, you manage the opt-out for each app separately.", "f": "weather-46"},
         {"text": "Reddit sends you to a separate Google Analytics browser add-on, plus separate opt-outs for Nielsen and Quantcast.", "f": "reddit-38"},
     ]},
]

AI_TABLE = [
    ("amazon", ("yes", "Yes", ["amazon-17"]), ("none", "Not mentioned", [])),
    ("duckduckgo", ("none", "Not mentioned", []), ("none", "Not mentioned", [])),
    ("ebay_previous", ("yes", "Yes, for its own and other companies' AI models it uses", ["ebay_previous-24"]), ("some", "A right to object; no setting described", ["ebay_previous-44"])),
    ("espn", ("none", "Not mentioned", []), ("none", "Not mentioned", [])),
    ("github", ("yes", "Yes", ["github-16"]), ("none", "Not mentioned", [])),
    ("google", ("may", "Public web data; contractors review samples of saved audio", ["google-21", "google-22"]), ("none", "Not mentioned", [])),
    ("linkedin", ("may", "May", ["linkedin-23"]), ("no", "“Depends on your settings”; no AI opt-out named", ["linkedin-41"])),
    ("meta", ("yes", "Yes, including for third parties", ["meta-26", "meta-28"]), ("no", "No specific opt-out described", [])),
    ("reddit", ("none", "Not mentioned (it does license content to other companies)", ["reddit-18"]), ("none", "Not mentioned", [])),
    ("strava", ("yes", "Yes", ["strava-18"]), ("some", "Links to your choices", ["strava-36"])),
    ("tiktok", ("yes", "Yes, machine-learning models", ["tiktok-20"]), ("none", "Not mentioned", [])),
    ("weather", ("yes", "Yes", ["weather-23", "weather-24"]), ("no", "No opt-out described for its own AI", [])),
    ("wikipedia", ("none", "Not mentioned", []), ("none", "Not mentioned", [])),
    ("x", ("may", "May, and partners may train their own", ["x-20", "x-21"]), ("no", "Only for partners' use (“if you do not opt out”); none for X's own AI", ["x-39"])),
]

EBAY_CHANGES = [  # indexes into ebay_changes.json, with page wording
    (3, "Drops the promise to tell you when an AI system is dealing with you directly."),
    (4, "Drops the promise to notify registered users of major changes by message or email. Changes take effect when posted."),
    (2, "Adds that in some places, the data used to train its AI “is not considered personal data”."),
    (5, "Extends face and other biometric checks from sellers to identity checks generally, including verifying your age."),
]


# ---------------------------------------------------------------- data access
def jload(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


FIND = {}
for p in os.listdir(os.path.join(A, "findings")):
    d = jload(os.path.join(A, "findings", p))
    if isinstance(d, dict) and "findings" in d:
        for f in d["findings"]:
            FIND[f["id"]] = dict(f, file=d["file"], key=d["key"])
CHANGES = jload(os.path.join(A, "findings/ebay_changes.json"))
SCORES = jload(os.path.join(A, "scores.json"))
TEXT_LINES = {}


def text_line(file, line):
    if file not in TEXT_LINES:
        with open(os.path.join(ROOT, file), encoding="utf-8") as f:
            TEXT_LINES[file] = f.read().split("\n")
    return TEXT_LINES[file][line - 1]


SRC = {}
with open(os.path.join(ROOT, "data/sources.csv"), encoding="utf-8") as f:
    for r in csv.DictReader(f):
        SRC[r["platform"]] = r
KEY_PLATFORM = {"amazon": "Amazon", "duckduckgo": "DuckDuckGo", "ebay_previous": "eBay", "ebay": "eBay", "espn": "ESPN",
                "github": "GitHub", "google": "Google", "linkedin": "LinkedIn", "meta": "Meta", "reddit": "Reddit",
                "strava": "Strava", "tiktok": "TikTok", "weather": "Weather.com", "wikipedia": "Wikipedia", "x": "X"}
FILE_KEY = {f"data/text/{k}.txt": k for k in KEY_PLATFORM}


def policy_url(key):
    return SRC[KEY_PLATFORM[key]]["url"].split(" ")[0]


def fragment_link(key, quote):
    """Policy URL plus a text fragment that jumps to the quote in browsers that support it."""
    words = []
    for w in quote.split():
        if "[" in w or "]" in w:
            break
        words.append(w)
        if len(words) == 6:
            break
    start = " ".join(words).rstrip(",.;:")
    if len(start) < 12:
        return policy_url(key)
    enc = urlquote(start, safe="").replace("-", "%2D")
    return policy_url(key) + "#:~:text=" + enc


PAGE_QUOTES = []


def quote_block(key, file, line, quote, label=None):
    assert quote in text_line(file, line), (file, line, quote[:60])
    PAGE_QUOTES.append({"file": file, "line": line, "quote": quote})
    who = label or KEY_PLATFORM[key]
    return (f'<blockquote class="q"><p><mark>{html.escape(quote)}</mark></p>'
            f'<footer><a href="{html.escape(fragment_link(key, quote))}" target="_blank" rel="noopener">'
            f'{html.escape(who)} privacy policy</a><span class="ref">{html.escape(file)}, line {line}</span></footer></blockquote>')


def finding_quotes(fid, extra_lines=(), extra_only=False):
    f = FIND[fid]
    out = [] if extra_only else [quote_block(f["key"], f["file"], f["line"], f["quote"])]
    by_line = {e["line"]: e for e in f.get("extra_quotes", [])}
    for ln in extra_lines:
        e = by_line[ln]
        out.append(quote_block(f["key"], f["file"], e["line"], e["quote"]))
    return out


# ---------------------------------------------------------------- sections
def esc(s):
    return html.escape(s, quote=True)


def render_headlines():
    parts = []
    for n, h in enumerate(HEADLINES, 1):
        keys = []
        items = []
        for it in h["items"]:
            if "f" in it:
                key = FIND[it["f"]]["key"]
                qs = finding_quotes(it["f"], it.get("extra", []), it.get("extra_only", False))
                for also in it.get("also", []):
                    qs += finding_quotes(also)
            else:
                q = it["q"]
                key = FILE_KEY[q["file"]]
                qs = [quote_block(key, q["file"], q["line"], q["quote"])]
            if KEY_PLATFORM[key] not in keys:
                keys.append(KEY_PLATFORM[key])
            items.append(f'<li><p class="says">{esc(it["text"])}</p>{"".join(qs)}</li>')
        more = '<p class="more"><a href="#ai-table">See what all 14 policies say about AI training</a></p>' if h.get("more") else ""
        parts.append(
            f'<article class="finding" id="{h["id"]}">'
            f'<header><h3>{esc(h["title"])}</h3><p class="chips">{"".join(f"<span>{esc(k)}</span>" for k in keys)}</p></header>'
            f'<p class="why"><strong>Why it’s surprising:</strong> {esc(h["why"])}</p>'
            f'<ul class="items">{"".join(items)}</ul>{more}</article>')
    return "\n".join(parts)


def render_toc():
    return "".join(f'<li><a href="#{h["id"]}">{esc(h["title"])}</a></li>' for h in HEADLINES)


def render_ai_table():
    rows = []
    for key, train, opt in AI_TABLE:
        def cell(spec):
            cls, label, ids = spec
            qs = "".join(q for fid in ids for q in finding_quotes(fid))
            det = f'<details><summary>Show the policy’s words</summary>{qs}</details>' if qs else ""
            return f'<td><span class="pill {cls}">{esc(label)}</span>{det}</td>'
        rows.append(f'<tr><th scope="row">{esc(KEY_PLATFORM[key])}</th>{cell(train)}{cell(opt)}</tr>')
    return "\n".join(rows)


def render_ebay():
    out = []
    for idx, text in EBAY_CHANGES:
        c = CHANGES[idx]
        qs = []
        if c.get("old_quote"):
            qs.append('<p class="vlabel">Notice in force until Nov 25, 2026</p>' +
                      quote_block("ebay_previous", "data/text/ebay_previous.txt", c["old_line"], c["old_quote"], "eBay (current)"))
        if c.get("new_quote"):
            qs.append('<p class="vlabel">New notice from Nov 26, 2026</p>' +
                      quote_block("ebay", "data/text/ebay.txt", c["new_line"], c["new_quote"], "eBay (new)"))
        out.append(f'<li><p class="says">{esc(text)}</p><details><summary>Compare the wording</summary>{"".join(qs)}</details></li>')
    return "".join(out)


def ranking_data():
    crit = SCORES["criteria"]
    rows = []
    for p in SCORES["platforms"]:
        cells = {}
        for c in crit:
            s = p["scores"][c["key"]]
            ev = []
            for e in s["evidence"]:
                fid = e["id"]
                ev.append(quote_block(p["key"], p["file"], e["line"], e["quote"]))
            cells[c["key"]] = {"score": s["score"], "why": s["why"], "quotes": ev,
                               "notStated": s.get("not_stated_parts", [])}
        rows.append({"key": p["key"], "name": p["platform"], "tier": SCORES["stability"]["tiers"][p["key"]],
                     "thirds": SCORES["stability"]["random_weights"]["thirds"][p["key"]], "cells": cells})
    return {"criteria": [{"key": c["key"], "name": c["name"], "weight": c["weight"], "rubric": c["rubric"]} for c in crit],
            "rows": rows}


def render_rank_rows(data):
    """Static rows at default weights so the table is complete before any script runs."""
    w = {c["key"]: c["weight"] for c in data["criteria"]}
    def tot(r):
        return sum(w[k] * r["cells"][k]["score"] for k in w) / (3 * sum(w.values())) * 100
    rows = sorted(data["rows"], key=lambda r: (-tot(r), r["name"]))
    out, prev, rank = [], None, 0
    for i, r in enumerate(rows, 1):
        t = round(tot(r), 1)
        if t != prev:
            rank, prev = i, t
        tied = sum(1 for x in rows if round(tot(x), 1) == t) > 1
        cells = "".join(f'<td class="sc"><button type="button" class="s s{r["cells"][c["key"]]["score"]}" data-k="{r["key"]}" data-c="{c["key"]}" aria-label="{esc(c["name"])}: {r["cells"][c["key"]]["score"]} of 3. Show evidence">{r["cells"][c["key"]]["score"]}</button></td>' for c in data["criteria"])
        out.append(f'<tr data-k="{r["key"]}"><td class="rk">{rank}{"=" if tied else ""}</td><th scope="row"><button type="button" class="pname" data-k="{r["key"]}">{esc(r["name"])}</button></th>'
                   f'<td class="tot">{t:.1f}</td>{cells}<td><span class="tier t-{r["tier"].lower()}">{esc(r["tier"])}</span></td></tr>')
    return "\n".join(out)


def render_sources():
    out = []
    for key in ["amazon", "duckduckgo", "ebay_previous", "espn", "github", "google", "linkedin", "meta", "reddit", "strava", "tiktok", "weather", "wikipedia", "x"]:
        r = SRC[KEY_PLATFORM[key]]
        upd = r["policy_last_updated"].split(" ")[0] if r["policy_last_updated"] else "no date stated"
        note = {"ebay_previous": " (notice in force on Oct 21, 2026; a new notice starts Nov 26, 2026)",
                "espn": " (Disney’s privacy policy, which covers ESPN)",
                "wikipedia": " (Wikimedia Foundation policy)",
                "meta": " (copy saved from a browser)", "reddit": " (copy saved from a browser)"}.get(key, "")
        out.append(f'<li><a href="{esc(policy_url(key))}" target="_blank" rel="noopener">{esc(KEY_PLATFORM[key])}</a>'
                   f'<span>policy dated {esc(upd)}{esc(note)}</span></li>')
    return "".join(out)


# ---------------------------------------------------------------- page
def main():
    headlines = render_headlines()
    ai_rows = render_ai_table()
    ebay = render_ebay()
    data = ranking_data()
    rank_rows = render_rank_rows(data)
    crit_heads = "".join(f'<th scope="col" class="num"><button type="button" class="sort" data-sort="{c["key"]}">{esc(c["name"])} <span class="w" data-w="{c["key"]}">{c["weight"]}%</span></button></th>' for c in data["criteria"])
    sliders = "".join(
        f'<label class="wt" for="w-{c["key"]}"><span>{esc(c["name"])}</span>'
        f'<input type="range" id="w-{c["key"]}" min="0" max="50" step="5" value="{c["weight"]}" data-c="{c["key"]}"><output id="o-{c["key"]}">{c["weight"]}%</output></label>'
        for c in data["criteria"])
    rubric = "".join(
        f'<li><strong>{esc(c["name"])}</strong> <span class="muted">({c["weight"]}%)</span><ol start="0">'
        + "".join(f"<li>{esc(v)}</li>" for v in c["rubric"].values()) + "</ol></li>" for c in data["criteria"])

    # numbers for the methods section
    n_find = len([f for f in FIND.values() if f["key"] != "ebay"])
    n_rev = sum(1 for f in FIND.values() if f.get("review_verdict"))
    n_fixed = sum(1 for f in FIND.values() if f.get("review_verdict") == "overstated")
    dom = SCORES["stability"]["dominance"]

    page_json = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    with open(os.path.join(A, "page_template.html"), encoding="utf-8") as f:
        tpl = f.read()
    out = (tpl.replace("{{TITLE}}", esc(TITLE))
              .replace("{{TOC}}", render_toc())
              .replace("{{HEADLINES}}", headlines)
              .replace("{{AI_ROWS}}", ai_rows)
              .replace("{{EBAY}}", ebay)
              .replace("{{CRIT_HEADS}}", crit_heads)
              .replace("{{RANK_ROWS}}", rank_rows)
              .replace("{{SLIDERS}}", sliders)
              .replace("{{RUBRIC}}", rubric)
              .replace("{{SOURCES}}", render_sources())
              .replace("{{N_FIND}}", str(n_find))
              .replace("{{N_REV}}", str(n_rev))
              .replace("{{N_FIXED}}", str(n_fixed))
              .replace("{{N_DOM}}", str(len(dom)))
              .replace("{{DATA}}", page_json))
    # the page-quote count is known only after rendering everything
    seen = {(q["file"], q["line"], q["quote"]) for q in PAGE_QUOTES}
    out = out.replace("{{N_PAGE_QUOTES}}", str(len(seen)))
    assert "{{" not in out, re.findall(r"\{\{\w+\}\}", out)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(out)
    with open(os.path.join(A, "page_quotes.json"), "w", encoding="utf-8") as f:
        json.dump({"note": "Every quote shown on what-your-apps-know.html", "quotes": [dict(file=a, line=b, quote=c) for a, b, c in sorted(seen)]},
                  f, ensure_ascii=False, indent=1)
    print(f"wrote {os.path.relpath(OUT, ROOT)} ({len(out)//1024} KB), {len(seen)} distinct quotes")


if __name__ == "__main__":
    main()
