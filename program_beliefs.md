# autoresearch — Arm 3: Structured Beliefs

This is an experiment to have the LLM do its own research, maintaining a structured set of beliefs about what works.

## Setup

1. **Agree on a run tag**: propose a tag based on today's date (e.g. `mar5`). The branch `autoresearch/<tag>` must not already exist.
2. **Create the branch**: `git checkout -b autoresearch/<tag>` from current master.
3. **Read the in-scope files**:
   - `README.md` — repository context.
   - `prepare.py` — fixed. Do not modify.
   - `train.py` — the file you modify.
4. **Verify data exists**: Check that `~/.cache/autoresearch/` contains data shards and a tokenizer. If not, tell the human to run `uv run prepare.py`.
5. **Initialize results_arm3.tsv**: Create with header row only.
6. **Initialize beliefs.md**: Copy the contents of `beliefs_seed.md` into a new file `beliefs.md`.
7. **Confirm and go**.

## Experimentation

Each experiment runs on a single GPU. Training runs for a **fixed 5 minutes** wall clock. Launch: `uv run train.py`.

**What you CAN do:** Modify `train.py` — architecture, optimizer, hyperparameters, training loop, batch size, model size.

**What you CANNOT do:** Modify `prepare.py`. Install new packages. Modify evaluation.

**Goal: get the lowest val_bpb.**

**VRAM**: soft constraint. Some increase acceptable for meaningful gains.

**Simplicity criterion**: All else being equal, simpler is better.

**First run**: Establish the baseline by running train.py as-is.

## Beliefs maintenance

You maintain `beliefs.md` — a numbered list of beliefs about what works and doesn't work for this training setup.

### Format

Each belief follows this format:
```
N. [confidence: high/med/low] <belief statement> — <supporting evidence from experiments>
```

### Rules

- **Max 20 beliefs.** When full, a new belief must replace the weakest/least-supported existing one.
- **Rewrite, don't append.** After each experiment, rewrite `beliefs.md` with updated beliefs. This is not an append log — it's a living document.
- **Update confidence** based on experimental evidence. Strengthen beliefs confirmed by results, weaken beliefs contradicted by results.

### Before each experiment

1. Read `beliefs.md`.
2. Explicitly state which belief(s) motivate your current hypothesis.
3. Explain why this experiment tests or builds on those beliefs.

### After each experiment

1. Update `beliefs.md`: adjust confidence levels, add new beliefs, replace weak ones.
2. Note which beliefs were confirmed or contradicted by this experiment's results.

## Logging results

Log to `results_arm3.tsv` (tab-separated). Header:

```
experiment_number	hypothesis_summary	motivating_beliefs	actual_val_bpb	best_val_bpb_so_far	kept_or_reverted	beliefs_updated
```

- `motivating_beliefs`: comma-separated belief numbers (e.g. "1,3")
- `beliefs_updated`: comma-separated belief numbers that changed (e.g. "2,5") or "none"

Do not commit the TSV.

## The experiment loop

LOOP FOREVER:

1. **Read beliefs.md**. State which beliefs motivate your next experiment.
2. Modify `train.py`.
3. `git commit`
4. `uv run train.py > run.log 2>&1`
5. `grep "^val_bpb:\|^peak_vram_mb:" run.log`
6. If grep is empty → crash. `tail -n 50 run.log` for stack trace.
7. Record results in TSV.
8. **Rewrite beliefs.md** with any updates from this experiment.
9. If val_bpb improved → keep the commit.
10. If val_bpb equal or worse → `git reset` back.

**Timeout**: >10 minutes → kill, treat as failure.

**Crashes**: Fix trivial bugs and re-run. Skip fundamentally broken ideas.

**NEVER STOP**: Do NOT pause to ask the human. You are autonomous. The loop runs until the human interrupts you.
