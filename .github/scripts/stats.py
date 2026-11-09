"""Generates assets/stats.svg from the GitHub contribution calendar."""

import datetime as dt
import json
import os
import urllib.request

USER = "Niyoru404"
QUERY = """query($login: String!) { user(login: $login) { contributionsCollection {
  totalCommitContributions restrictedContributionsCount
  contributionCalendar { weeks { contributionDays { date contributionCount contributionLevel } } }
} } }"""
LEVELS = {
    "NONE": "#141414",
    "FIRST_QUARTILE": "#3a3a3a",
    "SECOND_QUARTILE": "#6e6e6e",
    "THIRD_QUARTILE": "#a8a8a8",
    "FOURTH_QUARTILE": "#ededed",
}
MONO = "ui-monospace,SFMono-Regular,Menlo,Consolas,monospace"
STEP = 16


def fetch() -> dict:
    body = json.dumps({"query": QUERY, "variables": {"login": USER}}).encode()
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=body,
        headers={"Authorization": f"bearer {os.environ['GITHUB_TOKEN']}", "User-Agent": "profile-stats"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.load(resp)
    if "errors" in data:
        raise SystemExit(data["errors"])
    return data["data"]["user"]["contributionsCollection"]


def streaks(days: list[dict]) -> tuple[int, int]:
    longest = run = 0
    for day in days:
        run = run + 1 if day["contributionCount"] else 0
        longest = max(longest, run)
    # today does not break the streak while it is still empty
    recent = days[:-1] if not days[-1]["contributionCount"] else days
    current = 0
    for day in reversed(recent):
        if not day["contributionCount"]:
            break
        current += 1
    return current, longest


def stat(x: int, value: object, label: str) -> str:
    return (
        f'<text x="{x}" y="96" font-size="38" font-weight="700" fill="#ededed">{value}</text>'
        f'<text x="{x}" y="120" font-size="12" letter-spacing="2" fill="#77777f">{label}</text>'
    )


def render(data: dict) -> str:
    weeks = data["contributionCalendar"]["weeks"]
    days = [d for w in weeks for d in w["contributionDays"]]
    commits = data["totalCommitContributions"] + data["restrictedContributionsCount"]
    current, longest = streaks(days)
    best = max(d["contributionCount"] for d in days)

    x0, y0 = 26, 176
    parts = []
    seen = None
    for col, week in enumerate(weeks[-53:]):
        first = dt.date.fromisoformat(week["contributionDays"][0]["date"])
        if first.month != seen and first.day <= 7 and col < 52:
            parts.append(f'<text x="{x0 + col * STEP}" y="{y0 - 10}" font-size="11" fill="#55555c">{first:%b}</text>')
            seen = first.month
        for day in week["contributionDays"]:
            row = dt.date.fromisoformat(day["date"]).isoweekday() % 7
            parts.append(
                f'<rect x="{x0 + col * STEP}" y="{y0 + row * STEP}" width="13" height="13" rx="3" '
                f'fill="{LEVELS[day["contributionLevel"]]}"/>'
            )

    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 900 310" role="img" aria-label="{commits} commits in the last year. Current streak {current} days, longest streak {longest} days.">
  <rect width="900" height="310" rx="10" fill="#000"/>
  <rect x=".5" y=".5" width="899" height="309" rx="10" fill="none" stroke="#222"/>
  <g font-family="{MONO}">
    <path transform="translate(26 22) scale(.75)" d="M12 2a10 10 0 1 0 10 10 8 8 0 0 1-10-10z" fill="#d8d8d8"/>
    <text x="52" y="38" font-size="14" letter-spacing="3" fill="#a8a8a8">COMMIT ACTIVITY</text>
    {stat(26, commits, "COMMITS / YEAR")}
    {stat(246, current, "CURRENT STREAK")}
    {stat(466, longest, "LONGEST STREAK")}
    {stat(686, best, "BEST DAY")}
    {"".join(parts)}
  </g>
</svg>
"""


if __name__ == "__main__":
    with open("assets/stats.svg", "w", encoding="utf-8") as f:
        f.write(render(fetch()))
