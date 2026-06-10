import os
import re
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import numpy as np

BASE      = os.path.join(os.path.dirname(os.path.abspath(__file__)), "C_{OAP}")
TOTAL_REQ = 23
TOTAL_CON = 19

CONFIGS = [
    ("$J/T/M_1$",    "JSON/TEXT/llama"),
    ("$J/T/M_2$",    "JSON/TEXT/phi4"),
    ("$J/NT/M_1$",   "JSON/NO_TEXT/llama"),
    ("$J/NT/M_2$",   "JSON/NO_TEXT/phi4"),
    ("$TL/T/M_1$",   "TURTLE/TEXT/llama"),
    ("$TL/T/M_2$",   "TURTLE/TEXT/phi4"),
    ("$TL/NT/M_1$",  "TURTLE/NO_TEXT/llama"),
    ("$TL/NT/M_2$",  "TURTLE/NO_TEXT/phi4"),
]

COLORS = [
    "#1565C0", "#42A5F5",
    "#0D47A1", "#90CAF9",
    "#2E7D32", "#66BB6A",
    "#1B5E20", "#A5D6A7",
]

# indici per ciascun gruppo
GROUPS = {
    "Format":     {"JSON": [0,1,2,3], "TL": [4,5,6,7]},
    "Extractor":  {"$M_1$": [0,2,4,6], "$M_2$": [1,3,5,7]},
    "Text":       {"TEXT": [0,1,4,5], "NO TEXT": [2,3,6,7]},
}

def parse_validation(path):
    if not os.path.exists(path):
        return None, None
    with open(path, encoding="utf-8") as f:
        content = f.read()
    req = len(re.findall(r'^REQ-\d+', content, re.MULTILINE))
    con = len(re.findall(r'^CON-\d+', content, re.MULTILINE))
    return req, con

labels, req_pcts, con_pcts = [], [], []
for label, rel_path in CONFIGS:
    path = os.path.join(BASE, rel_path, "C_{OAP}_0", "single_validation_kgagents_tri.txt")
    req, con = parse_validation(path)
    if req is None:
        req, con = 0, 0
    labels.append(label)
    req_pcts.append(req / TOTAL_REQ * 100)
    con_pcts.append(con / TOTAL_CON * 100)

# ── layout ────────────────────────────────────────────────────────────────────
fig = plt.figure(figsize=(12, 13))
gs  = fig.add_gridspec(3, 2, height_ratios=[1, 1, 0.8], hspace=0.45, wspace=0.3)

ax_req  = fig.add_subplot(gs[0, :])
ax_con  = fig.add_subplot(gs[1, :])
ax_avg_req = fig.add_subplot(gs[2, 0])
ax_avg_con = fig.add_subplot(gs[2, 1])

x = np.arange(len(labels))

# ── barre principali ──────────────────────────────────────────────────────────
for ax, pcts, title in [
    (ax_req, req_pcts, f"Satisfied Requirements (tot. {TOTAL_REQ})"),
    (ax_con, con_pcts, f"Satisfied Constraints (tot. {TOTAL_CON})"),
]:
    bars = ax.bar(x, pcts, color=COLORS, edgecolor="white", width=0.6)
    ax.set_title(title, fontsize=13)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=10)
    ax.set_ylabel("% satisfied", fontsize=11)
    ax.yaxis.set_major_formatter(mtick.PercentFormatter())
    ax.set_ylim(0, 112)
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    for bar, pct in zip(bars, pcts):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 1.5,
                f"{pct:.0f}%", ha="center", va="bottom", fontsize=8)

    # linee medie per formato (gruppi contigui)
    for idxs, color, label_str in [
        ([0,1,2,3], "#1565C0", "avg JSON"),
        ([4,5,6,7], "#2E7D32", "avg TL"),
    ]:
        avg = np.mean([pcts[i] for i in idxs])
        x_start = x[idxs[0]]  - 0.35
        x_end   = x[idxs[-1]] + 0.35
        ax.hlines(avg, x_start, x_end, colors=color, linestyles="dashed",
                  linewidth=1.8, label=f"{label_str}: {avg:.1f}%")
    ax.legend(fontsize=8, loc="upper right")

# ── medie per gruppo ──────────────────────────────────────────────────────────
group_colors = ["#5C6BC0", "#EF5350"]   # opzione A, opzione B

for ax, pcts, title in [
    (ax_avg_req, req_pcts, "Group Averages: Requirements"),
    (ax_avg_con, con_pcts, "Group Averages: Constraints"),
]:
    group_names, vals_a, vals_b, labels_a, labels_b = [], [], [], [], []

    for grp_name, options in GROUPS.items():
        keys = list(options.keys())
        group_names.append(grp_name)
        vals_a.append(np.mean([pcts[i] for i in options[keys[0]]]))
        vals_b.append(np.mean([pcts[i] for i in options[keys[1]]]))
        labels_a.append(keys[0])
        labels_b.append(keys[1])

    xg = np.arange(len(group_names))
    w  = 0.35
    ba = ax.bar(xg - w/2, vals_a, w, color=group_colors[0], label="option A")
    bb = ax.bar(xg + w/2, vals_b, w, color=group_colors[1], label="option B")

    for bar, val, lbl in list(zip(ba, vals_a, labels_a)) + list(zip(bb, vals_b, labels_b)):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
                f"{lbl}\n{val:.1f}%", ha="center", va="bottom", fontsize=7.5)

    ax.set_title(title, fontsize=11)
    ax.set_xticks(xg)
    ax.set_xticklabels(group_names, fontsize=10)
    ax.set_ylabel("% satisfied", fontsize=10)
    ax.yaxis.set_major_formatter(mtick.PercentFormatter())
    ax.set_ylim(0, 120)
    ax.grid(axis="y", linestyle="--", alpha=0.4)

fig.suptitle("$C_{OAP}$: Configuration Comparison ($\\gamma=0$)", fontsize=14)

out = os.path.join(os.path.dirname(BASE), "coap_comparison.png")
plt.savefig(out, dpi=150, bbox_inches="tight")
print(f"Plot saved to: {out}")
plt.show()
