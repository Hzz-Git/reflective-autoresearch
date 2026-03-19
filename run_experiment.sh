#!/bin/zsh
set -euo pipefail

# Usage: ./run_experiment.sh <arm:1-4> <num_experiments:default 50>
#
# Creates a git worktree so each arm runs in its own isolated directory.
# This allows multiple arms to run in parallel without conflicts.

ARM="${1:?Usage: ./run_experiment.sh <arm:1-4> [num_experiments]}"
NUM_EXPERIMENTS="${2:-50}"
DATE=$(date +%Y%m%d)
BRANCH="experiment/arm${ARM}-${DATE}"
REPO_ROOT="$(git rev-parse --show-toplevel)"
WORKTREE_DIR="${REPO_ROOT}/../arm${ARM}"

if [[ "$ARM" -lt 1 || "$ARM" -gt 4 ]]; then
    echo "Error: arm must be 1-4, got ${ARM}"
    exit 1
fi

# Map arm number to program file, results file, TSV header
case "$ARM" in
    1)
        PROGRAM="program_baseline.md"
        RESULTS="results_arm1.tsv"
        HEADER="experiment_number\thypothesis_summary\tactual_val_bpb\tbest_val_bpb_so_far\tkept_or_reverted"
        ;;
    2)
        PROGRAM="program_summary.md"
        RESULTS="results_arm2.tsv"
        HEADER="experiment_number\thypothesis_summary\tactual_val_bpb\tbest_val_bpb_so_far\tkept_or_reverted"
        ;;
    3)
        PROGRAM="program_beliefs.md"
        RESULTS="results_arm3.tsv"
        HEADER="experiment_number\thypothesis_summary\tmotivating_beliefs\tactual_val_bpb\tbest_val_bpb_so_far\tkept_or_reverted\tbeliefs_updated"
        ;;
    4)
        PROGRAM="program_reflective.md"
        RESULTS="results_arm4.tsv"
        HEADER="experiment_number\thypothesis_summary\tmotivating_beliefs\tpredicted_val_bpb\tactual_val_bpb\tprediction_gap\tbest_val_bpb_so_far\tkept_or_reverted\tattribution_summary\tbeliefs_updated\treflection_triggered"
        ;;
esac

echo "=== Reflective Autoresearch ==="
echo "Arm:              ${ARM} (${PROGRAM})"
echo "Experiments:      ${NUM_EXPERIMENTS}"
echo "Branch:           ${BRANCH}"
echo "Worktree:         ${WORKTREE_DIR}"
echo "Results file:     ${RESULTS}"
echo ""

# Clean up existing worktree/branch if present
if [[ -d "${WORKTREE_DIR}" ]]; then
    echo "Removing existing worktree at ${WORKTREE_DIR}..."
    git worktree remove "${WORKTREE_DIR}" --force 2>/dev/null || rm -rf "${WORKTREE_DIR}"
fi
if git rev-parse --verify "${BRANCH}" >/dev/null 2>&1; then
    echo "Removing existing branch ${BRANCH}..."
    git branch -D "${BRANCH}" 2>/dev/null || true
fi

# Create branch from master
MASTER_REF=$(git rev-parse master 2>/dev/null || git rev-parse main)
git branch "${BRANCH}" "${MASTER_REF}"

# Create worktree — a full isolated copy of the repo
git worktree add "${WORKTREE_DIR}" "${BRANCH}"

# Copy program files and support files into the worktree
for f in program_baseline.md program_summary.md program_beliefs.md program_reflective.md beliefs_seed.md analyze.py; do
    [[ -f "${REPO_ROOT}/${f}" ]] && cp "${REPO_ROOT}/${f}" "${WORKTREE_DIR}/${f}"
done

# Initialize results TSV
echo -e "${HEADER}" > "${WORKTREE_DIR}/${RESULTS}"
echo "Created ${RESULTS} with header."

# For arms 3 and 4, initialize beliefs.md from seed
if [[ "$ARM" -eq 3 || "$ARM" -eq 4 ]]; then
    cp "${WORKTREE_DIR}/beliefs_seed.md" "${WORKTREE_DIR}/beliefs.md"
    echo "Initialized beliefs.md from beliefs_seed.md."
fi

# For arm 2, create empty summary.md
if [[ "$ARM" -eq 2 ]]; then
    touch "${WORKTREE_DIR}/summary.md"
    echo "Created empty summary.md."
fi

# Sync uv environment in worktree
echo "Syncing dependencies in worktree..."
(cd "${WORKTREE_DIR}" && ~/.local/bin/uv sync 2>&1 | tail -1)

echo ""
echo "========================================"
echo "Setup complete!"
echo "========================================"
echo ""
echo "1. cd ${WORKTREE_DIR}"
echo "2. Open Claude Code:  claude --dangerously-skip-permissions"
echo "3. Prompt:  Read ${PROGRAM} and follow it. Let's kick off a new experiment — do the setup first."
echo ""
echo "The agent should run ${NUM_EXPERIMENTS} experiments."
echo "Results will be logged to ${RESULTS}."
