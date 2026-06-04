# ⏰ Time Skill

**Stop guessing at timezone math. Let your AI agent handle it.**

> *"I get such anxiety scheduling across time zones, even though I do it all day long."* — [real Reddit user](https://codeandsolder.substack.com/p/time-zones-are-causing-havoc)

Most AI agents can't tell you what time it is. Seriously. Ask Claude "what time is it in Tokyo?" and it'll either guess wrong or tell you it doesn't have a clock.

This fixes that. Time Skill plugs into your agent and gives it a real clock, proper timezone conversion (yes, Daylight Saving is handled correctly), and a bunch of scheduling tools that actually work.

It follows the [Agent Skills open standard](https://code.claude.com/docs/en/skills), so it works with Claude Code, Claude.ai, and other compatible AI tools.

---

## What's in the box

| Command | What you'd ask |
|---------|---------------|
| `now` | "What time is it in Tokyo right now?" |
| `convert` | "What's 3pm EST in IST?" |
| `compare` | Show me the time in Chennai, London, and New York side by side |
| `overlap` | When can all of us actually meet? |
| `snippet` | Give me a `3pm PT / 6pm ET / 11pm London` line for my email |
| `ics` | Make me a calendar invite I can send out |
| `dst` | Heads up: the clocks change next month and your standing call will shift |
| `handoff` | Who on the team is online right now? Who's next? |
| `epoch` | What's this timestamp: `1749009600`? |

You can also use natural-language dates everywhere: `tomorrow`, `next friday`, `in 3 days`.

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

## How to use it

Once it's installed, just talk normally. The skill picks up on time-related questions automatically:

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

### Running the script directly

If you want to use it outside an AI agent, the Python script works standalone:

```bash
# Current time
python3 time-skill/scripts/timezone_tool.py now tokyo

# Convert with a natural-language date
python3 time-skill/scripts/timezone_tool.py convert "3pm" EST IST "next friday"

# Copy-paste snippet for an email
python3 time-skill/scripts/timezone_tool.py snippet "3pm" PT ET London IST

# DST warnings for two zones
python3 time-skill/scripts/timezone_tool.py dst chennai london --months 12

# Who's online right now?
python3 time-skill/scripts/timezone_tool.py handoff chennai london "new york" tokyo

# Calendar invite
python3 time-skill/scripts/timezone_tool.py ics "3pm" IST --title "Investor call" --when "next monday" --duration 45

# Decode a Unix timestamp
python3 time-skill/scripts/timezone_tool.py epoch 1749009600 chennai "new york"
```

---

## Why I built this

I dug through Reddit, LinkedIn, and developer forums to understand what actually goes wrong with timezone tools. Three problems kept showing up:

**1. DST trips everyone up.** When someone types "EST" in June, they almost certainly mean Eastern Time, which is EDT (UTC-4) in summer. But most tools treat EST as a fixed UTC-5 offset. This skill maps abbreviations to geographic zones that auto-adjust. So "EST" in summer correctly shows EDT, and in winter shows EST.

**2. Mental math breaks down past two timezones.** Comparing Chennai, London, and New York in your head? Good luck. The `compare` and `overlap` commands do it instantly, and `overlap` will tell you straight up if there's no shared window instead of faking one.

**3. Recurring meetings silently break twice a year.** The US and EU change clocks on different dates. Your weekly standup just shifted by an hour and nobody noticed. The `dst` command flags exactly when this happens for any pair of zones.

### How it works under the hood

The script reads the system clock and uses Python's `zoneinfo` library, which carries the full IANA timezone database. No API calls, no network requests, no external dependencies. Just the standard library.

A few deliberate choices worth mentioning:

- If a timezone abbreviation is ambiguous (IST could be India, Israel, or Ireland), the skill flags it rather than quietly picking one. Same with CST (US Central vs China vs Cuba).
- If there's no overlapping work window between two cities, it says so. It won't invent a slot to look helpful.
- Every output shows the resolved date and offset so you can verify at a glance.

---

## Requirements

- Python 3.9+ (that's when `zoneinfo` was added to the standard library)
- No pip install needed. Zero dependencies.

---

## Supported places

Three ways to name a location:

- **IANA names** (most precise): `America/New_York`, `Asia/Kolkata`, `Europe/London`
- **City names** (~90 covered): `tokyo`, `chennai`, `"new york"`, `london`, `singapore`, `dubai`
- **Abbreviations**: `EST`, `PST`, `IST`, `GMT`, `UTC`, `JST`, `CET`

Every IANA timezone works through its full name. The city shortlist covers the places people actually reference in day-to-day scheduling.

---

## What it doesn't do (yet)

Being upfront about the gaps:

- `overlap` and `handoff` apply one working-hours range to everyone. You can't set 9-5 for one person and 10-6 for another. Weekends and holidays aren't factored in either.
- `overlap` scans in whole-hour steps, so the window edges aren't minute-precise.
- Natural-language dates handle a defined set (`tomorrow`, `next friday`, `in 3 days`) but won't parse something like "the second Tuesday of next month."
- About 90 cities work by name. For anything else, use the IANA name (e.g. `Europe/Warsaw`).
- For a meeting that really can't go wrong, double-check against a second source.

---

## Contributing

PRs and issues are welcome. Some things that would make this better:

- More cities in the shortlist
- Per-person working hours in `overlap`
- Weekend and holiday awareness
- A market-hours tracker (stock exchange open/close times)
- Some kind of visual timeline output

---

## License

MIT. See [LICENSE](LICENSE).

---

If you've ever missed a call because of timezone math, or sent a meeting invite that landed at 3am someone's time, this might save you some grief.
