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

ALLOW_OVERRIDE_TOKEN = re.compile(r"^\s*--\s*allow-destructive\s*$", re.IGNORECASE | re.MULTILINE)

def strip_sql_comments(sql: str) -> str:
    sql = re.sub(r"--.*?$", "", sql, flags=re.MULTILINE)
    sql = re.sub(r"/\*.*?\*/", "", sql, flags=re.DOTALL)
    return sql

def scan_file(path: Path) -> list[str]:
    raw = path.read_text(encoding="utf-8", errors="ignore")

    # Allow explicit override for exceptional cases
    if ALLOW_OVERRIDE_TOKEN.search(raw):
        return []

    sql = strip_sql_comments(raw)
    issues = []

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

def main():
    if len(sys.argv) != 2:
        print("Usage: sql_guard.py <folder>")
        sys.exit(2)

    folder = Path(sys.argv[1])
    if not folder.exists():
        print(f"Folder not found: {folder}")
        sys.exit(2)

    failures = []
    for root, _, files in os.walk(folder):
        for f in files:
            if f.lower().endswith(".sql"):
                path = Path(root) / f
                issues = scan_file(path)
                if issues:
                    failures.append((path, issues))

    if failures:
        print("\n❌ Destructive SQL guardrails failed:\n")
        for path, issues in failures:
            print(f"- {path}")
            for issue in issues:
                print(f"  • {issue}")
            print("  → To override intentionally, add: -- allow-destructive\n")
        sys.exit(1)

    print("✅ Guardrails passed (no destructive SQL detected).")

if __name__ == "__main__":
    main()
