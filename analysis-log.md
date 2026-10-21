# Analysis Log

Running record of this project's data work. Entries are appended in date
order within each section; earlier entries are never deleted or rewritten.
If an entry turns out to be wrong, add a new dated entry that corrects it.

Entry format: `- **YYYY-MM-DD** — what was done / what failed / what was decided.`

## Sources

_Where each dataset or document came from (URL or path, date retrieved, version)._

- **2026-10-21** — No sources logged yet. `claude-system-prompt-drift.html`
  predates this log; its sources have not been recorded here.
- **2026-10-21** — Started privacy-policy collection (15 platforms). Meta: target URL https://www.facebook.com/privacy/policy/ — not yet retrieved.
- **2026-10-21** — Meta: saved https://opensource.fb.com/legal/privacy/ (HTTP 200, 10.7 KB) → data/raw/meta.html, data/text/meta.txt. Stated "Effective April 25, 2023". Scope is Meta open-source websites only, not the main Facebook/Instagram privacy policy.
- **2026-10-21** — Meta (main policy): saved user-uploaded browser copy of the printable policy (saved-from URL https://mbasic.facebook.com/privacy/policy/printable/version/26776488768644674/, 296 KB) → data/raw/meta.html, data/text/meta.txt. Stated "Effective July 23, 2026". The open-source policy files were renamed to data/raw/meta_opensource.html and data/text/meta_opensource.txt (not deleted).

## Collection problems and workarounds

_What broke while gathering data and how it was handled._

- **2026-10-21** — None yet.
- **2026-10-21** — Meta: plain curl GET (Chrome User-Agent) returned HTTP 400 and an 856-byte Facebook "Sorry, something went wrong" error page, not the policy. Likely bot/JS gating. Error page moved out of data/raw/ (not a policy). No workaround tried yet; paused for user decision.
- **2026-10-21** — Meta workaround: user supplied an alternate URL, https://opensource.fb.com/legal/privacy/, which downloaded with plain curl.
- **2026-10-21** — Collection paused by user at X (step 2 of 15). Remaining 13 platforms not started.
- **2026-10-21** — Meta (main policy): user uploaded a browser-saved HTML of https://www.facebook.com/privacy/policy/ (361 KB, title "Meta Privacy Policy - How Meta collects and uses user data", canonical URL confirmed). It contains no policy text: body is a single empty div plus 67 script tags, 11 words of visible text total, and no policy phrases in the scripts. The page is rendered by JavaScript and the save captured only the unrendered shell. Not saved to data/raw/; kept in scratchpad. Paused for user decision.
- **2026-10-21** — Meta workaround that worked: user saved the printable version of the policy from their browser and uploaded it (.htm). Unlike the 1st upload, it contains the rendered text.
- **2026-10-21** — Logging note: a shell quoting error stopped the logging command partway; the remaining entries for this step were added in a second pass. No data was affected.

## Permissions I approved or denied

_Tool, command, or access requests and the decision made on each._

- **2026-10-21** — No permission prompts this step.
- **2026-10-21** — X: user rejected the tool call that would clean the downloaded X page (https://x.com/en/privacy, HTTP 200, title "X Privacy Policy") and said "stop". X copy stays in scratchpad only; nothing for X saved to data/ or sources.csv. Collection paused after Meta.

## Analysis decisions

_Choices about scope, cleaning, methods, and interpretation, with the reason._

- **2026-10-21** — Decided to keep a running analysis log and to require it
  be updated after every step (rule added to `CLAUDE.md`).
- **2026-10-21** — Collection setup: originals go in data/raw/, cleaned text (BeautifulSoup: drop script/style/nav/header/footer, keep headings, paragraphs, list items) in data/text/, metadata in data/sources.csv (platform, url, retrieval_date, policy_last_updated, method, status). Platforms done one at a time; on any failure, stop and report before a workaround.
- **2026-10-21** — User chose https://opensource.fb.com/legal/privacy/ as the Meta source. Claude flagged that it covers only Meta open-source websites; recorded the scope in sources.csv status. Not yet decided whether it should be replaced by the main Meta Products policy for comparison.
- **2026-10-21** — Made the main Meta Products policy the "Meta" row and kept the open-source websites policy as a separate row, "Meta (open-source sites)". Claude proposed this; the user did not explicitly confirm it before uploading the main policy. Repeated lines in the cleaned Meta text (e.g. 19x "Information categories we use...") come from the policy's per-purpose tables and were left in, not de-duplicated.

## Prompts I used

_Prompts given to Claude, verbatim or closely paraphrased._

- **2026-10-21** — "Create analysis-log.md for this project, with sections for:
  Sources, Collection problems and workarounds, Permissions I approved or
  denied, Analysis decisions, Prompts I used, and Verification checks. Then
  add a rule to CLAUDE.md: after every step, update analysis-log.md with what
  you did, what failed, and what I decided. Never delete earlier entries."
- **2026-10-21** — "Collect the current privacy policies of these platforms: [Meta, X, Strava, Google, OpenAI, Reddit, TikTok, Wikipedia, Weather.com, ESPN, DuckDuckGo, GitHub, Amazon, EBay, LinkedIn]. For each one, find the official policy page, save the original in data/raw/ (HTML or PDF), save cleaned plain text in data/text/, and record in data/sources.csv: platform, URL, retrieval date, the policy's stated last-updated date, how you got it, and status. Work through them one at a time and tell me when a download fails and why, before trying a workaround."
- **2026-10-21** — User reply to the Meta failure: "https://opensource.fb.com/legal/privacy/"
- **2026-10-21** — User uploaded file: Meta_Privacy_Policy_-_How_Meta_collects_and_uses_user_data___Privacy_Center___...___Facebook_Privacy.html (no accompanying text).
- **2026-10-21** — User uploaded file: Meta_Privacy_Policy_-_How_Meta_collects_and_uses_user_data.htm (no accompanying text).

## Verification checks

_How results were checked (spot checks, recounts, cross-source comparisons) and the outcome._

- **2026-10-21** — Confirmed `analysis-log.md` and `CLAUDE.md` were created
  and committed. No data checks yet.
- **2026-10-21** — Meta: inspected the response body; confirmed it was an error page (title "Error"), so it was not saved as the policy.
- **2026-10-21** — Meta: confirmed HTTP 200, page is a privacy policy (2,868 words cleaned), "Effective April 25, 2023" on line 1; read the opening scope paragraph and confirmed it applies only to the open-source websites.
- **2026-10-21** — Meta upload: checked title and canonical link (match the official policy), then counted visible text (11 words) and searched scripts for policy text and an effective date (none found). Rejected as unusable.
- **2026-10-21** — Meta (main): 21,323 visible words in the raw file, 21,776 after cleaning; 260 headings, including all 14 top-level policy questions; "Effective July 23, 2026" at line 40 of the text; 41 of 536 long lines repeat, traced to the per-purpose tables, not to cleaning.
