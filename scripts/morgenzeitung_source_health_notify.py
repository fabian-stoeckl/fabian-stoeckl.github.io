"""Notify once per confirmed publisher blackout; never confuse missing audits with outages.

Only the minimal public assessment (publisher/date/verdict) is used in issues.
Detailed article candidates, URLs and feedback remain in the PRIVATE repository.
GitHub's existing Actions token is used; no external service or extra token.
"""
import argparse
import datetime as dt
import json
import os
import subprocess

from scripts.morgenzeitung_source_health import REQUIRED_SOURCES

PREFIX = "[Morgenzeitung] Quellenzugang: "
AUDIT_TITLE = "[Morgenzeitung] Quellenüberwachung: Recherchenachweise fehlen"
AUDIT_START = dt.date(2026, 10, 30)


def plan_actions(report, open_issues):
    """Pure idempotent transition: [(action, number-or-None, title, body)]."""
    if not isinstance(report, dict) or not isinstance(open_issues, list):
        raise ValueError("Assessment and issues required")
    day = dt.date.fromisoformat(report["date"])
    verdict = report["verdict"]
    if verdict not in ("AUDIT_GAP", "ACCESS_GAPS", "NO_CONFIRMED_ACCESS_GAPS"):
        raise ValueError("Unrecognized source assessment verdict")
    if not all(isinstance(i, dict) and isinstance(i.get("number"), int)
               and isinstance(i.get("title"), str) for i in open_issues):
        raise ValueError("Invalid issue inventory")
    existing = {i["title"]: i["number"] for i in open_issues}
    chosen = set()
    operations = []

    if verdict == "ACCESS_GAPS":
        # An assessment lacking the independently checked date span is not an
        # actionable publisher outage. Fail instead of silently omitting alerts.
        if not isinstance(report.get("confirmed_blackout_details"), list):
            raise ValueError("Verified blackout details missing from private assessment")
        details = report["confirmed_blackout_details"]
        names = report.get("confirmed_blackouts")
        if (not isinstance(names, list) or not details
                or set(names) != {x.get("publisher") for x in details if isinstance(x, dict)}
                or len(names) != len(details)):
            raise ValueError("Mismatch between verified blackout names and dated evidence")
        for row in report.get("confirmed_blackout_details", []):
            publisher = row["publisher"]
            if publisher not in REQUIRED_SOURCES:
                raise ValueError("Unknown publisher in blackout notification")
            dates = row.get("dates")
            if (not isinstance(dates, list) or len(dates) != 3
                    or any(not isinstance(x, str) for x in dates)):
                raise ValueError("Three actual research dates required")
            title = PREFIX + publisher
            chosen.add(title)
            if title not in existing:
                body = (
                    "Unabhängige Quellenkontrolle: Für **" + publisher +
                    "** wurden trotz protokollierter Original- und Alternativrecherche "
                    "an drei aufeinanderfolgenden Tagen (" + ", ".join(dates) +
                    ") keine eigenständig verifizierbaren Artikel ermittelt.\n\n"
                    "Der Verlag bleibt dauerhaft im Recherchepool. Keine Aussage "
                    "über die Lesbarkeit aller Volltexte oder einen generellen "
                    "Ausfall des Verlags. Details liegen nur im privaten Audit. "
                    "Bitte alternative offizielle Verlagszugänge kontrollieren."
                )
                operations.append(("create", None, title, body))

    if verdict == "AUDIT_GAP":
        missing = report.get("missing_dates", [])
        if not isinstance(missing, list) or any(not isinstance(x, str) for x in missing):
            raise ValueError("Invalid audit gap")
        # During rollout, two old missing ledgers must not cause an immediate
        # artificial alert. From day 3, a real missing S3/S4 audit is actionable.
        if day >= AUDIT_START and missing and AUDIT_TITLE not in existing:
            operations.append(("create", None, AUDIT_TITLE,
                "Die unabhängige Quellenkontrolle findet keine vollständigen "
                "22-Verlags-Rechercheprotokolle für: " + ", ".join(missing) +
                ".\n\nDies ist **keine bestätigte Verlagssperre**. Bitte die "
                "automatische private S3/S4-Recherchearchivierung und das "
                "Zurücklesen prüfen; fehlende Belege dürfen nicht erfunden werden."))
        # Never close an earlier blackout merely because its evidence is missing.
        return operations

    if AUDIT_TITLE in existing:
        operations.append(("close", existing[AUDIT_TITLE], AUDIT_TITLE, "Vollständige Quellenprotokolle wieder vorhanden."))
    for title, issue_id in existing.items():
        if title.startswith(PREFIX) and title not in chosen:
            operations.append(("close", issue_id, title,
                               "Die aktuelle Drei-Tage-Prüfung bestätigt keinen durchgehenden Rechercheausfall mehr."))
    return operations


def run(report):
    if not os.environ.get("GH_TOKEN"):
        raise ValueError("Existing GitHub Actions issue token required")
    if os.environ.get("GITHUB_REPOSITORY") != "fabian-stoeckl/fabian-stoeckl.github.io":
        raise ValueError("Refusing to notify in another repository")
    result = subprocess.run(
        ["gh", "issue", "list", "--repo", os.environ["GITHUB_REPOSITORY"],
         "--state", "open", "--limit", "200", "--json", "number,title"],
        check=True, capture_output=True, text=True)
    existing = json.loads(result.stdout)
    actions = plan_actions(report, existing)
    for verb, number, title, body in actions:
        if verb == "create":
            subprocess.run(["gh", "issue", "create", "--repo", os.environ["GITHUB_REPOSITORY"],
                            "--title", title, "--body", body], check=True, capture_output=True, text=True)
        elif verb == "close":
            subprocess.run(["gh", "issue", "close", str(number), "--repo", os.environ["GITHUB_REPOSITORY"],
                            "--comment", body], check=True, capture_output=True, text=True)
    print(json.dumps({"verdict": report["verdict"], "actions": [
        {"action": v, "title": t} for v, _, t, _ in actions]}))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", required=True)
    args = parser.parse_args()
    with open(args.report, encoding="utf-8") as fd:
        run(json.load(fd))


if __name__ == "__main__":
    main()
