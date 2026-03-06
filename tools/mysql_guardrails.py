#!/usr/bin/env python3
import argparse
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class Finding:
    severity: str  # ERROR | WARN | INFO
    rule_id: str
    message: str
    path: str | None = None


def add(findings: list[Finding], severity: str, rule_id: str, message: str, path: Path | None = None) -> None:
    findings.append(
        Finding(
            severity=severity,
            rule_id=rule_id,
            message=message,
            path=str(path.relative_to(REPO_ROOT)) if path else None,
        )
    )


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def summarize(findings: list[Finding]) -> dict:
    return {
        "errors": sum(1 for f in findings if f.severity == "ERROR"),
        "warnings": sum(1 for f in findings if f.severity == "WARN"),
        "info": sum(1 for f in findings if f.severity == "INFO"),
    }


def check_required_files(findings: list[Finding]) -> None:
    required = [
        REPO_ROOT / "README.md",
        REPO_ROOT / "docker-compose.yml",
        REPO_ROOT / "docs" / "runbooks" / "backup-and-restore.md",
        REPO_ROOT / "scripts" / "backup.sh",
        REPO_ROOT / "scripts" / "restore.sh",
        REPO_ROOT / "scripts" / "check_replication.sh",
        REPO_ROOT / "scripts" / "seed_demo_data.sh",
        REPO_ROOT / "scripts" / "backup_verify.sh",
    ]
    for p in required:
        if not p.exists():
            add(findings, "ERROR", "repo.required", "Required file is missing.", p)


def check_compose_is_mysql(findings: list[Finding]) -> None:
    compose = REPO_ROOT / "docker-compose.yml"
    if not compose.exists():
        return
    text = read_text(compose)
    if "mysql-primary" not in text or "mysql-replica" not in text:
        add(findings, "ERROR", "compose.mysql_services", "docker-compose.yml should define mysql-primary and mysql-replica services.", compose)

    images = re.findall(r"(?m)^\\s*image:\\s*([^\\s#]+)\\s*$", text)
    for img in images:
        if ":" not in img:
            add(findings, "WARN", "compose.image_tag", f"Image has no tag pinned: {img}", compose)
        if img.endswith(":latest"):
            add(findings, "ERROR", "compose.latest", f"Image uses floating latest tag: {img}", compose)


def check_restore_is_isolated(findings: list[Finding]) -> None:
    restore = REPO_ROOT / "scripts" / "restore.sh"
    if not restore.exists():
        return
    text = read_text(restore)
    if "appdb_verify" not in text:
        add(findings, "WARN", "restore.verify_db", "Restore should use an isolated verification database (e.g., appdb_verify).", restore)


def check_readme_mentions(findings: list[Finding]) -> None:
    readme = REPO_ROOT / "README.md"
    if not readme.exists():
        return
    text = read_text(readme)
    if "MySQL" not in text:
        add(findings, "WARN", "docs.mysql", "README should explicitly mention MySQL.", readme)
    if "TEST_MODE" not in text:
        add(findings, "WARN", "docs.test_mode", "README should document TEST_MODE=demo|production.", readme)


def check_gitignore(findings: list[Finding]) -> None:
    ignore = REPO_ROOT / ".gitignore"
    if not ignore.exists():
        add(findings, "WARN", "gitignore.missing", ".gitignore is missing; add rules for artifacts and private inputs.")
        return
    text = read_text(ignore)
    if ".[0-9][0-9]_*.txt" not in text:
        add(findings, "WARN", "gitignore.job_desc", "Ignore private job description .txt inputs.", ignore)


def main() -> int:
    parser = argparse.ArgumentParser(description="Offline, deterministic MySQL lab guardrails for this repo.")
    parser.add_argument("--format", choices=["text", "json"], default="text")
    parser.add_argument("--out", default="", help="Write output to a file (optional).")
    args = parser.parse_args()

    findings: list[Finding] = []
    check_required_files(findings)
    check_compose_is_mysql(findings)
    check_restore_is_isolated(findings)
    check_readme_mentions(findings)
    check_gitignore(findings)

    report = {"summary": summarize(findings), "findings": [asdict(f) for f in findings]}
    if args.format == "json":
        output = json.dumps(report, indent=2, sort_keys=True)
    else:
        lines = []
        for f in findings:
            where = f" ({f.path})" if f.path else ""
            lines.append(f"{f.severity} {f.rule_id}{where}: {f.message}")
        lines.append("")
        lines.append(f"Summary: {report['summary']}")
        output = "\n".join(lines)

    if args.out:
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(output + "\n", encoding="utf-8")
    else:
        print(output)

    return 1 if report["summary"]["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())

