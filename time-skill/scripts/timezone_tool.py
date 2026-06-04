#!/usr/bin/env python3
"""
timezone_tool.py — DST-aware time and timezone helper.

Uses the system clock (accurate UTC) + Python's zoneinfo standard library.
No external API or network access required. Handles Daylight Saving Time
automatically because zoneinfo carries the full IANA timezone database.

Commands:
  now      <place>                          Current date+time in a place
  convert  <time> <from> <to> [when]        Convert a time between two zones (DST-aware)
  compare  <place> <place> ...              Current time across many places at once
  overlap  <place> ... [--hours START END]  Find overlapping working hours
  snippet  <time> <from> <t1> <t2> ... [--when WHEN]
                                            One-line "3pm PT / 6pm ET / ..." for messages
  ics      <time> <from> --title T [--when WHEN] [--duration MIN] [--out PATH]
                                            Generate a calendar (.ics) invite file
  dst      <place> [place2] [--months N]    Show upcoming Daylight-Saving changes
  handoff  <place> ... [--hours START END]  Who's working now + next follow-the-sun handoff
  epoch    <value> [place ...]              Convert a Unix timestamp to human time

"when"/"--when" accepts: an ISO date (YYYY-MM-DD) OR natural language —
  today, tomorrow, yesterday, "day after tomorrow", "in 3 days", "2 days ago",
  a weekday (monday..sunday), "this friday", or "next friday".
  Weekday rule: bare/"this" = soonest matching day (today counts);
  "next" = the following week's occurrence. The resolved date is always printed
  so you can verify it at a glance.

A "place" can be:
  - an IANA name        e.g. Asia/Kolkata, America/New_York, Europe/London
  - a common city name  e.g. chennai, london, "new york", tokyo
  - a common abbrev     e.g. IST, EST, PST, GMT, UTC, JST, CET
"""

import sys
import re
import uuid
import argparse
from datetime import datetime, timezone, timedelta, date
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

# ---------------------------------------------------------------------------
# Place resolution data
# ---------------------------------------------------------------------------

CITY_TO_IANA = {
    "chennai": "Asia/Kolkata", "mumbai": "Asia/Kolkata", "delhi": "Asia/Kolkata",
    "bangalore": "Asia/Kolkata", "bengaluru": "Asia/Kolkata", "kolkata": "Asia/Kolkata",
    "hyderabad": "Asia/Kolkata", "pune": "Asia/Kolkata", "india": "Asia/Kolkata",
    "thoothukudi": "Asia/Kolkata", "tuticorin": "Asia/Kolkata",
    "new york": "America/New_York", "nyc": "America/New_York", "boston": "America/New_York",
    "washington": "America/New_York", "atlanta": "America/New_York", "miami": "America/New_York",
    "chicago": "America/Chicago", "dallas": "America/Chicago", "houston": "America/Chicago",
    "denver": "America/Denver", "phoenix": "America/Phoenix",
    "los angeles": "America/Los_Angeles", "la": "America/Los_Angeles",
    "san francisco": "America/Los_Angeles", "sf": "America/Los_Angeles",
    "seattle": "America/Los_Angeles", "san diego": "America/Los_Angeles",
    "london": "Europe/London", "uk": "Europe/London", "manchester": "Europe/London",
    "dublin": "Europe/Dublin", "lisbon": "Europe/Lisbon",
    "paris": "Europe/Paris", "berlin": "Europe/Berlin", "madrid": "Europe/Madrid",
    "rome": "Europe/Rome", "amsterdam": "Europe/Amsterdam", "brussels": "Europe/Brussels",
    "zurich": "Europe/Zurich", "vienna": "Europe/Vienna", "stockholm": "Europe/Stockholm",
    "moscow": "Europe/Moscow", "istanbul": "Europe/Istanbul", "athens": "Europe/Athens",
    "dubai": "Asia/Dubai", "abu dhabi": "Asia/Dubai", "uae": "Asia/Dubai",
    "riyadh": "Asia/Riyadh", "doha": "Asia/Qatar", "tel aviv": "Asia/Jerusalem",
    "jerusalem": "Asia/Jerusalem",
    "tokyo": "Asia/Tokyo", "osaka": "Asia/Tokyo", "japan": "Asia/Tokyo",
    "singapore": "Asia/Singapore", "hong kong": "Asia/Hong_Kong", "hongkong": "Asia/Hong_Kong",
    "beijing": "Asia/Shanghai", "shanghai": "Asia/Shanghai", "china": "Asia/Shanghai",
    "seoul": "Asia/Seoul", "korea": "Asia/Seoul",
    "bangkok": "Asia/Bangkok", "thailand": "Asia/Bangkok",
    "jakarta": "Asia/Jakarta", "manila": "Asia/Manila",
    "kuala lumpur": "Asia/Kuala_Lumpur", "karachi": "Asia/Karachi", "pakistan": "Asia/Karachi",
    "dhaka": "Asia/Dhaka", "bangladesh": "Asia/Dhaka",
    "sydney": "Australia/Sydney", "melbourne": "Australia/Melbourne",
    "perth": "Australia/Perth", "auckland": "Pacific/Auckland",
    "toronto": "America/Toronto", "vancouver": "America/Vancouver",
    "mexico city": "America/Mexico_City", "sao paulo": "America/Sao_Paulo",
    "buenos aires": "America/Argentina/Buenos_Aires",
    "lagos": "Africa/Lagos", "nairobi": "Africa/Nairobi",
    "johannesburg": "Africa/Johannesburg", "cairo": "Africa/Cairo",
}

ABBREV_TO_IANA = {
    "utc": "UTC", "gmt": "Etc/GMT", "z": "UTC",
    "ist": "Asia/Kolkata",
    "est": "America/New_York", "edt": "America/New_York", "et": "America/New_York",
    "cst": "America/Chicago", "cdt": "America/Chicago", "ct": "America/Chicago",
    "mst": "America/Denver", "mdt": "America/Denver", "mt": "America/Denver",
    "pst": "America/Los_Angeles", "pdt": "America/Los_Angeles", "pt": "America/Los_Angeles",
    "bst": "Europe/London",
    "cet": "Europe/Paris", "cest": "Europe/Paris",
    "eet": "Europe/Athens", "eest": "Europe/Athens",
    "jst": "Asia/Tokyo", "kst": "Asia/Seoul",
    "sgt": "Asia/Singapore", "hkt": "Asia/Hong_Kong",
    "aest": "Australia/Sydney", "aedt": "Australia/Sydney",
    "nzst": "Pacific/Auckland", "nzdt": "Pacific/Auckland",
    "gst": "Asia/Dubai",
}

AMBIGUOUS_NOTE = {
    "ist": "IST is ambiguous (India / Israel / Ireland) — assumed India (Asia/Kolkata).",
    "cst": "CST is ambiguous (US Central / China / Cuba) — assumed US Central.",
}

SEASONAL_ABBREVS = {
    "est", "edt", "et", "cst", "cdt", "ct", "mst", "mdt", "mt",
    "pst", "pdt", "pt", "bst", "cet", "cest", "eet", "eest",
    "aest", "aedt", "nzst", "nzdt",
}

WEEKDAYS = {
    "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
    "friday": 4, "saturday": 5, "sunday": 6,
    "mon": 0, "tue": 1, "tues": 1, "wed": 2, "weds": 2,
    "thu": 3, "thur": 3, "thurs": 3, "fri": 4, "sat": 5, "sun": 6,
}


def resolve(place: str):
    """Resolve a place string to (ZoneInfo, canonical_label, note_or_None)."""
    raw = place.strip()
    key = raw.lower()
    note = AMBIGUOUS_NOTE.get(key)

    if key in ABBREV_TO_IANA:
        iana = ABBREV_TO_IANA[key]
        if key in SEASONAL_ABBREVS and not note:
            note = (f"'{raw.upper()}' interpreted as a Daylight-Saving-aware zone "
                    f"({iana}); the live offset reflects whatever is in effect on the date shown.")
        return ZoneInfo(iana), iana, note

    for cand in (raw, raw.replace(" ", "_")):
        try:
            zi = ZoneInfo(cand)
            return zi, cand, note
        except (ZoneInfoNotFoundError, ValueError, KeyError):
            pass

    if key in CITY_TO_IANA:
        iana = CITY_TO_IANA[key]
        return ZoneInfo(iana), iana, note

    raise ValueError(
        f"Could not resolve '{place}'. Try an IANA name like 'America/New_York', "
        f"a major city like 'tokyo', or an abbreviation like 'EST'."
    )


def parse_time(s: str):
    """Parse a flexible time string into (hour, minute). Accepts 3pm, 3:30 PM, 15:00."""
    t = s.strip().lower().replace(" ", "")
    ampm = None
    if t.endswith("am"):
        ampm, t = "am", t[:-2]
    elif t.endswith("pm"):
        ampm, t = "pm", t[:-2]

    if ":" in t:
        hh, mm = t.split(":", 1)
        hour, minute = int(hh), int(mm)
    else:
        hour, minute = int(t), 0

    if ampm == "pm" and hour != 12:
        hour += 12
    elif ampm == "am" and hour == 12:
        hour = 0

    if not (0 <= hour <= 23 and 0 <= minute <= 59):
        raise ValueError(f"Invalid time '{s}'. Use formats like 3pm, 3:30pm, or 15:00.")
    return hour, minute


def parse_when(phrase, today: date):
    """Resolve a date phrase (ISO or natural language) into a date object."""
    p = " ".join(phrase.strip().lower().split())

    try:
        return datetime.strptime(p, "%Y-%m-%d").date()
    except ValueError:
        pass

    fixed = {
        "today": 0, "tonight": 0,
        "tomorrow": 1, "tmrw": 1, "tmr": 1,
        "yesterday": -1,
        "day after tomorrow": 2, "overmorrow": 2,
        "day before yesterday": -2,
    }
    if p in fixed:
        return today + timedelta(days=fixed[p])

    m = re.fullmatch(r"in (\d+) days?", p)
    if m:
        return today + timedelta(days=int(m.group(1)))
    m = re.fullmatch(r"(\d+) days? ago", p)
    if m:
        return today - timedelta(days=int(m.group(1)))

    nxt = p.startswith("next ")
    ths = p.startswith("this ")
    wd_word = p[5:] if (nxt or ths) else p
    if wd_word in WEEKDAYS:
        target = WEEKDAYS[wd_word]
        incl = (target - today.weekday()) % 7  # 0..6 (0 == today)
        coming = today + timedelta(days=incl)
        if nxt:
            return coming + timedelta(days=7)
        return coming

    raise ValueError(
        f"Could not understand date '{phrase}'. Use YYYY-MM-DD or phrases like "
        f"'tomorrow', 'next friday', 'in 3 days'."
    )


def fmt(dt: datetime):
    """Human-friendly datetime label, e.g. 'Thu, 04 Jun 2026, 09:57 (IST, UTC+05:30)'."""
    return f"{dt:%a, %d %b %Y, %H:%M} ({dt.tzname()}, {offset_str(dt.utcoffset())})"


def offset_str(off: timedelta):
    total = int((off or timedelta(0)).total_seconds())
    sign = "+" if total >= 0 else "-"
    total = abs(total)
    return f"UTC{sign}{total // 3600:02d}:{(total % 3600) // 60:02d}"


def time12(dt: datetime):
    """12-hour time with no leading zero, e.g. '3:00 PM' or '11:30 AM'."""
    s = dt.strftime("%I:%M %p")
    return s[1:] if s.startswith("0") else s


def day_shift_tag(src: datetime, dst: datetime):
    shift = (dst.date() - src.date()).days
    if shift == 1:
        return " (+1d)"
    if shift == -1:
        return " (-1d)"
    if shift != 0:
        return f" ({shift:+d}d)"
    return ""


# ---------------------------------------------------------------------------
# Core commands
# ---------------------------------------------------------------------------

def cmd_now(places):
    print("Current time:")
    for p in places:
        zi, label, note = resolve(p)
        print(f"  {p:<16} → {fmt(datetime.now(zi))}   [{label}]")
        if note:
            print(f"  {'':<16}   ⚠ {note}")


def cmd_convert(time_str, from_place, to_place, when=None):
    from_zi, from_label, from_note = resolve(from_place)
    to_zi, to_label, to_note = resolve(to_place)
    hour, minute = parse_time(time_str)
    base_date = parse_when(when, datetime.now(from_zi).date()) if when else datetime.now(from_zi).date()

    src = datetime(base_date.year, base_date.month, base_date.day, hour, minute, tzinfo=from_zi)
    dst = src.astimezone(to_zi)

    print("Conversion:")
    print(f"  {fmt(src)}   [{from_label}]")
    print(f"  = {fmt(dst)}{day_shift_tag(src, dst)}   [{to_label}]")
    for n in (from_note, to_note):
        if n:
            print(f"  ⚠ {n}")


def cmd_compare(places):
    rows = []
    for p in places:
        zi, label, note = resolve(p)
        rows.append((p, datetime.now(zi), label, note))
    rows.sort(key=lambda r: r[1].utcoffset() or timedelta(0))
    print("Time comparison (sorted west → east):")
    for p, now, label, note in rows:
        print(f"  {p:<16} → {fmt(now)}   [{label}]")
        if note:
            print(f"  {'':<16}   ⚠ {note}")


def cmd_overlap(places, work_start=9, work_end=18):
    zones = []
    for p in places:
        zi, label, note = resolve(p)
        zones.append((p, zi, label))
        if note:
            print(f"⚠ {note}")

    today = datetime.now(timezone.utc).date()
    overlap = [h for h in range(24)
               if all(work_start <= datetime(today.year, today.month, today.day, h, tzinfo=timezone.utc)
                      .astimezone(zi).hour < work_end for _, zi, _ in zones)]

    print(f"\nWorking-hours overlap (working day = {work_start:02d}:00–{work_end:02d}:00 local):")
    if not overlap:
        print("  ❌ No hour falls within working hours for ALL locations simultaneously.")
        print("     Consider asynchronous handoffs or shifting one team's hours.")
        return

    start = datetime(today.year, today.month, today.day, overlap[0], tzinfo=timezone.utc)
    end = datetime(today.year, today.month, today.day, tzinfo=timezone.utc) + timedelta(hours=overlap[-1] + 1)
    print(f"  ✅ Overlap window ({len(overlap)}h) — everyone is working during:")
    for p, zi, label in zones:
        print(f"     {p:<16} {start.astimezone(zi):%H:%M}–{end.astimezone(zi):%H:%M}   [{label}]")


# ---------------------------------------------------------------------------
# New commands
# ---------------------------------------------------------------------------

def cmd_snippet(time_str, from_place, targets, when=None):
    from_zi, from_label, from_note = resolve(from_place)
    hour, minute = parse_time(time_str)
    base_date = parse_when(when, datetime.now(from_zi).date()) if when else datetime.now(from_zi).date()
    src = datetime(base_date.year, base_date.month, base_date.day, hour, minute, tzinfo=from_zi)

    parts = [f"{time12(src)} {from_place}"]
    notes = [from_note] if from_note else []
    for t in targets:
        zi, label, note = resolve(t)
        dst = src.astimezone(zi)
        parts.append(f"{time12(dst)} {t}{day_shift_tag(src, dst)}")
        if note:
            notes.append(note)

    print("Copy-paste snippet:")
    print("  " + "  /  ".join(parts))
    print(f"\n(Date: {src:%a, %d %b %Y} in {from_label})")
    for n in notes:
        print(f"⚠ {n}")


def cmd_ics(time_str, from_place, title, duration=30, when=None, out=None):
    from_zi, from_label, from_note = resolve(from_place)
    hour, minute = parse_time(time_str)
    base_date = parse_when(when, datetime.now(from_zi).date()) if when else datetime.now(from_zi).date()
    src = datetime(base_date.year, base_date.month, base_date.day, hour, minute, tzinfo=from_zi)
    start_utc = src.astimezone(timezone.utc)
    end_utc = start_utc + timedelta(minutes=duration)
    stamp = datetime.now(timezone.utc)

    def z(dt):
        return dt.strftime("%Y%m%dT%H%M%SZ")

    ics = "\r\n".join([
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//time-skill//time-skill//EN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        "BEGIN:VEVENT",
        f"UID:{uuid.uuid4()}@time-skill",
        f"DTSTAMP:{z(stamp)}",
        f"DTSTART:{z(start_utc)}",
        f"DTEND:{z(end_utc)}",
        f"SUMMARY:{title}",
        f"DESCRIPTION:Starts {time12(src)} {from_label} ({fmt(src)})",
        "END:VEVENT",
        "END:VCALENDAR",
        "",
    ])

    out_path = out or "/tmp/invite.ics"
    with open(out_path, "w", newline="") as f:
        f.write(ics)

    print(f"Calendar invite written to: {out_path}")
    print(f"  Event:    {title}")
    print(f"  Starts:   {fmt(src)}   [{from_label}]")
    print(f"  Duration: {duration} min  (ends {time12(src.astimezone(from_zi) + timedelta(minutes=duration))} local)")
    print(f"  Stored in UTC as {z(start_utc)} → universally compatible with any calendar app.")
    if from_note:
        print(f"⚠ {from_note}")


def _transitions(zi, start: date, days: int):
    """Detect DST/offset transitions by sampling local noon each day."""
    out = []
    prev = datetime(start.year, start.month, start.day, 12, tzinfo=zi)
    prev_off = prev.utcoffset()
    for i in range(1, days + 1):
        d = start + timedelta(days=i)
        cur = datetime(d.year, d.month, d.day, 12, tzinfo=zi)
        off = cur.utcoffset()
        if off != prev_off:
            out.append((d, prev_off, off, prev.tzname(), cur.tzname()))
            prev_off, prev = off, cur
    return out


def cmd_dst(places, months=12):
    today = datetime.now(timezone.utc).date()
    days = int(months * 30.5)

    for p in places:
        zi, label, note = resolve(p)
        if note:
            print(f"⚠ {note}")
        trans = _transitions(zi, today, days)
        print(f"\nUpcoming clock changes for {p} [{label}] (next {months} months):")
        if not trans:
            print("  None — this zone has no Daylight Saving changes in the window.")
        for d, o1, o2, n1, n2 in trans:
            direction = "forward" if (o2 > o1) else "back"
            print(f"  {d:%a, %d %b %Y}: clocks go {direction}  "
                  f"{n1} ({offset_str(o1)}) → {n2} ({offset_str(o2)})")

    if len(places) == 2:
        za = resolve(places[0])[0]
        zb = resolve(places[1])[0]

        def diff_on(d):
            a = datetime(d.year, d.month, d.day, 12, tzinfo=za).utcoffset()
            b = datetime(d.year, d.month, d.day, 12, tzinfo=zb).utcoffset()
            return b - a

        cur = diff_on(today)
        changes = []
        prev = cur
        for i in range(1, days + 1):
            d = today + timedelta(days=i)
            dd = diff_on(d)
            if dd != prev:
                changes.append((d, prev, dd))
                prev = dd
        total = int(cur.total_seconds())
        if total == 0:
            rel = f"in sync with {places[0]}"
        elif total > 0:
            rel = f"{_humandelta(abs(cur))} ahead of {places[0]}"
        else:
            rel = f"{_humandelta(abs(cur))} behind {places[0]}"
        print(f"\nGap between {places[0]} and {places[1]} today: {places[1]} is {rel}.")
        if changes:
            print("  ⚠ This gap CHANGES on:")
            for d, before, after in changes:
                print(f"     {d:%a, %d %b %Y}: {_gap_phrase(before)} → {_gap_phrase(after)} "
                      f"(recurring meetings shift by {_humandelta(after-before)})")
        else:
            print("  The gap stays constant over this window.")


def _humandelta(td: timedelta):
    total = int(td.total_seconds())
    sign = "" if total >= 0 else "-"
    total = abs(total)
    h, m = total // 3600, (total % 3600) // 60
    return f"{sign}{h}h" + (f"{m:02d}m" if m else "")


def _gap_phrase(td: timedelta):
    """Direction-aware gap, e.g. '4h30m ahead', '5h30m behind', or 'in sync'."""
    total = int(td.total_seconds())
    if total == 0:
        return "in sync"
    word = "ahead" if total > 0 else "behind"
    return f"{_humandelta(abs(td))} {word}"


def cmd_handoff(places, work_start=9, work_end=18):
    now_utc = datetime.now(timezone.utc)
    rows = []
    for p in places:
        zi, label, note = resolve(p)
        if note:
            print(f"⚠ {note}")
        local = now_utc.astimezone(zi)
        working = work_start <= local.hour < work_end
        start_today = local.replace(hour=work_start, minute=0, second=0, microsecond=0)
        end_today = local.replace(hour=work_end, minute=0, second=0, microsecond=0)
        next_start = start_today if local < start_today else start_today + timedelta(days=1)
        mins_to_start = int((next_start - local).total_seconds() // 60)
        mins_to_end = int((end_today - local).total_seconds() // 60) if working else None
        rows.append((p, label, local, working, mins_to_start, mins_to_end))

    rows.sort(key=lambda r: (not r[3], r[2].hour))
    print(f"\nFollow-the-sun status (working day = {work_start:02d}:00–{work_end:02d}:00 local):")
    for p, label, local, working, _, mte in rows:
        status = "🟢 ONLINE " if working else "⚪ off    "
        tail = f"(off in {_mins(mte)})" if working and mte is not None else ""
        print(f"  {status} {p:<16} {local:%H:%M} local  {tail}   [{label}]")

    online = [r for r in rows if r[3]]
    offline = [r for r in rows if not r[3]]
    print()
    if online:
        soonest_off = min(online, key=lambda r: r[5])
        print(f"  Currently covering: {', '.join(r[0] for r in online)}.")
        print(f"  Earliest to go offline: {soonest_off[0]} in {_mins(soonest_off[5])}.")
    else:
        print("  Nobody is currently within working hours.")
    if offline:
        next_on = min(offline, key=lambda r: r[4])
        print(f"  Next to come online: {next_on[0]} in {_mins(next_on[4])}.")


def _mins(m):
    if m is None:
        return "—"
    return (f"{m // 60}h" if m >= 60 else "") + (f"{m % 60}m" if m % 60 or m < 60 else "")


def cmd_epoch(value, places):
    s = str(value).strip()
    if not re.fullmatch(r"-?\d+", s):
        raise ValueError(f"'{value}' is not a Unix timestamp (expected an integer).")
    n = int(s)
    digits = len(s.lstrip("-"))
    if digits >= 16:
        secs, unit = n / 1_000_000, "microseconds"
    elif digits >= 13:
        secs, unit = n / 1000, "milliseconds"
    else:
        secs, unit = n, "seconds"

    dt_utc = datetime.fromtimestamp(secs, tz=timezone.utc)
    print(f"Unix timestamp {n} (interpreted as {unit}):")
    print(f"  {fmt(dt_utc)}   [UTC]")
    for p in places:
        zi, label, note = resolve(p)
        print(f"  {fmt(dt_utc.astimezone(zi))}   [{label}]")
        if note:
            print(f"  ⚠ {note}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="DST-aware time and timezone helper.")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("now"); p.add_argument("places", nargs="+")

    p = sub.add_parser("convert")
    p.add_argument("time"); p.add_argument("from_place"); p.add_argument("to_place")
    p.add_argument("when", nargs="?", default=None)

    p = sub.add_parser("compare"); p.add_argument("places", nargs="+")

    p = sub.add_parser("overlap"); p.add_argument("places", nargs="+")
    p.add_argument("--hours", nargs=2, type=int, metavar=("START", "END"), default=[9, 18])

    p = sub.add_parser("snippet")
    p.add_argument("time"); p.add_argument("from_place")
    p.add_argument("targets", nargs="+")
    p.add_argument("--when", default=None)

    p = sub.add_parser("ics")
    p.add_argument("time"); p.add_argument("from_place")
    p.add_argument("--title", required=True)
    p.add_argument("--when", default=None)
    p.add_argument("--duration", type=int, default=30)
    p.add_argument("--out", default=None)

    p = sub.add_parser("dst"); p.add_argument("places", nargs="+")
    p.add_argument("--months", type=int, default=12)

    p = sub.add_parser("handoff"); p.add_argument("places", nargs="+")
    p.add_argument("--hours", nargs=2, type=int, metavar=("START", "END"), default=[9, 18])

    p = sub.add_parser("epoch")
    p.add_argument("value"); p.add_argument("places", nargs="*", default=[])

    args = parser.parse_args()
    try:
        if args.command == "now":
            cmd_now(args.places)
        elif args.command == "convert":
            cmd_convert(args.time, args.from_place, args.to_place, args.when)
        elif args.command == "compare":
            cmd_compare(args.places)
        elif args.command == "overlap":
            cmd_overlap(args.places, args.hours[0], args.hours[1])
        elif args.command == "snippet":
            cmd_snippet(args.time, args.from_place, args.targets, args.when)
        elif args.command == "ics":
            cmd_ics(args.time, args.from_place, args.title, args.duration, args.when, args.out)
        elif args.command == "dst":
            cmd_dst(args.places, args.months)
        elif args.command == "handoff":
            cmd_handoff(args.places, args.hours[0], args.hours[1])
        elif args.command == "epoch":
            cmd_epoch(args.value, args.places)
    except (ValueError, ZoneInfoNotFoundError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
