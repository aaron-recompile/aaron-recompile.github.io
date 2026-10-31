"""Monthly traffic report for the bitcoincoding.dev sites, with AI referrals called out.

Reads page counts and referrers from GoatCounter's API and writes a Markdown
report. The token is read from ~/.config/goatcounter/token (never from this
repo). Usage:

    python3 tools/ai_referrals.py                  # last 30 days
    python3 tools/ai_referrals.py --start 2026-11-01 --end 2026-11-30
    python3 tools/ai_referrals.py --out ~/reports  # also save YYYY-MM-DD.md there

AI assistants show up two ways: as a referring host (chatgpt.com, perplexity.ai)
or as a campaign, because ChatGPT and others append ?utm_source=<host> to the
links they cite. Both are matched below.
"""
import argparse
import datetime as dt
import json
import urllib.parse
import urllib.request
from pathlib import Path

API = "https://bitcoincoding.goatcounter.com/api/v0"
TOKEN_FILE = Path.home() / ".config/goatcounter/token"

# Hosts (or utm_source values) that mean "an AI assistant sent this visitor".
AI_SOURCES = {
    "chatgpt.com": "ChatGPT", "chat.openai.com": "ChatGPT", "openai.com": "ChatGPT",
    "perplexity.ai": "Perplexity", "www.perplexity.ai": "Perplexity",
    "claude.ai": "Claude", "gemini.google.com": "Gemini", "bard.google.com": "Gemini",
    "copilot.microsoft.com": "Copilot", "edgeservices.bing.com": "Copilot",
    "you.com": "You.com", "phind.com": "Phind", "kagi.com": "Kagi Assistant",
    "chat.deepseek.com": "DeepSeek", "grok.com": "Grok", "x.ai": "Grok",
    "meta.ai": "Meta AI", "chat.mistral.ai": "Mistral",
}


def get(path, **params):
    url = f"{API}/{path}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={
        "Authorization": "Bearer " + TOKEN_FILE.read_text().strip(),
        "Content-Type": "application/json",
    })
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def listing(path, key, **params):
    """One page of up to 100 rows; plenty for a site this size (flagged if cut)."""
    data = get(path, limit=100, **params)
    return data.get(key, []), bool(data.get("more"))


def ai_name(ref):
    host = ref.lower().split("/")[0].removeprefix("www.")
    for src, name in AI_SOURCES.items():
        if host == src.removeprefix("www.") or host.endswith("." + src):
            return name
    return None


def site_of(path):
    """Pages on the booklet and archive subdomains are recorded as /<host>/<path>."""
    first = path.strip("/").split("/")[0]
    return first if first.endswith("bitcoincoding.dev") else "bitcoincoding.dev"


def report(start, end):
    window = {"start": start.isoformat(), "end": end.isoformat()}
    hits, more_hits = listing("stats/hits", "hits", **window)
    refs, more_refs = listing("stats/toprefs", "stats", **window)

    total = sum(h["count"] for h in hits)
    by_site = {}
    for h in hits:
        by_site[site_of(h["path"])] = by_site.get(site_of(h["path"]), 0) + h["count"]

    ai = [(r, ai_name(r["name"])) for r in refs]
    ai = [(r, n) for r, n in ai if n]
    ai_total = sum(r["count"] for r, _ in ai)

    lines = [f"# bitcoincoding.dev traffic · {start} to {end}", "",
             f"- Visits: **{total}**", f"- From AI assistants: **{ai_total}**"]
    if more_hits or more_refs:
        lines.append("- Note: only the top 100 pages / referrers were read.")
    lines.append("")
    lines += ["## By site", "", "| Site | Visits |", "|---|---|"]
    lines += [f"| {s} | {c} |" for s, c in sorted(by_site.items(), key=lambda x: -x[1])]
    lines += ["", "## AI referrals", ""]
    if ai:
        lines += ["| Assistant | Source | Visits | Landing pages |", "|---|---|---|---|"]
        for r, name in sorted(ai, key=lambda x: -x[0]["count"]):
            try:
                pages = get(f"stats/toprefs/{urllib.parse.quote(r['name'], safe='')}", **window).get("stats", [])
                landing = ", ".join(f"{p['name']} ({p['count']})" for p in pages[:5])
            except Exception:
                landing = ""
            lines.append(f"| {name} | {r['name']} | {r['count']} | {landing} |")
    else:
        lines.append("None yet.")
    lines += ["", "## Top pages", "", "| Page | Visits |", "|---|---|"]
    lines += [f"| {h['path']} | {h['count']} |" for h in sorted(hits, key=lambda h: -h["count"])[:15]]
    lines += ["", "## All referrers", "", "| Referrer | Visits |", "|---|---|"]
    lines += [f"| {r['name'] or '(direct / unknown)'} | {r['count']} |" for r in refs[:25]]
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    today = dt.date.today()
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", type=dt.date.fromisoformat, default=today - dt.timedelta(days=30))
    ap.add_argument("--end", type=dt.date.fromisoformat, default=today + dt.timedelta(days=1))
    ap.add_argument("--out", type=Path, help="directory to also save the report in")
    a = ap.parse_args()
    md = report(a.start, a.end)
    print(md)
    if a.out:
        a.out.expanduser().mkdir(parents=True, exist_ok=True)
        (a.out.expanduser() / f"{a.end}.md").write_text(md)
