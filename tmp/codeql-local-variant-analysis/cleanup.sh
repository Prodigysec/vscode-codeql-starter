#!/bin/bash
#
# cleanup.sh - Clean up CodeQL analysis workspace before git operations
#
# Usage: ./cleanup.sh [root_directory]
#
# Removes cloned repositories and databases while preserving results.
# If no directory specified, cleans all VariantAnalysisRoot* directories.

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}[+] CodeQL Workspace Cleanup${NC}"
echo

# Function to clean a single root directory
clean_root() {
    local root_dir="$1"
    
    if [ ! -d "$root_dir" ]; then
        echo -e "${YELLOW}[!] Directory not found: $root_dir${NC}"
        return
    fi
    
    echo -e "${GREEN}[*] Cleaning: $root_dir${NC}"
    
    # Clean repos
    if [ -d "$root_dir/repos" ]; then
        echo "    - Removing repos/*"
        rm -rf "$root_dir/repos"/*
    fi
    
    # Clean databases
    if [ -d "$root_dir/databases" ]; then
        echo "    - Removing databases/*"
        rm -rf "$root_dir/databases"/*
    fi
    
    # Keep results directory
    if [ -d "$root_dir/results" ]; then
        result_count=$(find "$root_dir/results" -name "*.sarif" 2>/dev/null | wc -l)
        echo -e "    - Preserving results/ (${result_count} SARIF files)"
    fi
    
    echo
}

# Function to show space freed
show_space_freed() {
    df -h . | awk 'NR==2 {print "Available space: " $4}'
}

echo "Before cleanup:"
show_space_freed
echo

# If specific directory provided, clean only that
if [ $# -eq 1 ]; then
    clean_root "$1"
else
    # Clean all VariantAnalysisRoot* directories
    found=0
    for dir in VariantAnalysisRoot*/; do
        if [ -d "$dir" ]; then
            clean_root "$dir"
            found=1
        fi
    done
    
    # Also check for VariantAnalysisRoot without suffix
    if [ -d "VariantAnalysisRoot" ]; then
        clean_root "VariantAnalysisRoot"
        found=1
    fi
    
    if [ $found -eq 0 ]; then
        echo -e "${YELLOW}[!] No VariantAnalysisRoot directories found${NC}"
        exit 0
    fi
fi

echo "After cleanup:"
show_space_freed
echo
echo -e "${GREEN}[✓] Cleanup complete${NC}"
echo -e "${YELLOW}[i] Results preserved in */results/ directories${NC}"