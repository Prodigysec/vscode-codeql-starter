#!/usr/bin/env python3
import argparse
import requests
import sys
from pathlib import Path
from typing import Set


SOURCEGRAPH_API = "https://sourcegraph.com/.api/graphql"


GRAPHQL_QUERY = """
query SearchRepos($query: String!, $patternType: SearchPatternType!) {
  search(query: $query, patternType: $patternType) {
    results {
      resultCount
      results {
        __typename
        ... on FileMatch {
          repository {
            name
          }
        }
      }
    }
  }
}
"""


def run_search(search_query: str, limit: int) -> Set[str]:
    """
    Run a Sourcegraph GraphQL search and return a set of repo names (org/repo)
    """
    # Extract patternType from query string and remove it
    clean_query = search_query.replace("patternType:regexp", "").replace("patternType:literal", "").replace("patternType:structural", "").strip()
    
    # Extract patternType from the original query, default to literal
    if "patternType:regexp" in search_query:
        pattern_type = "regexp"
    elif "patternType:structural" in search_query:
        pattern_type = "structural"
    else:
        pattern_type = "literal"
    
    # Add count:all or count:N to the query
    if "count:" not in clean_query:
        clean_query = f"{clean_query} count:{limit}"
    
    print(f"[DEBUG] Pattern type: {pattern_type}")
    print(f"[DEBUG] Clean query: {clean_query}")
    
    payload = {
        "query": GRAPHQL_QUERY,
        "variables": {
            "query": clean_query,
            "patternType": pattern_type
        }
    }

    r = requests.post(SOURCEGRAPH_API, json=payload)
    if r.status_code != 200:
        print(f"[!] Sourcegraph API error: {r.status_code}")
        print(r.text)
        sys.exit(1)

    data = r.json()
    
    # Check for GraphQL errors
    if "errors" in data:
        print("[!] GraphQL API error:")
        for error in data["errors"]:
            print(f"  - {error.get('message', 'Unknown error')}")
        sys.exit(1)

    repos = set()

    try:
        search_results = data["data"]["search"]["results"]
        result_count = search_results.get("resultCount", 0)
        
        print(f"[*] API returned {result_count} total matching results")
        
        results = search_results["results"]
        print(f"[*] Processing {len(results)} results")
        
        for item in results:
            if item.get("__typename") == "FileMatch":
                repo_name = item.get("repository", {}).get("name")
                if repo_name:
                    # ✅ Strip github.com/ prefix and other host prefixes
                    if repo_name.startswith("github.com/"):
                        repo_name = repo_name.replace("github.com/", "")
                    elif repo_name.startswith("gitlab.com/"):
                        repo_name = repo_name.replace("gitlab.com/", "")
                    # Add other hosts as needed
                    
                    repos.add(repo_name)
                    
    except (KeyError, TypeError) as e:
        print(f"[!] Unexpected API response format: {e}")
        print(data)
        sys.exit(1)

    return repos

def main():
    parser = argparse.ArgumentParser(
        description="Discover repositories using Sourcegraph GraphQL search"
    )
    parser.add_argument(
        "--query",
        required=True,
        help="Sourcegraph search query (see https://sourcegraph.com/docs/code-search/queries)"
    )
    parser.add_argument(
        "--count",
        type=int,
        default=500,
        help="Max number of repos to retrieve (default: 500)"
    )
    parser.add_argument(
        "--output",
        default="repos.txt",
        help="Output file for discovered repos"
    )

    args = parser.parse_args()

    print("[+] Running Sourcegraph discovery")
    print(f"[+] Query: {args.query}")

    repos = run_search(args.query, args.count)

    if not repos:
        print("[!] No repositories found")
        sys.exit(0)

    output_path = Path(args.output)
    with output_path.open("w") as f:
        for repo in sorted(repos):
            f.write(f"{repo}\n")

    print(f"[✓] Discovered {len(repos)} repositories")
    print(f"[✓] Written to {output_path}")


if __name__ == "__main__":
    main()
