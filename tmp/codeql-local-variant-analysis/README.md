# CodeQL Variant Analysis Workflow

A two-phase security analysis workflow that discovers vulnerable repositories using Sourcegraph and analyzes them with CodeQL.

## Overview
```
[Phase 1: Discovery]  →  [Phase 2: Analysis]
    Sourcegraph              CodeQL
```

This workflow enables large-scale security research by:
1. **Discovery**: Finding repositories matching specific vulnerability patterns using Sourcegraph
2. **Analysis**: Running CodeQL queries against discovered repositories to identify security issues

## Why This Tool Exists

When running GitHub's CodeQL variant analysis, you may encounter:

⚠️ **"No CodeQL database available for the selected language"**

This happens because:
- The repository has never run a CodeQL analysis workflow
- GitHub doesn't have a pre-built database stored
- You can't analyze repositories that haven't opted into code scanning

**codeql-local-variant-analysis** solves this by:
1. 🔍 Discovering target repositories via Sourcegraph
2. 📦 Cloning repositories locally
3. 🏗️ Building CodeQL databases from source
4. 🔬 Running your security queries in parallel
5. 📊 Generating SARIF results


## Prerequisites

- Python 3.7+
- Git
- CodeQL CLI
- Required Python packages:
```bash
  pip install requests
```

## Project Structure
```
codeql-local-variant-analysis/
├── sourcegraph_discovery.py    # Phase 1: Repository discovery
├── variant_analysis.py          # Phase 2: CodeQL analysis
├── UnsafeDeserialization.ql     # Example CodeQL query
├── repos.txt                    # Discovered repositories list
├── codeql-pack.yml             # CodeQL pack configuration
└── VariantAnalysisRoot/        # Analysis workspace
    ├── repos/                   # Cloned repositories
    ├── databases/               # CodeQL databases
    └── results/                 # SARIF output files
```

## Phase 1: Discovery with Sourcegraph

### Script: `sourcegraph_discovery.py`

Searches Sourcegraph's public code index to find repositories matching specific patterns.

### Usage
```bash
python3 sourcegraph_discovery.py \
  --query 'SEARCH_QUERY' \
  --count MAX_RESULTS \
  --output OUTPUT_FILE
```

### Parameters

- `--query`: Sourcegraph search query (required)
- `--count`: Maximum number of repositories to retrieve (default: 500)
- `--output`: Output file for repository list (default: repos.txt)

### Query Syntax

The query supports Sourcegraph's search syntax with pattern types:

- **Pattern Types**:
  - `patternType:regexp` - Regular expression matching
  - `patternType:literal` - Exact string matching
  - `patternType:structural` - Structural code patterns

- **Filters**:
  - `lang:LANGUAGE` - Filter by programming language
  - `-file:PATTERN` - Exclude files matching pattern
  - `count:N` or `count:all` - Result limit

- **Boolean Operators**:
  - `AND` - Both conditions must match
  - `OR` - Either condition matches
  - Parentheses for grouping

### Example: Finding Unsafe Pickle Usage
```bash
python3 sourcegraph_discovery.py \
  --query 'lang:python import gradio (import pickle OR pickle.loads OR pickle.load) -file:test -file:docs patternType:regexp' \
  --count 1000 \
  --output repos.txt
```

This query finds Python repositories that:
- Import the `gradio` library
- Use pickle deserialization (`import pickle`, `pickle.loads`, or `pickle.load`)
- Exclude test and documentation files

### Output
```
AlibabaResearch/DAMO-ConvAI
Ascend/ModelZoo-PyTorch
CarperAI/cheese
Cinnamon/kotaemon
```

Format: One repository per line in `org/repo` format.

## Phase 2: Analysis with CodeQL

### Script: `variant_analysis.py`

Performs parallel CodeQL analysis on discovered repositories.

### Usage
```bash
python3 variant_analysis.py \
  REPO_FILE \
  LANGUAGE \
  QUERY \
  [OPTIONS]
```

### Parameters

- `REPO_FILE`: Path to file containing repository list (required)
- `LANGUAGE`: CodeQL language (cpp, java, python, javascript, go, etc.) (required)
- `QUERY`: Path to CodeQL query (.ql) or query pack (required)
- `--root`: Analysis workspace directory (default: VariantAnalysisRoot)
- `--sarif-format`: SARIF output format (default: sarifv2.1.0)
- `--workers`: Number of parallel workers (default: CPU count / 2)

### Example: Analyzing for Unsafe Deserialization
```bash
python3 variant_analysis.py \
  repos.txt \
  python \
  UnsafeDeserialization.ql \
  --workers 2
```

### Workflow Per Repository

For each repository, the script:

1. **Clone**: Downloads repository from GitHub
```
   repos/org-repo/
```

2. **Create Database**: Builds CodeQL database
```
   databases/org-repo/
```

3. **Analyze**: Runs query and generates SARIF output
```
   results/org-repo.sarif
```

### Output
```
[+] Starting analysis with 2 workers
[✓] AlibabaResearch/DAMO-ConvAI
[✓] Ascend/ModelZoo-PyTorch
[✗] BigComputer-Project/SWE-Arena

=== Failures ===
[BigComputer-Project/SWE-Arena]
Error: Database creation failed...
```

Results are saved as SARIF files in `VariantAnalysisRoot/results/`.

## Complete Workflow Example

### 1. Discover Vulnerable Repositories
```bash
# Find repositories using Gradio with pickle deserialization
python3 sourcegraph_discovery.py \
  --query 'lang:python import gradio (import pickle OR pickle.loads OR pickle.load) -file:test -file:docs patternType:regexp' \
  --count 1000 \
  --output gradio_pickle_repos.txt
```

**Output:**
```
[+] Running Sourcegraph discovery
[+] Query: lang:python import gradio (import pickle OR pickle.loads OR pickle.load) -file:test -file:docs patternType:regexp
[DEBUG] Pattern type: regexp
[DEBUG] Clean query: lang:python import gradio (import pickle OR pickle.loads OR pickle.load) -file:test -file:docs count:1000
[*] API returned 584 total matching results
[*] Processing 100 results
[✓] Discovered 87 repositories
[✓] Written to gradio_pickle_repos.txt
```

### 2. Analyze with CodeQL
```bash
# Run CodeQL analysis on discovered repositories
python3 variant_analysis.py \
  gradio_pickle_repos.txt \
  python \
  UnsafeDeserialization.ql \
  --workers 4 \
  --root GradioPickleAnalysis
```

**Output:**
```
[+] Starting analysis with 4 workers
[✓] AlibabaResearch/DAMO-ConvAI
[✓] CarperAI/cheese
[✓] ChenghaoMou/text-dedup
...
```

### 3. Review Results

SARIF files contain structured security findings:
```bash
ls GradioPickleAnalysis/results/
# AlibabaResearch-DAMO-ConvAI.sarif
# CarperAI-cheese.sarif
# ChenghaoMou-text-dedup.sarif
```

View in VS Code with CodeQL extension or parse programmatically.

## Common Search Patterns

### Finding SQL Injection Vulnerabilities
```bash
python3 sourcegraph_discovery.py \
  --query 'lang:javascript (SELECT|INSERT|UPDATE|DELETE) (req.query OR req.body) -file:test patternType:regexp' \
  --count 500 \
  --output sql_injection_repos.txt
```

### Finding Command Injection
```bash
python3 sourcegraph_discovery.py \
  --query 'lang:python (subprocess.call OR os.system OR exec) (request.args OR request.form) -file:test patternType:regexp' \
  --count 500 \
  --output command_injection_repos.txt
```

### Finding XSS Vulnerabilities
```bash
python3 sourcegraph_discovery.py \
  --query 'lang:javascript innerHTML dangerouslySetInnerHTML -file:test patternType:literal' \
  --count 500 \
  --output xss_repos.txt
```

## Performance Tuning

### Parallel Workers

Adjust `--workers` based on your system:
```bash
# Conservative (low memory usage)
--workers 2

# Balanced (recommended)
--workers $(( $(nproc) / 2 ))

# Aggressive (high memory usage)
--workers $(nproc)
```

### Memory Considerations

Each worker requires:
- ~500MB for repository clone
- ~1-2GB for database creation
- ~500MB for analysis

**Recommended**: 4GB RAM per worker

### Disk Space

Per repository:
- Clone: ~100-500MB
- Database: ~200MB-2GB
- Results: ~1-10MB

**Example**: 100 repositories ≈ 50-300GB

## Troubleshooting

### No Repositories Found
```
[!] No repositories found
```

**Solutions:**
- Verify query syntax in Sourcegraph web UI first
- Check if `count:` parameter is included
- Try broader search terms
- Remove `patternType:regexp` if not using regex

### Database Creation Failures
```
[✗] org/repo
Error: Could not determine primary language
```

**Solutions:**
- Verify repository contains code in specified language
- Check if repository requires authentication
- Ensure CodeQL supports the language version

### API Rate Limiting
```
[!] Sourcegraph API error: 429
```

**Solutions:**
- Reduce `--count` parameter
- Add delays between requests
- Use authenticated Sourcegraph API (requires token)

### Out of Disk Space
```
Error: No space left on device
```

**Solutions:**
- Clean up old analysis runs: `rm -rf VariantAnalysisRoot/repos/*`
- Use external storage for `--root`
- Reduce number of repositories analyzed

## Cleanup Before Git Operations

The analysis workspace can grow very large. Clean up before committing:
```bash
# Clean all workspace directories
./cleanup.sh
```

This removes:
- ✅ `repos/` - Cloned repositories
- ✅ `databases/` - CodeQL databases

This preserves:
- ✅ `results/` - SARIF output files

## Advanced Usage

### Custom CodeQL Queries

Create a `.ql` file with your query:
```ql
/**
 * @name Unsafe pickle deserialization
 * @description Detects pickle.loads() calls that may deserialize untrusted data
 * @kind problem
 * @id py/unsafe-deserialization
 */

import python

from Call call
where call.getFunc().(Attribute).getName() = "loads"
  and call.getFunc().(Attribute).getObject().toString() = "pickle"
select call, "Unsafe pickle deserialization"
```

### Query Packs

Use CodeQL query packs for comprehensive analysis:
```bash
python3 variant_analysis.py \
  repos.txt \
  python \
  codeql/python-queries:codeql-suites/python-security-and-quality.qls \
  --workers 4
```

### Filtering Repository List

Remove specific repositories:
```bash
# Remove archived or unmaintained repos
grep -v "archived-org" repos.txt > filtered_repos.txt

# Only analyze repos with recent commits
# (requires manual filtering or additional scripting)
```

## Security Considerations

- **Rate Limiting**: Respect Sourcegraph and GitHub rate limits
- **Authentication**: Some repositories may require GitHub authentication
- **Sensitive Data**: Cloned repositories may contain secrets or sensitive data
- **Resource Usage**: Monitor system resources during large-scale analysis
- **Results Handling**: SARIF files may contain sensitive code snippets

## References

- [Sourcegraph Search Syntax](https://sourcegraph.com/docs/code-search/queries)
- [CodeQL Documentation](https://codeql.github.com/docs/)
- [SARIF Format](https://sarifweb.azurewebsites.net/)
- [CodeQL Query Help](https://codeql.github.com/docs/writing-codeql-queries/)

## License

These scripts are provided as-is for security research and educational purposes.
