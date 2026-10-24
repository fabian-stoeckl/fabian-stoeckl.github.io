"""Independent GitHub commit-time provenance for private preselection evidence.

This establishes a necessary ordering (private evidence committed before public
edition), not proof that the selector actually consumed those exact bytes.
"""
import datetime
import re


def parse_github_time(value):
    if not isinstance(value, str):
        raise ValueError("Missing GitHub commit timestamp")
    try:
        parsed = datetime.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("Invalid GitHub commit timestamp") from exc
    if parsed.tzinfo is None:
        raise ValueError("Commit timestamp lacks timezone")
    return parsed


def verify_commit_chronology(private_commits, publication_commit):
    """Fail closed if any of the four originals lacks an earlier commit."""
    required = ("candidates", "profile", "issues", "parameters")
    if not isinstance(private_commits, dict) or set(private_commits) != set(required):
        raise ValueError("Four original private commits required")
    if not isinstance(publication_commit, dict):
        raise ValueError("Public edition commit required")
    public_time = parse_github_time(publication_commit.get("timestamp"))
    public_sha = publication_commit.get("sha")
    if not isinstance(public_sha, str) or not re.fullmatch(r"[a-f0-9]{40}", public_sha):
        raise ValueError("Invalid public commit SHA")
    evidence = {}
    for key in required:
        item = private_commits[key]
        if not isinstance(item, dict):
            raise ValueError("Invalid private commit evidence: " + key)
        sha = item.get("sha")
        if not isinstance(sha, str) or not re.fullmatch(r"[a-f0-9]{40}", sha):
            raise ValueError("Invalid private commit SHA: " + key)
        instant = parse_github_time(item.get("timestamp"))
        if instant >= public_time:
            raise ValueError("Private original not earlier than public edition: " + key)
        evidence[key] = {"sha": sha, "timestamp": item["timestamp"]}
    return {"chronology_verified": True, "private_commits": evidence,
            "publication_commit": {"sha": public_sha, "timestamp": publication_commit["timestamp"]},
            "limitation": "Commit ordering does not prove selector execution or prevent earlier off-repository selection."}
