# autoresearch — Arm 2: Naive Summary

This is an experiment to have the LLM do its own research, with a running summary of past experiments.

## Setup

1. **Agree on a run tag**: propose a tag based on today's date (e.g. `mar5`). The branch `autoresearch/<tag>` must not already exist.
2. **Create the branch**: `git checkout -b autoresearch/<tag>` from current master.
3. **Read the in-scope files**:
   - `README.md` — repository context.
   - `prepare.py` — fixed. Do not modify.
   - `train.py` — the file you modify.
4. **Verify data exists**: Check that `~/.cache/autoresearch/` contains data shards and a tokenizer. If not, tell the human to run `uv run prepare.py`.
5. **Initialize results_arm2.tsv**: Create with header row only.
6. **Create summary.md**: Create an empty `summary.md` file.
7. **Confirm and go**.

## Experimentation

Each experiment runs on a single GPU. Training runs for a **fixed 5 minutes** wall clock. Launch: `uv run train.py`.

**What you CAN do:** Modify `train.py` — architecture, optimizer, hyperparameters, training loop, batch size, model size.

**What you CANNOT do:** Modify `prepare.py`. Install new packages. Modify evaluation.

**Goal: get the lowest val_bpb.**

**VRAM**: soft constraint. Some increase acceptable for meaningful gains.

**Simplicity criterion**: All else being equal, simpler is better.

**First run**: Establish the baseline by running train.py as-is.

## Summary maintenance

You maintain `summary.md`. This is your memory across experiments.

**After every experiment:**
- Append 2-3 sentences: what you changed, the val_bpb result, kept or reverted.

**Before every experiment:**
- Read `summary.md` in full before deciding what to try next.
- Use it to avoid repeating failed approaches and build on what worked.

No size cap — let it grow naturally.

## Logging results

Log to `results_arm2.tsv` (tab-separated). Header:

```
experiment_number	hypothesis_summary	actual_val_bpb	best_val_bpb_so_far	kept_or_reverted
```

Do not commit the TSV.

## The experiment loop

LOOP FOREVER:

1. **Read summary.md** for context on past experiments.
2. Decide what to try next, informed by the summary.
3. Modify `train.py`.
4. `git commit`
5. `uv run train.py > run.log 2>&1`
6. `grep "^val_bpb:\|^peak_vram_mb:" run.log`
7. If grep is empty → crash. `tail -n 50 run.log` for stack trace.
8. Record results in TSV.
9. **Append to summary.md**: 2-3 sentences about this experiment.
10. If val_bpb improved → keep the commit.
11. If val_bpb equal or worse → `git reset` back.

**Timeout**: >10 minutes → kill, treat as failure.

**Crashes**: Fix trivial bugs and re-run. Skip fundamentally broken ideas.

**NEVER STOP**: Do NOT pause to ask the human. You are autonomous. The loop runs until the human interrupts you.
