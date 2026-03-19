"""
Analyze results from all 4 arms of the reflective-autoresearch experiment.

Usage: python analyze.py

Reads results_arm{1,2,3,4}.tsv and outputs:
- PNG charts (val_bpb curves, prediction accuracy, diagnostics)
- Text summary of key metrics
"""

import os
import sys

import matplotlib
import matplotlib.pyplot as plt
import numpy as np

matplotlib.rcParams.update({"font.size": 11})

ARMS = {
    1: {"name": "Baseline", "file": "results_arm1.tsv", "color": "#888888"},
    2: {"name": "Summary", "file": "results_arm2.tsv", "color": "#4A90D9"},
    3: {"name": "Beliefs", "file": "results_arm3.tsv", "color": "#E8A838"},
    4: {"name": "Reflective", "file": "results_arm4.tsv", "color": "#D94A4A"},
}


def load_tsv(path):
    """Load a TSV file into a list of dicts."""
    if not os.path.exists(path):
        return None
    rows = []
    with open(path) as f:
        header = f.readline().strip().split("\t")
        for line in f:
            vals = line.strip().split("\t")
            if len(vals) != len(header):
                continue
            rows.append(dict(zip(header, vals)))
    return rows if rows else None


def parse_float(s, default=None):
    try:
        return float(s)
    except (ValueError, TypeError):
        return default


def compute_metrics(rows):
    """Compute per-arm metrics from result rows."""
    n = len(rows)
    val_bpbs = [parse_float(r["actual_val_bpb"]) for r in rows]
    best_so_far = [parse_float(r["best_val_bpb_so_far"]) for r in rows]
    reverts = sum(
        1 for r in rows
        if r["kept_or_reverted"].strip().lower() in ("reverted", "discard")
    )

    valid_best = [b for b in best_so_far if b is not None]
    final_best = min(valid_best) if valid_best else None
    revert_ratio = reverts / n if n > 0 else 0
    auc = np.trapz(valid_best, dx=1) / len(valid_best) if valid_best else None

    return {
        "n": n,
        "val_bpbs": val_bpbs,
        "best_so_far": best_so_far,
        "final_best": final_best,
        "revert_ratio": revert_ratio,
        "reverts": reverts,
        "auc": auc,
    }


def plot_val_bpb_curves(all_data, output_path="val_bpb_curves.png"):
    """Plot val_bpb over experiment number for all arms."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

    for arm_id, info in ARMS.items():
        if arm_id not in all_data:
            continue
        m = all_data[arm_id]
        xs = list(range(1, m["n"] + 1))
        ax1.plot(xs, m["val_bpbs"], marker=".", alpha=0.6,
                 color=info["color"], label=info["name"])
    ax1.set_xlabel("Experiment #")
    ax1.set_ylabel("val_bpb")
    ax1.set_title("val_bpb per Experiment")
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    for arm_id, info in ARMS.items():
        if arm_id not in all_data:
            continue
        m = all_data[arm_id]
        xs = list(range(1, m["n"] + 1))
        ax2.plot(xs, m["best_so_far"], linewidth=2,
                 color=info["color"], label=info["name"])
    ax2.set_xlabel("Experiment #")
    ax2.set_ylabel("Best val_bpb so far")
    ax2.set_title("Convergence (Best val_bpb Over Time)")
    ax2.legend()
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()
    print(f"Saved: {output_path}")


def plot_prediction_accuracy(rows, output_path="prediction_accuracy.png"):
    """Arm 4 only: predicted vs actual val_bpb, split first/last half."""
    predictions = []
    for r in rows:
        pred = parse_float(r.get("predicted_val_bpb"))
        actual = parse_float(r.get("actual_val_bpb"))
        if pred is not None and actual is not None:
            predictions.append((pred, actual))

    if not predictions:
        print("No prediction data for Arm 4 — skipping prediction accuracy plot.")
        return

    mid = len(predictions) // 2
    first_half = predictions[:mid]
    second_half = predictions[mid:]

    fig, ax = plt.subplots(figsize=(7, 7))

    if first_half:
        preds, actuals = zip(*first_half)
        ax.scatter(preds, actuals, color="#4A90D9", alpha=0.6,
                   label=f"First {mid} experiments", s=40)
    if second_half:
        preds, actuals = zip(*second_half)
        ax.scatter(preds, actuals, color="#D94A4A", alpha=0.6,
                   label=f"Last {len(second_half)} experiments", s=40)

    all_vals = [p[0] for p in predictions] + [p[1] for p in predictions]
    lo, hi = min(all_vals), max(all_vals)
    margin = (hi - lo) * 0.05
    ax.plot([lo - margin, hi + margin], [lo - margin, hi + margin],
            "k--", alpha=0.3, label="Perfect prediction")

    ax.set_xlabel("Predicted val_bpb")
    ax.set_ylabel("Actual val_bpb")
    ax.set_title("Arm 4: Prediction Calibration")
    ax.legend()
    ax.grid(True, alpha=0.3)
    ax.set_aspect("equal")

    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()
    print(f"Saved: {output_path}")


def plot_diagnostics(all_data, all_rows, output_path="diagnostics.png"):
    """Bar charts for revert ratio, progress AUC, wasted-step ratio."""
    present = [a for a in ARMS if a in all_data]
    names = [ARMS[a]["name"] for a in present]
    colors = [ARMS[a]["color"] for a in present]

    revert_ratios = [all_data[a]["revert_ratio"] for a in present]
    aucs = [all_data[a]["auc"] for a in present]

    # Wasted-step ratio (arms 3-4 only)
    wasted = {}
    for arm_id in [3, 4]:
        if arm_id not in all_rows:
            continue
        rows = all_rows[arm_id]
        wasted_count = 0
        total_reverts = 0
        for i, r in enumerate(rows):
            if r["kept_or_reverted"].strip().lower() in ("reverted", "discard"):
                total_reverts += 1
                if i + 1 < len(rows):
                    next_updated = rows[i + 1].get("beliefs_updated", "none").strip().lower()
                    if next_updated in ("none", "", "n/a"):
                        wasted_count += 1
                else:
                    wasted_count += 1
        wasted[arm_id] = wasted_count / total_reverts if total_reverts > 0 else 0

    fig, axes = plt.subplots(1, 3, figsize=(15, 5))

    axes[0].bar(names, revert_ratios, color=colors, alpha=0.8)
    axes[0].set_title("Revert Ratio")
    axes[0].set_ylabel("Fraction reverted")
    axes[0].set_ylim(0, 1)

    axes[1].bar(names, aucs, color=colors, alpha=0.8)
    axes[1].set_title("Progress AUC (lower = faster convergence)")
    axes[1].set_ylabel("AUC")

    w_names, w_vals, w_colors = [], [], []
    for arm_id in [3, 4]:
        if arm_id in wasted:
            w_names.append(ARMS[arm_id]["name"])
            w_vals.append(wasted[arm_id])
            w_colors.append(ARMS[arm_id]["color"])
    if w_vals:
        axes[2].bar(w_names, w_vals, color=w_colors, alpha=0.8)
    axes[2].set_title("Wasted-Step Ratio (Arms 3-4)")
    axes[2].set_ylabel("Fraction wasted")
    axes[2].set_ylim(0, 1)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()
    print(f"Saved: {output_path}")


def print_summary(all_data, all_rows):
    """Print text summary of key metrics."""
    print("\n" + "=" * 60)
    print("RESULTS SUMMARY")
    print("=" * 60)

    for arm_id in sorted(all_data.keys()):
        m = all_data[arm_id]
        info = ARMS[arm_id]
        print(f"\nArm {arm_id} ({info['name']}):")
        print(f"  Experiments:    {m['n']}")
        if m["final_best"]:
            print(f"  Final best:     {m['final_best']:.6f}")
        else:
            print(f"  Final best:     N/A")
        print(f"  Revert ratio:   {m['revert_ratio']:.1%} ({m['reverts']}/{m['n']})")
        if m["auc"]:
            print(f"  Progress AUC:   {m['auc']:.6f}")
        else:
            print(f"  Progress AUC:   N/A")

    if 4 in all_rows:
        rows = all_rows[4]
        reflections = sum(
            1 for r in rows
            if r.get("reflection_triggered", "").strip().lower() == "yes"
        )
        valid_preds = [
            (parse_float(r.get("predicted_val_bpb")), parse_float(r.get("actual_val_bpb")))
            for r in rows
        ]
        valid_preds = [(p, a) for p, a in valid_preds if p is not None and a is not None]
        if valid_preds:
            gaps = [abs(a - p) for p, a in valid_preds]
            mean_gap = np.mean(gaps)
            print(f"\nArm 4 Prediction Stats:")
            print(f"  Mean |prediction gap|: {mean_gap:.6f}")
            print(f"  Reflections triggered: {reflections}/{len(rows)}")

            mid = len(valid_preds) // 2
            if mid > 0:
                first_gap = np.mean([abs(a - p) for p, a in valid_preds[:mid]])
                second_gap = np.mean([abs(a - p) for p, a in valid_preds[mid:]])
                print(f"  First-half mean gap:   {first_gap:.6f}")
                print(f"  Second-half mean gap:  {second_gap:.6f}")
                if second_gap < first_gap:
                    print(f"  Calibration improved by {(1 - second_gap / first_gap):.1%}")
                else:
                    print(f"  Calibration did not improve")

    print("\n" + "=" * 60)


def main():
    all_data = {}
    all_rows = {}

    for arm_id, info in ARMS.items():
        rows = load_tsv(info["file"])
        if rows is None:
            print(f"Arm {arm_id} ({info['name']}): no data found ({info['file']})")
            continue
        all_rows[arm_id] = rows
        all_data[arm_id] = compute_metrics(rows)
        print(f"Arm {arm_id} ({info['name']}): loaded {len(rows)} experiments")

    if not all_data:
        print("No data found. Run experiments first.")
        sys.exit(1)

    plot_val_bpb_curves(all_data)

    if 4 in all_rows:
        plot_prediction_accuracy(all_rows[4])

    plot_diagnostics(all_data, all_rows)
    print_summary(all_data, all_rows)


if __name__ == "__main__":
    main()
