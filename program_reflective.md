# autoresearch — Arm 4: Reflective (Predict-Attribute-Update)

This is an experiment to have the LLM do its own research, maintaining structured beliefs AND making explicit predictions that get checked against reality.

## Setup

1. **Agree on a run tag**: propose a tag based on today's date (e.g. `mar5`). The branch `autoresearch/<tag>` must not already exist.
2. **Create the branch**: `git checkout -b autoresearch/<tag>` from current master.
3. **Read the in-scope files**:
   - `README.md` — repository context.
   - `prepare.py` — fixed. Do not modify.
   - `train.py` — the file you modify.
4. **Verify data exists**: Check that `~/.cache/autoresearch/` contains data shards and a tokenizer. If not, tell the human to run `uv run prepare.py`.
5. **Initialize results_arm4.tsv**: Create with header row only.
6. **Initialize beliefs.md**: Copy the contents of `beliefs_seed.md` into a new file `beliefs.md`.
7. **Confirm and go**.

## Experimentation

Each experiment runs on a single GPU. Training runs for a **fixed 5 minutes** wall clock. Launch: `uv run train.py`.

**What you CAN do:** Modify `train.py` — architecture, optimizer, hyperparameters, training loop, batch size, model size.

**What you CANNOT do:** Modify `prepare.py`. Install new packages. Modify evaluation.

**Goal: get the lowest val_bpb.**

**VRAM**: soft constraint. Some increase acceptable for meaningful gains.

**Simplicity criterion**: All else being equal, simpler is better.

**First run**: Establish the baseline by running train.py as-is. Skip prediction/attribution for the baseline — just record the result.

## Beliefs maintenance

You maintain `beliefs.md` — a numbered list of beliefs about what works and doesn't work for this training setup. Same rules as Arm 3:

- Each belief: `N. [confidence: high/med/low] <belief statement> — <supporting evidence>`
- **Max 20 beliefs.** New belief must replace the weakest when full.
- **Rewrite after each experiment.** This is a living document, not an append log.

## Prediction (before each experiment)

Before every experiment (except the baseline), write a prediction block:

```
## Prediction for experiment N
- Hypothesis: <what I'm changing and why>
- Motivated by belief(s): <which beliefs from beliefs.md>
- Expected outcome: val_bpb will [increase/decrease] by approximately [X] to reach approximately [Y]
- Confidence: [high/med/low]
- Falsifier: if val_bpb instead [does Z], it would mean [which belief is wrong]
```

Write this prediction in your response before modifying train.py. Be specific — a vague prediction is useless.

## Attribution (after each experiment)

After every experiment (except the baseline), write an attribution block:

```
## Attribution for experiment N
- Predicted: [X], Actual: [Y], Gap: [Z]
- Prediction was: [accurate / partially wrong / completely wrong]
- If wrong: the assumption that failed was [specific belief], because [reasoning]
- Belief update: [which belief to strengthen/weaken/replace and why]
- If right: this confirms [specific belief], confidence [stays/increases]
```

Then update beliefs.md accordingly.

## Triggered deep reflection

Most experiments get just the lightweight prediction + attribution above. But trigger a **full reflection** when ANY of these conditions are met:

- 2+ consecutive reverts (repeated failure)
- Actual val_bpb is >10% worse than current best
- Confidence was "high" but prediction gap > 5%
- You proposed something very similar to a previously reverted experiment

When triggered, answer these additional questions:

1. What pattern of failures am I seeing?
2. Is there a category of changes I should stop trying?
3. What is my biggest uncertainty right now?
4. What is the cheapest experiment that would resolve that uncertainty?

Do NOT run deep reflection on every experiment. Only when triggered.

## Logging results

Log to `results_arm4.tsv` (tab-separated). Header:

```
experiment_number	hypothesis_summary	motivating_beliefs	predicted_val_bpb	actual_val_bpb	prediction_gap	best_val_bpb_so_far	kept_or_reverted	attribution_summary	beliefs_updated	reflection_triggered
```

- `motivating_beliefs`: comma-separated belief numbers (e.g. "1,3")
- `prediction_gap`: actual minus predicted (positive = worse than expected)
- `beliefs_updated`: comma-separated belief numbers that changed, or "none"
- `reflection_triggered`: "yes" or "no"
- For the baseline experiment: leave predicted_val_bpb, prediction_gap, attribution_summary, beliefs_updated, and reflection_triggered as "N/A"

Do not commit the TSV.

## The experiment loop

LOOP FOREVER:

1. **Read beliefs.md**. State which beliefs motivate your next experiment.
2. **Write prediction block** (see format above).
3. Modify `train.py`.
4. `git commit`
5. `uv run train.py > run.log 2>&1`
6. `grep "^val_bpb:\|^peak_vram_mb:" run.log`
7. If grep is empty → crash. `tail -n 50 run.log` for stack trace.
8. **Write attribution block** (see format above).
9. **Check deep reflection triggers.** If any condition is met, do the full reflection.
10. Record results in TSV.
11. **Rewrite beliefs.md** with any updates.
12. If val_bpb improved → keep the commit.
13. If val_bpb equal or worse → `git reset` back.

**Timeout**: >10 minutes → kill, treat as failure.

**Crashes**: Fix trivial bugs and re-run. Skip fundamentally broken ideas.

**NEVER STOP**: Do NOT pause to ask the human. You are autonomous. The loop runs until the human interrupts you.
