import os
import re
import sys
from pathlib import Path

# Patterns treated as destructive for an NHS-grade demo.
BLOCK_PATTERNS = [
    (re.compile(r"\bDROP\s+DATABASE\b", re.IGNORECASE), "DROP DATABASE"),
    (re.compile(r"\bDROP\s+SCHEMA\b", re.IGNORECASE), "DROP SCHEMA"),
    (re.compile(r"\bDROP\s+TABLE\b", re.IGNORECASE), "DROP TABLE"),
    (re.compile(r"\bTRUNCATE\s+TABLE\b", re.IGNORECASE), "TRUNCATE TABLE"),
    (re.compile(r"\bALTER\s+TABLE\b.*\bDROP\b", re.IGNORECASE), "ALTER TABLE ... DROP"),
    (re.compile(r"\bCREATE\s+OR\s+REPLACE\s+DATABASE\b", re.IGNORECASE), "CREATE OR REPLACE DATABASE"),
    (re.compile(r"\bCREATE\s+OR\s+REPLACE\s+SCHEMA\b", re.IGNORECASE), "CREATE OR REPLACE SCHEMA"),
]

# Exact line token:  -- allow-destructive
ALLOW_OVERRIDE_TOKEN = re.compile(
    r"^\s*--\s*allow-destructive\s*$",
    re.IGNORECASE | re.MULTILINE,
)


def strip_sql_comments(sql: str) -> str:
    """Remove line and block comments for pattern scanning."""
    sql = re.sub(r"--.*?$", "", sql, flags=re.MULTILINE)
    sql = re.sub(r"/\*.*?\*/", "", sql, flags=re.DOTALL)
    return sql


def scan_file(path: Path) -> list[str]:
    """Return list of issues found in a SQL file. Empty list means pass."""
    raw = path.read_text(encoding="utf-8", errors="ignore")

    # Allow explicit override for exceptional cases
    if ALLOW_OVERRIDE_TOKEN.search(raw):
        return []

    sql = strip_sql_comments(raw)
    issues: list[str] = []

    # Destructive patterns
    for pattern, label in BLOCK_PATTERNS:
        if pattern.search(sql):
            issues.append(f"{label} detected")

    # Basic risky DML heuristic: UPDATE/DELETE without WHERE
    statements = [s.strip() for s in sql.split(";") if s.strip()]
    for stmt in statements:
        up = stmt.upper()
        if up.startswith("UPDATE") and "WHERE" not in up:
            issues.append("UPDATE without WHERE detected")
        if up.startswith("DELETE") and "WHERE" not in up:
            issues.append("DELETE without WHERE detected")

    return issues


def iter_sql_files(target: Path) -> list[Path]:
    """Return a list of .sql files for a file or directory target."""
    if not target.exists():
        return []

    if target.is_file():
        return [target] if target.suffix.lower() == ".sql" else []

    sql_files: list[Path] = []
    for root, _, files in os.walk(target):
        for f in files:
            if f.lower().endswith(".sql"):
                sql_files.append(Path(root) / f)

    return sorted(sql_files)


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage:")
        print("  sql_guard.py <folder>")
        print("  sql_guard.py <file1.sql> <file2.sql> ...")
        sys.exit(2)

    args = [Path(a) for a in sys.argv[1:]]
    sql_files: list[Path] = []

    for a in args:
        sql_files.extend(iter_sql_files(a))

    # De-duplicate while preserving sort order
    sql_files = sorted(set(sql_files))

    if not sql_files:
        # If user passed files/dirs but none resolved to SQL, treat as misuse
        print("No .sql files found for the provided path(s):")
        for a in args:
            print(f"  - {a}")
        sys.exit(2)

    failures: list[tuple[Path, list[str]]] = []

    for path in sql_files:
        issues = scan_file(path)
        if issues:
            failures.append((path, issues))

    if failures:
        print("\n❌ Destructive SQL guardrails failed:\n")
        for path, issues in failures:
            print(f"- {path}")
            for issue in issues:
                print(f"  • {issue}")
            print("  → To override intentionally, add a line anywhere in the file:")
            print("    -- allow-destructive\n")
        sys.exit(1)

    print(f"✅ Guardrails passed ({len(sql_files)} SQL file(s) scanned).")


if __name__ == "__main__":
    main()

    print("✅ Guardrails passed (no destructive SQL detected).")

if __name__ == "__main__":
    main()
