#!/usr/bin/env python3
import argparse
import subprocess
import sys
from pathlib import Path

GITHUB_BASE = "https://github.com"

def run(cmd, cwd=None):
    print(f"[+] {' '.join(cmd)}")
    subprocess.run(cmd, cwd=cwd, check=True)

def safe_repo_dir(org_repo: str) -> str:
    return org_repo.replace("/", "-")

def clone_repo(org_repo: str, repos_dir: Path):
    repo_dir = repos_dir / safe_repo_dir(org_repo)
    if repo_dir.exists():
        print(f"[!] Repo already exists, skipping clone: {org_repo}")
        return repo_dir

    run([
        "git", "clone",
        f"{GITHUB_BASE}/{org_repo}.git",
        str(repo_dir)
    ])
    return repo_dir

def create_database(org_repo: str, language: str, repo_dir: Path, db_root: Path):
    db_dir = db_root / safe_repo_dir(org_repo)
    if db_dir.exists():
        print(f"[!] Database already exists, skipping DB creation: {org_repo}")
        return db_dir

    run([
        "codeql", "database", "create",
        str(db_dir),
        f"--language={language}",
        f"--source-root={repo_dir}"
    ])
    return db_dir

def run_query(org_repo: str, db_dir: Path, query: Path, results_dir: Path):
    result_file = results_dir / f"{safe_repo_dir(org_repo)}.bqrs"
    run([
        "codeql", "query", "run",
        str(query),
        "--database", str(db_dir),
        "--output", str(result_file)
    ])
    return result_file

def main():
    parser = argparse.ArgumentParser(
        description="Local CodeQL variant analysis across multiple repositories"
    )
    parser.add_argument("repo_file", help="File containing org/repo list")
    parser.add_argument("language", help="CodeQL language (e.g. cpp, java, go, javascript)")
    parser.add_argument("query", help="Path to CodeQL query (e.g. UnsafeDeserialization.ql)")
    parser.add_argument(
        "--root",
        default="VariantAnalysisRoot",
        help="Root directory for analysis"
    )

    args = parser.parse_args()

    root = Path(args.root).resolve()
    repos_dir = root / "repos"
    db_dir = root / "databases"
    results_dir = root / "results"

    repos_dir.mkdir(parents=True, exist_ok=True)
    db_dir.mkdir(parents=True, exist_ok=True)
    results_dir.mkdir(parents=True, exist_ok=True)

    query_path = Path(args.query).resolve()
    if not query_path.exists():
        print(f"[!] Query not found: {query_path}")
        sys.exit(1)

    with open(args.repo_file) as f:
        repos = [line.strip() for line in f if line.strip() and not line.startswith("#")]

    for org_repo in repos:
        print(f"\n=== Processing {org_repo} ===")

        try:
            repo_path = clone_repo(org_repo, repos_dir)
            database_path = create_database(
                org_repo,
                args.language,
                repo_path,
                db_dir
            )
            run_query(org_repo, database_path, query_path, results_dir)

        except subprocess.CalledProcessError as e:
            print(f"[!] Failed processing {org_repo}: {e}")
            continue

if __name__ == "__main__":
    main()
