import os
import re
import argparse
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import numpy as np

BASE      = os.path.dirname(os.path.abspath(__file__))
TOTAL_REQ = 23
TOTAL_CON = 19

ALL_CONFIGS = [
    # (extractor, schema,      format,   text,      rel_path)
    ("phi4",  "SCHEMA",    "JSON",   "TEXT",    "phi4/SCHEMA/JSON/TEXT"),
    ("phi4",  "SCHEMA",    "JSON",   "NO_TEXT", "phi4/SCHEMA/JSON/NO_TEXT"),
    ("phi4",  "SCHEMA",    "TURTLE", "TEXT",    "phi4/SCHEMA/TURTLE/TEXT"),
    ("phi4",  "SCHEMA",    "TURTLE", "NO_TEXT", "phi4/SCHEMA/TURTLE/NO_TEXT"),
    ("phi4",  "NO_SCHEMA", "JSON",   "TEXT",    "phi4/NO_SCHEMA/JSON/TEXT"),
    ("phi4",  "NO_SCHEMA", "JSON",   "NO_TEXT", "phi4/NO_SCHEMA/JSON/NO_TEXT"),
    ("phi4",  "NO_SCHEMA", "TURTLE", "TEXT",    "phi4/NO_SCHEMA/TURTLE/TEXT"),
    ("phi4",  "NO_SCHEMA", "TURTLE", "NO_TEXT", "phi4/NO_SCHEMA/TURTLE/NO_TEXT"),
    ("llama", None,        "JSON",   "TEXT",    "llama/JSON/TEXT"),
    ("llama", None,        "JSON",   "NO_TEXT", "llama/JSON/NO_TEXT"),
    ("llama", None,        "TURTLE", "TEXT",    "llama/TURTLE/TEXT"),
    ("llama", None,        "TURTLE", "NO_TEXT", "llama/TURTLE/NO_TEXT"),
]

DIM_ORDER  = ["extractor", "schema", "format", "text"]
DIM_VALUES = {
    "extractor": ["phi4",   "llama"],
    "schema":    ["SCHEMA", "NO_SCHEMA"],
    "format":    ["JSON",   "TURTLE"],
    "text":      ["TEXT",   "NO_TEXT"],
}
DIM_SHORT = {
    "extractor": {"phi4": "M_2",  "llama": "M_1"},
    "schema":    {"SCHEMA": "S", "NO_SCHEMA": "NS"},
    "format":    {"JSON":   "J", "TURTLE":    "TL"},
    "text":      {"TEXT":   "T", "NO_TEXT":   "NT"},
}
PALETTE = ["#1565C0", "#42A5F5", "#0D47A1", "#90CAF9",
           "#2E7D32", "#66BB6A", "#1B5E20", "#A5D6A7",
           "#E65100", "#FF8F00", "#BF360C", "#FFCA28"]

parser = argparse.ArgumentParser()
parser.add_argument("--extractor", choices=DIM_VALUES["extractor"])
parser.add_argument("--schema",    choices=DIM_VALUES["schema"])
parser.add_argument("--format",    choices=DIM_VALUES["format"])
parser.add_argument("--text",      choices=DIM_VALUES["text"])
args = parser.parse_args()

freeze = {d: getattr(args, d) for d in DIM_ORDER if getattr(args, d) is not None}
extractor_free = "extractor" not in freeze


def cfg_val(cfg, dim):
    ext, sch, fmt, txt, _ = cfg
    return {"extractor": ext, "schema": sch, "format": fmt, "text": txt}[dim]


def matches_freeze(cfg, freeze):
    for d, v in freeze.items():
        val = cfg_val(cfg, d)
        # llama has no schema: skip schema filter for llama entries
        if val is None:
            continue
        if val != v:
            return False
    return True


def apply_constraint(cfg):
    # when extractor is free, phi4/NO_SCHEMA is excluded (schema must always be present)
    if extractor_free:
        ext, sch, _, _, _ = cfg
        if ext == "phi4" and sch == "NO_SCHEMA":
            return False
    return True


# when extractor is free, schema is not a free dim (fixed by constraint for phi4, N/A for llama)
free = [d for d in DIM_ORDER if d not in freeze]
if extractor_free and "schema" in free:
    free.remove("schema")


def sort_key(cfg):
    return tuple(
        DIM_VALUES[d].index(cfg_val(cfg, d)) if cfg_val(cfg, d) is not None else 999
        for d in free
    )


filtered = sorted(
    [c for c in ALL_CONFIGS if matches_freeze(c, freeze) and apply_constraint(c)],
    key=sort_key,
)

if not filtered:
    raise SystemExit("No configurations match the selected filters.")

labels, req_pcts, con_pcts = [], [], []
for cfg in filtered:
    _, _, _, _, rel_path = cfg
    path = os.path.join(BASE, rel_path, "C_{OAP}_0", "single_validation_kgagents_tri.txt")
    if os.path.exists(path):
        with open(path, encoding="utf-8") as fh:
            content = fh.read()
        req = len(re.findall(r'^REQ-\d+', content, re.MULTILINE))
        con = len(re.findall(r'^CON-\d+', content, re.MULTILINE))
    else:
        req, con = 0, 0
    parts = [DIM_SHORT[d][cfg_val(cfg, d)] for d in free if cfg_val(cfg, d) is not None]
    labels.append("$" + "/".join(parts) + "$" if parts else rel_path)
    req_pcts.append(req / TOTAL_REQ * 100)
    con_pcts.append(con / TOTAL_CON * 100)

# groups from free dimensions (only dims with ≥2 distinct values in filtered set)
GROUPS = {}
for dim in free:
    opts = {}
    for val in DIM_VALUES[dim]:
        idxs = [i for i, cfg in enumerate(filtered) if cfg_val(cfg, dim) == val]
        if idxs:
            opts[val] = idxs
    if len(opts) >= 2:
        GROUPS[dim] = opts

avg_line_dim    = free[0] if free else None
avg_line_groups = list(GROUPS[avg_line_dim].items()) if avg_line_dim and avg_line_dim in GROUPS else []
avg_line_colors = ["#1565C0", "#2E7D32"]

n_groups = len(GROUPS)
fig = plt.figure(figsize=(max(8, len(filtered) * 1.5), 13))
if n_groups > 0:
    gs = fig.add_gridspec(3, 2, height_ratios=[1, 1, 0.8], hspace=0.45, wspace=0.3)
    ax_req     = fig.add_subplot(gs[0, :])
    ax_con     = fig.add_subplot(gs[1, :])
    ax_avg_req = fig.add_subplot(gs[2, 0])
    ax_avg_con = fig.add_subplot(gs[2, 1])
else:
    gs = fig.add_gridspec(2, 1, hspace=0.45)
    ax_req = fig.add_subplot(gs[0])
    ax_con = fig.add_subplot(gs[1])

x      = np.arange(len(labels))
colors = PALETTE[:len(filtered)]

for ax, pcts, title in [
    (ax_req, req_pcts, f"Satisfied Requirements (tot. {TOTAL_REQ})"),
    (ax_con, con_pcts, f"Satisfied Constraints (tot. {TOTAL_CON})"),
]:
    bars = ax.bar(x, pcts, color=colors, edgecolor="white", width=0.6)
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
    for (val, idxs), color in zip(avg_line_groups, avg_line_colors):
        avg = np.mean([pcts[i] for i in idxs])
        ax.hlines(avg, x[idxs[0]] - 0.35, x[idxs[-1]] + 0.35,
                  colors=color, linestyles="dashed", linewidth=1.8,
                  label=f"avg {val}: {avg:.1f}%")
    if avg_line_groups:
        ax.legend(fontsize=8, loc="upper right")

if n_groups > 0:
    group_colors = ["#5C6BC0", "#EF5350"]
    for ax, pcts, title in [
        (ax_avg_req, req_pcts, "Group Averages: Requirements"),
        (ax_avg_con, con_pcts, "Group Averages: Constraints"),
    ]:
        group_names, vals_a, vals_b, labels_a, labels_b = [], [], [], [], []
        for dim, opts in GROUPS.items():
            keys = list(opts.keys())
            group_names.append(dim)
            vals_a.append(np.mean([pcts[i] for i in opts[keys[0]]]))
            vals_b.append(np.mean([pcts[i] for i in opts[keys[1]]]))
            labels_a.append(keys[0])
            labels_b.append(keys[1])
        xg = np.arange(len(group_names))
        w  = 0.35
        ba = ax.bar(xg - w/2, vals_a, w, color=group_colors[0])
        bb = ax.bar(xg + w/2, vals_b, w, color=group_colors[1])
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

freeze_str = ", ".join(f"{d}={v}" for d, v in freeze.items()) if freeze else "no freeze"
fig.suptitle(f"belval: $C_{{OAP}}$, $\\gamma=0$ ({freeze_str})", fontsize=14)

freeze_tag = "_".join(v for v in freeze.values()) if freeze else "all"
out = os.path.join(BASE, f"phi4_{freeze_tag}.png")
plt.savefig(out, dpi=150, bbox_inches="tight")
print(f"Plot saved to: {out}")
plt.show()
