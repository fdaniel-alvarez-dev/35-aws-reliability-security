#!/usr/bin/env python3
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS_DIR = REPO_ROOT / "artifacts"


def run(cmd: list[str], *, cwd: Path | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        cmd,
        cwd=str(cwd or REPO_ROOT),
        env=os.environ.copy(),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )


def fail(message: str, *, output: str | None = None, code: int = 1) -> None:
    print(f"FAIL: {message}")
    if output:
        print(output.rstrip())
    raise SystemExit(code)


def load_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        fail(f"Invalid JSON: {path}", output=str(exc))
    return {}


def require_file(path: Path, description: str) -> None:
    if not path.exists():
        fail(f"Missing {description}: {path}")


def demo_mode() -> None:
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    report_path = ARTIFACTS_DIR / "mysql_guardrails.json"

    guard = run([sys.executable, "tools/mysql_guardrails.py", "--format", "json", "--out", str(report_path)])
    if guard.returncode != 0:
        fail("MySQL guardrails failed (demo mode must be offline).", output=guard.stdout)

    report = load_json(report_path)
    if report.get("summary", {}).get("errors", 0) != 0:
        fail("MySQL guardrails reported errors.", output=json.dumps(report.get("findings", []), indent=2))

    for required in ["NOTICE.md", "COMMERCIAL_LICENSE.md", "GOVERNANCE.md"]:
        require_file(REPO_ROOT / required, required)

    license_text = (REPO_ROOT / "LICENSE").read_text(encoding="utf-8", errors="replace")
    if "it.freddy.alvarez@gmail.com" not in license_text:
        fail("LICENSE must include the commercial licensing contact email.")

    print("OK: demo-mode tests passed (offline).")


def production_mode() -> None:
    if os.environ.get("PRODUCTION_TESTS_CONFIRM") != "1":
        fail(
            "Production-mode tests require an explicit opt-in.",
            output=(
                "Set `PRODUCTION_TESTS_CONFIRM=1` and rerun:\n"
                "  TEST_MODE=production PRODUCTION_TESTS_CONFIRM=1 python3 tests/run_tests.py\n"
            ),
            code=2,
        )

    docker_usable = False
    if shutil.which("docker") is not None:
        info = run(["docker", "info"])
        if info.returncode == 0:
            docker_usable = True
        else:
            fail(
                "Docker is installed but not usable (daemon/socket not accessible).",
                output=info.stdout,
                code=2,
            )
    else:
        fail("Docker is required for production-mode drills in this repo.", output="Install Docker and rerun.", code=2)

    try:
        up = run(["docker", "compose", "up", "-d", "--build"])
        if up.returncode != 0:
            fail("docker compose up failed.", output=up.stdout, code=2)

        seed = run(["bash", "scripts/seed_demo_data.sh"])
        if seed.returncode != 0:
            fail("Seeding demo data failed.", output=seed.stdout)

        check = run(["bash", "scripts/check_replication.sh"])
        if check.returncode != 0:
            fail("Replication check failed.", output=check.stdout)

        backup = run(["bash", "scripts/backup.sh"])
        if backup.returncode != 0:
            fail("Backup script failed.", output=backup.stdout)

        backups = sorted((REPO_ROOT / "artifacts" / "backups").glob("*.sql"))
        if not backups:
            fail("No backup files created under artifacts/backups/.")
        latest = backups[-1]

        verify = run(["bash", "scripts/backup_verify.sh", str(latest)])
        if verify.returncode != 0:
            fail("Backup verification failed.", output=verify.stdout)

        restore = run(["bash", "scripts/restore.sh"])
        if restore.returncode != 0:
            fail("Restore drill failed.", output=restore.stdout)

        print("OK: production-mode tests passed (docker integrations executed).")
    finally:
        if docker_usable:
            down = run(["docker", "compose", "down", "-v"])
            if down.returncode != 0:
                print("WARN: docker compose down failed (manual cleanup may be required).")
                print(down.stdout.rstrip())


def main() -> None:
    mode = os.environ.get("TEST_MODE", "demo").strip().lower()
    if mode not in {"demo", "production"}:
        fail("Invalid TEST_MODE. Expected 'demo' or 'production'.", code=2)

    if mode == "demo":
        demo_mode()
        return

    production_mode()


if __name__ == "__main__":
    main()

