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

## Collection problems and workarounds

_What broke while gathering data and how it was handled._

- **2026-10-21** — None yet.
- **2026-10-21** — Meta: plain curl GET (Chrome User-Agent) returned HTTP 400 and an 856-byte Facebook "Sorry, something went wrong" error page, not the policy. Likely bot/JS gating. Error page moved out of data/raw/ (not a policy). No workaround tried yet; paused for user decision.

## Permissions I approved or denied

_Tool, command, or access requests and the decision made on each._

- **2026-10-21** — No permission prompts this step.

## Analysis decisions

_Choices about scope, cleaning, methods, and interpretation, with the reason._

- **2026-10-21** — Decided to keep a running analysis log and to require it
  be updated after every step (rule added to `CLAUDE.md`).
- **2026-10-21** — Collection setup: originals go in data/raw/, cleaned text (BeautifulSoup: drop script/style/nav/header/footer, keep headings, paragraphs, list items) in data/text/, metadata in data/sources.csv (platform, url, retrieval_date, policy_last_updated, method, status). Platforms done one at a time; on any failure, stop and report before a workaround.

## Prompts I used

_Prompts given to Claude, verbatim or closely paraphrased._

- **2026-10-21** — "Create analysis-log.md for this project, with sections for:
  Sources, Collection problems and workarounds, Permissions I approved or
  denied, Analysis decisions, Prompts I used, and Verification checks. Then
  add a rule to CLAUDE.md: after every step, update analysis-log.md with what
  you did, what failed, and what I decided. Never delete earlier entries."
- **2026-10-21** — "Collect the current privacy policies of these platforms: [Meta, X, Strava, Google, OpenAI, Reddit, TikTok, Wikipedia, Weather.com, ESPN, DuckDuckGo, GitHub, Amazon, EBay, LinkedIn]. For each one, find the official policy page, save the original in data/raw/ (HTML or PDF), save cleaned plain text in data/text/, and record in data/sources.csv: platform, URL, retrieval date, the policy's stated last-updated date, how you got it, and status. Work through them one at a time and tell me when a download fails and why, before trying a workaround."

## Verification checks

_How results were checked (spot checks, recounts, cross-source comparisons) and the outcome._

- **2026-10-21** — Confirmed `analysis-log.md` and `CLAUDE.md` were created
  and committed. No data checks yet.
- **2026-10-21** — Meta: inspected the response body; confirmed it was an error page (title "Error"), so it was not saved as the policy.
