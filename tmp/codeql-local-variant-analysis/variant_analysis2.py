#!/usr/bin/env python3
import argparse
import subprocess
import sys
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed
import os

GITHUB_BASE = "https://github.com"

def run(cmd, cwd=None):
    subprocess.run(cmd, cwd=cwd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

def safe_repo_dir(org_repo: str) -> str:
    return org_repo.replace("/", "-")

def process_repo(
    org_repo: str,
    language: str,
    query: str,
    root: str,
    sarif_format: str
):
    root = Path(root)
    repos_dir = root / "repos"
    db_dir = root / "databases"
    results_dir = root / "results"

    repo_dir = repos_dir / safe_repo_dir(org_repo)
    database_dir = db_dir / safe_repo_dir(org_repo)
    sarif_file = results_dir / f"{safe_repo_dir(org_repo)}.sarif"

    try:
        # Clone
        if not repo_dir.exists():
            run([
                "git", "clone",
                f"{GITHUB_BASE}/{org_repo}.git",
                str(repo_dir)
            ])

        # Create database
        if not database_dir.exists():
            run([
                "codeql", "database", "create",
                str(database_dir),
                f"--language={language}",
                f"--source-root={repo_dir}"
            ])

        # Analyze
        run([
            "codeql", "database", "analyze",
            str(database_dir),
            query,
            "--format", sarif_format,
            "--output", str(sarif_file),
            "--threads", "2"
        ])

        return (org_repo, "OK", None)

    except subprocess.CalledProcessError as e:
        return (org_repo, "FAIL", e.stderr.decode(errors="ignore"))

def main():
    parser = argparse.ArgumentParser(
        description="Parallel local CodeQL variant analysis (SARIF output)"
    )
    parser.add_argument("repo_file", help="File containing org/repo list")
    parser.add_argument("language", help="CodeQL language (e.g. cpp, java, go, javascript)")
    parser.add_argument("query", help="Path to CodeQL query or query pack")
    parser.add_argument("--root", default="VariantAnalysisRoot")
    parser.add_argument("--sarif-format", default="sarifv2.1.0")
    parser.add_argument(
        "--workers",
        type=int,
        default=max(1, os.cpu_count() // 2),
        help="Number of parallel workers (default: cpu_count / 2)"
    )

    args = parser.parse_args()

    root = Path(args.root).resolve()
    (root / "repos").mkdir(parents=True, exist_ok=True)
    (root / "databases").mkdir(parents=True, exist_ok=True)
    (root / "results").mkdir(parents=True, exist_ok=True)

    query_path = Path(args.query).resolve()
    if not query_path.exists():
        print(f"[!] Query or pack not found: {query_path}")
        sys.exit(1)

    with open(args.repo_file) as f:
        repos = [
            line.strip()
            for line in f
            if line.strip() and not line.startswith("#")
        ]

    print(f"[+] Starting analysis with {args.workers} workers")

    failures = []

    with ProcessPoolExecutor(max_workers=args.workers) as executor:
        futures = {
            executor.submit(
                process_repo,
                repo,
                args.language,
                str(query_path),
                str(root),
                args.sarif_format
            ): repo
            for repo in repos
        }

        for future in as_completed(futures):
            repo = futures[future]
            org_repo, status, error = future.result()

            if status == "OK":
                print(f"[✓] {org_repo}")
            else:
                print(f"[✗] {org_repo}")
                failures.append((org_repo, error))

    if failures:
        print("\n=== Failures ===")
        for repo, err in failures:
            print(f"\n[{repo}]\n{err}")

if __name__ == "__main__":
    main()
