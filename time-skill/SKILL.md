---
name: time-skill
description: Get the current time anywhere, convert times between timezones, compare multiple cities at once, find overlapping working hours, generate copy-paste meeting times and calendar (.ics) invites, warn about upcoming Daylight-Saving clock changes, show follow-the-sun team handoffs, and convert Unix/epoch timestamps — all DST-aware. Use this skill WHENEVER the user asks what time it is in a place, the current time/date, to convert a time between zones (e.g. "3pm EST in IST"), to compare times across cities, to schedule or find a meeting slot across timezones, to write out a time for an email/invite, to make a calendar invite, to check when clocks change, to see who on a team is online now, or to decode a Unix timestamp. Trigger it even for casual phrasings like "what time is it in Tokyo", "when is 9am London for me", "find a good time for a Chennai–New York call", "give me the times for the invite", or "what's this timestamp 1749009600" — and even when the user does not say the words "timezone" or "convert".
---

# Time Skill

This skill answers time and timezone questions accurately, including the part that trips people up most: **Daylight Saving Time**. Research into real user complaints (Reddit, LinkedIn, developer forums) shows the recurring failures are DST mistakes, manual-math errors when comparing several places, and botched cross-timezone meeting scheduling. This skill removes all of them using Python's `zoneinfo` standard library, which carries the full IANA timezone database and adjusts for DST automatically.

## Why a script instead of mental math

Claude has no real-time clock and cannot reliably do timezone math in its head, especially across DST boundaries (the rules differ by country and change over time). The bundled script reads the machine's accurate system clock and uses the IANA database for every conversion, so the answer is correct and verifiable. **Always use the script — never compute times by hand.**

## The tool

A single script handles everything: `scripts/timezone_tool.py`. It has ten commands — four core, six for scheduling/dev workflows. Run `python3 scripts/timezone_tool.py <command> --help` for any command's exact arguments.

## Core commands

### 1. Current time — `now`
```bash
python3 scripts/timezone_tool.py now <place> [<place> ...]
```
Example: `python3 scripts/timezone_tool.py now tokyo`

### 2. Convert a time between two zones — `convert`
```bash
python3 scripts/timezone_tool.py convert "<time>" <from> <to> [when]
```
Examples:
- `python3 scripts/timezone_tool.py convert "3pm" EST IST`
- `python3 scripts/timezone_tool.py convert "09:00" london chennai 2026-07-15`
- `python3 scripts/timezone_tool.py convert "9am" london chennai "next friday"`

The optional `when` matters for DST correctness — "3pm EST" lands on a different UTC offset in July than in January. It accepts an ISO date or natural language (see "Naming dates" below). If omitted, the script assumes today.

### 3. Compare current time across places — `compare`
```bash
python3 scripts/timezone_tool.py compare <place> <place> ...
```
Example: `python3 scripts/timezone_tool.py compare chennai london "new york" tokyo`

Output is sorted west-to-east so the day's progression reads naturally.

### 4. Find overlapping working hours — `overlap`
```bash
python3 scripts/timezone_tool.py overlap <place> <place> ... [--hours START END]
```
Examples:
- `python3 scripts/timezone_tool.py overlap chennai "new york"`
- `python3 scripts/timezone_tool.py overlap chennai london tokyo --hours 9 18`

Working hours default to 09:00–18:00 local (whole-hour granularity). Reports the window (if any) when everyone is simultaneously working, in each person's local time. If there's no overlap, it says so plainly rather than inventing one.

## Scheduling & dev commands

### 5. Copy-paste meeting snippet — `snippet`
Produces a one-line string to drop into an email or Slack message.
```bash
python3 scripts/timezone_tool.py snippet "<time>" <from> <target> [<target> ...] [--when WHEN]
```
Example: `python3 scripts/timezone_tool.py snippet "3pm" PT ET London IST`
→ `3:00 PM PT  /  6:00 PM ET  /  11:00 PM London  /  3:30 AM IST (+1d)`

The `(+1d)` / `(-1d)` tags flag when a zone lands on a different calendar day.

### 6. Calendar invite — `ics`
Writes a universally-compatible `.ics` file (stored in UTC) that any calendar app can import.
```bash
python3 scripts/timezone_tool.py ics "<time>" <from> --title "T" [--when WHEN] [--duration MIN] [--out PATH]
```
Example: `python3 scripts/timezone_tool.py ics "3pm" IST --title "Investor call" --when "next monday" --duration 45`

Default duration is 30 min; default output path is `/tmp/invite.ics`. After running, present the `.ics` file to the user so they can download/import it.

### 7. Daylight-Saving change warnings — `dst`
Lists upcoming clock changes for one zone, and for **two** zones also flags when the gap between them changes (the classic trap that silently shifts a recurring cross-timezone meeting by an hour).
```bash
python3 scripts/timezone_tool.py dst <place> [place2] [--months N]
```
Examples:
- `python3 scripts/timezone_tool.py dst london`
- `python3 scripts/timezone_tool.py dst chennai london --months 12`

Note: it reports the *date* of each change (the exact local instant is typically 2–3am); that date is what matters for scheduling.

### 8. Follow-the-sun handoff — `handoff`
Shows who is currently within working hours, who goes offline soonest, and who comes online next — for distributed teams, on-call, or support coverage.
```bash
python3 scripts/timezone_tool.py handoff <place> <place> ... [--hours START END]
```
Example: `python3 scripts/timezone_tool.py handoff chennai london "new york" tokyo`

### 9. Unix/epoch timestamp — `epoch`
Converts a Unix timestamp to human time. Auto-detects seconds (10 digits), milliseconds (13), or microseconds (16).
```bash
python3 scripts/timezone_tool.py epoch <value> [place ...]
```
Examples:
- `python3 scripts/timezone_tool.py epoch 1749009600` (shows UTC)
- `python3 scripts/timezone_tool.py epoch 1749009600 chennai "new york"`

### 10. Per-command help — `--help`
Every command supports `--help` to show its exact arguments and options.

## Naming dates (for `convert`, `snippet`, `ics`)

The `when` / `--when` argument accepts:
- **ISO date**: `2026-07-15`
- **Relative words**: `today`, `tomorrow`, `yesterday`, `"day after tomorrow"`, `"in 3 days"`, `"2 days ago"`
- **Weekdays**: `monday`..`sunday`, `"this friday"`, `"next friday"`

**Weekday rule** (documented so results never surprise): a bare weekday or `"this <day>"` resolves to the soonest matching day, counting today if it matches; `"next <day>"` resolves to the following week's occurrence. The resolved date is always printed in the output, so verify it at a glance. If a phrase isn't understood, the script errors clearly rather than guessing.

## How to name a place

Any of these work as `<place>`:
- **IANA name** (most precise): `America/New_York`, `Asia/Kolkata`, `Europe/London`, `Australia/Sydney`
- **City name**: `tokyo`, `chennai`, `"new york"`, `"los angeles"`, `singapore`, `dubai`
- **Abbreviation**: `EST`, `PST`, `IST`, `GMT`, `UTC`, `JST`, `CET`

Multi-word cities must be quoted on the command line (`"new york"`, `"hong kong"`).

## Handling ambiguity honestly

The script prints a `⚠` note when it makes an assumption:
- **IST** → assumed India (also means Israel / Ireland time)
- **CST** → assumed US Central (also means China / Cuba)
- **EST/PST/CET/etc.** → interpreted as the Daylight-Saving-aware geographic zone, so "EST" shows EDT in summer and EST in winter

When you relay results, surface these notes if they could matter. If the user's intent is unclear (e.g. they say "IST" and might mean Israel), ask which they meant rather than silently guessing.

## Presenting results to the user

Run the script, then translate its output into a short, natural answer. Lead with the direct answer. Mention the day-shift ("that's the next day in Tokyo") and any DST/ambiguity caveat only when relevant. Don't dump the raw script output unless the user wants the full table — for a single "what time is it in X" question, one clean sentence is best. For `snippet` and `ics`, give the user the snippet line or the file directly.

## Limitations to be honest about

- Recognizes ~90 major cities by name; for others, use the IANA name (e.g. `Europe/Warsaw`).
- `overlap` and `handoff` apply one shared working-hours range to everyone (not per-person hours), and ignore weekends/holidays.
- `overlap` works in whole-hour steps, so windows are hour-granular.
- Natural-language dates cover the defined set above, not arbitrary English.
- For high-stakes times (a critical meeting), it's worth verifying against a second source.

## Adding places that aren't recognized

If a city isn't in the shortlist, use its IANA name directly (every IANA zone is accepted). The standard form is `Region/City` (e.g. `Europe/Warsaw`, `America/Bogota`); when unsure of the exact zone, say you're not certain and offer the closest major city you can confirm.
