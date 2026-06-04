# ⏰ Time Skill

**DST-aware time, timezone conversion, and cross-timezone scheduling for AI agents.**

> *"I get such anxiety scheduling across time zones, even though I do it all day long."* — [real Reddit user](https://codeandsolder.substack.com/p/time-zones-are-causing-havoc)

Time Skill gives your AI agent an accurate real-time clock, Daylight-Saving-aware timezone math, and practical scheduling tools — so it never guesses at times or botches a meeting invite.

Built on the [Agent Skills open standard](https://code.claude.com/docs/en/skills). Works with **Claude Code**, **Claude.ai**, and any AI tool that supports Agent Skills.

---

## What it does

| Command | What it solves |
|---------|---------------|
| `now` | "What time is it in Tokyo right now?" |
| `convert` | "What's 3pm EST in IST?" — DST-correct, with day-shift warnings |
| `compare` | Side-by-side current time across 2–10 cities, sorted west→east |
| `overlap` | Find the working-hours window where everyone's available |
| `snippet` | One-line `3pm PT / 6pm ET / 11pm London` to paste into Slack/email |
| `ics` | Generate a downloadable `.ics` calendar invite (stored in UTC) |
| `dst` | Warn when upcoming clock changes will shift your recurring meetings |
| `handoff` | Follow-the-sun: who's online now, who comes on next |
| `epoch` | Decode Unix timestamps (auto-detects seconds/ms/µs) |

**Plus natural-language dates** everywhere: `tomorrow`, `next friday`, `in 3 days`.

---

## Install

### Claude Code (recommended)

```bash
# Add as a plugin marketplace
/plugin marketplace add LadsonDavid/time-skill

# Install the skill
/plugin install time-skill@time-skill
```

Or with npx:

```bash
npx skills add https://github.com/LadsonDavid/time-skill
```

### Claude.ai

1. Download [`dist/time-skill.skill`](dist/time-skill.skill) from this repo
2. Go to **Settings → Capabilities → Skills**
3. Upload the `.skill` file

### Manual install (any AI tool)

```bash
git clone https://github.com/LadsonDavid/time-skill.git
cp -r time-skill/time-skill ~/.claude/skills/
```

---

## Usage examples

Once installed, just ask naturally — the skill triggers automatically:

> "What time is it in Chennai?"
>
> "Convert 3pm London to IST"
>
> "Find a good meeting time for our team in Chennai, London, and New York"
>
> "When do the clocks change in the US vs Europe?"
>
> "What's this timestamp: 1749009600"
>
> "Give me the times for the invite — 3pm IST, 45 min, title Investor Call"

### Direct script usage

You can also run the script directly:

```bash
# Current time
python3 time-skill/scripts/timezone_tool.py now tokyo

# Convert with natural-language date
python3 time-skill/scripts/timezone_tool.py convert "3pm" EST IST "next friday"

# Copy-paste snippet for an email
python3 time-skill/scripts/timezone_tool.py snippet "3pm" PT ET London IST

# DST warnings for a pair of zones
python3 time-skill/scripts/timezone_tool.py dst chennai london --months 12

# Follow-the-sun handoff
python3 time-skill/scripts/timezone_tool.py handoff chennai london "new york" tokyo

# Calendar invite
python3 time-skill/scripts/timezone_tool.py ics "3pm" IST --title "Investor call" --when "next monday" --duration 45

# Unix timestamp
python3 time-skill/scripts/timezone_tool.py epoch 1749009600 chennai "new york"
```

---

## Why this exists

Research across Reddit, LinkedIn, and developer forums surfaced three recurring timezone failures:

1. **DST mistakes** — "EST" in summer is actually EDT (UTC-4, not UTC-5). Most tools get this wrong. This skill maps abbreviations to geographic zones that auto-adjust.

2. **Manual math errors** — comparing 3+ timezones by hand is error-prone. The `compare` and `overlap` commands eliminate this entirely.

3. **Recurring meeting drift** — the US and EU change clocks on *different dates*, silently shifting your standing call by an hour. The `dst` command for two zones flags exactly when this happens.

### Design decisions

- **No external API** — uses Python's `zoneinfo` standard library (the official IANA timezone database) + the system clock. Zero network dependency.
- **DST-correct by default** — abbreviations like EST/PST resolve to the geographic zone that auto-adjusts for Daylight Saving.
- **Honest about ambiguity** — flags that "IST" could mean India/Israel/Ireland, and "CST" could mean US/China/Cuba. Never silently guesses.
- **Honest about limits** — says "no overlap" when there isn't one, rather than inventing a slot.

---

## Requirements

- Python 3.9+ (for `zoneinfo` standard library)
- No pip dependencies — uses only the standard library

---

## Supported places

The skill accepts three formats:

- **IANA names** (most precise): `America/New_York`, `Asia/Kolkata`, `Europe/London`
- **~90 city names**: `tokyo`, `chennai`, `"new york"`, `london`, `singapore`, `dubai`
- **Abbreviations**: `EST`, `PST`, `IST`, `GMT`, `UTC`, `JST`, `CET`

Every IANA timezone is supported via its full name. The city shortlist covers the most commonly referenced places globally.

---

## Limitations

Transparency matters more than marketing:

- `overlap` and `handoff` use one shared working-hours range (not per-person hours) and ignore weekends/holidays
- `overlap` works in whole-hour steps
- Natural-language dates cover a defined set (`tomorrow`, `next friday`, `in 3 days`) — not arbitrary English
- Recognizes ~90 cities by name; others need the IANA name
- For high-stakes scheduling, verify against a second source

---

## Contributing

Issues and PRs welcome! Some areas where help would be great:

- Adding more cities to the shortlist
- Per-person working hours for `overlap`
- Weekend/holiday awareness
- Market-hours tracker for investors
- Visual timeline output

---

## License

MIT — see [LICENSE](LICENSE).

---

Built with research, not guesswork. If timezone pain has ever cost you a meeting, a deal, or your sleep — this is for you.
