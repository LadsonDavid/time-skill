# Changelog

## v1.0.0 — 2026-06-04

### Initial release

**Core commands:**
- `now` — current time in any city/timezone
- `convert` — DST-aware conversion between two zones
- `compare` — side-by-side time across multiple cities
- `overlap` — find shared working-hours window

**Scheduling & dev commands:**
- `snippet` — copy-paste one-liner for emails/Slack (e.g. `3pm PT / 6pm ET / 11pm London`)
- `ics` — generate calendar invite (.ics) file
- `dst` — upcoming Daylight Saving warnings; for two zones, flags when the gap shifts
- `handoff` — follow-the-sun: who's online, who's next
- `epoch` — Unix timestamp converter (auto-detects s/ms/µs)

**Natural-language dates:**
- `tomorrow`, `next friday`, `in 3 days`, `yesterday`, and more — works in `convert`, `snippet`, and `ics`

**Other:**
- ~90 city names recognized (plus all IANA timezone names)
- Ambiguity warnings for IST (India/Israel/Ireland) and CST (US/China/Cuba)
- EST/PST/etc. resolve to DST-aware geographic zones
- Zero external dependencies (Python 3.9+ standard library only)
