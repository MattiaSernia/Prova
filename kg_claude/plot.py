import os
import re
import argparse
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import numpy as np

ROOT        = os.path.dirname(os.path.abspath(__file__))
EXPERIMENTS = os.path.join(ROOT, "experiments")

CFT_META = {
    "belval":  {"total_req": 23, "total_con": 19},
    "chrb":    {"total_req": 25, "total_con": 23},
    "cabinet": {"total_req": 27, "total_con": 26},
}

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
CFT_COLORS = ["#1565C0", "#E65100", "#2E7D32", "#9C27B0"]

parser = argparse.ArgumentParser()
parser.add_argument("--cft",       choices=list(CFT_META.keys()))
parser.add_argument("--extractor", choices=DIM_VALUES["extractor"])
parser.add_argument("--schema",    choices=DIM_VALUES["schema"])
parser.add_argument("--format",    choices=DIM_VALUES["format"])
parser.add_argument("--text",      choices=DIM_VALUES["text"])
args = parser.parse_args()

freeze = {d: getattr(args, d) for d in DIM_ORDER if getattr(args, d) is not None}
extractor_free = "extractor" not in freeze

active_cfts = [args.cft] if args.cft else list(CFT_META.keys())


def read_scores(rel_path, cft):
    path = os.path.join(EXPERIMENTS, cft, rel_path,
                        "C_{OAP}_0", "single_validation_kgagents_tri.txt")
    if not os.path.exists(path):
        return None, None
    with open(path, encoding="utf-8") as fh:
        content = fh.read()
    req = len(re.findall(r'^REQ-\d+', content, re.MULTILINE))
    con = len(re.findall(r'^CON-\d+', content, re.MULTILINE))
    return req, con


def read_null_scores(cft):
    path = os.path.join(EXPERIMENTS, cft, "C_null", "C_null_0",
                        "single_validation_nokg.txt")
    if not os.path.exists(path):
        return None, None
    with open(path, encoding="utf-8") as fh:
        content = fh.read()
    req = len(re.findall(r'^REQ-\d+', content, re.MULTILINE))
    con = len(re.findall(r'^CON-\d+', content, re.MULTILINE))
    return (req / CFT_META[cft]["total_req"] * 100,
            con / CFT_META[cft]["total_con"] * 100)


def cfg_val(cfg, dim):
    ext, sch, fmt, txt, _ = cfg
    return {"extractor": ext, "schema": sch, "format": fmt, "text": txt}[dim]


def matches_freeze(cfg, freeze):
    for d, v in freeze.items():
        val = cfg_val(cfg, d)
        if val is None:
            continue
        if val != v:
            return False
    return True


def apply_constraint(cfg):
    if extractor_free:
        ext, sch, _, _, _ = cfg
        if ext == "phi4" and sch == "NO_SCHEMA":
            return False
    return True


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

labels = []
for cfg in filtered:
    parts = [DIM_SHORT[d][cfg_val(cfg, d)] for d in free if cfg_val(cfg, d) is not None]
    labels.append("$" + "/".join(parts) + "$" if parts else cfg[-1])

per_cft_req = {cft: [] for cft in active_cfts}
per_cft_con = {cft: [] for cft in active_cfts}

for cfg in filtered:
    _, _, _, _, rel_path = cfg
    for cft in active_cfts:
        req, con = read_scores(rel_path, cft)
        per_cft_req[cft].append(req / CFT_META[cft]["total_req"] * 100 if req is not None else 0.0)
        per_cft_con[cft].append(con / CFT_META[cft]["total_con"] * 100 if con is not None else 0.0)


GROUPS = {}
for dim in free:
    opts = {}
    for val in DIM_VALUES[dim]:
        idxs = [i for i, cfg in enumerate(filtered) if cfg_val(cfg, dim) == val]
        if idxs:
            opts[val] = idxs
    if len(opts) >= 2:
        GROUPS[dim] = opts

n_groups   = len(GROUPS)
n_cfts     = len(active_cfts)
cft_label  = args.cft.upper() if args.cft else " + ".join(c.upper() for c in active_cfts)
freeze_str = ", ".join(f"{d}={v}" for d, v in freeze.items()) if freeze else "no freeze"
cft_tag    = f"_{args.cft}" if args.cft else ""
freeze_tag = "_".join(freeze.values()) if freeze else "all"

null_scores = {cft: read_null_scores(cft) for cft in active_cfts}

# --- Figure 1: per-config bar charts ---
fig1 = plt.figure(figsize=(max(8, len(filtered) * 1.5), 9))
gs1  = fig1.add_gridspec(2, 1, hspace=0.45)
ax_req = fig1.add_subplot(gs1[0])
ax_con = fig1.add_subplot(gs1[1])

x         = np.arange(len(labels))
bar_width = 0.6 / n_cfts

for ax, data_by_cft, title, null_idx in [
    (ax_req, per_cft_req, "Satisfied Requirements", 0),
    (ax_con, per_cft_con, "Satisfied Constraints",  1),
]:
    for ci, cft in enumerate(active_cfts):
        offset = (ci - (n_cfts - 1) / 2) * bar_width
        xpos   = x + offset
        bars   = ax.bar(xpos, data_by_cft[cft], width=bar_width * 0.9,
                        color=CFT_COLORS[ci % len(CFT_COLORS)], edgecolor="white",
                        label=cft.upper())
        for bar, pct in zip(bars, data_by_cft[cft]):
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 1.5,
                    f"{pct:.0f}%", ha="center", va="bottom", fontsize=7)
        nv = null_scores[cft][null_idx]
        if nv is not None:
            ax.axhline(nv, color=CFT_COLORS[ci % len(CFT_COLORS)], linestyle="--",
                       linewidth=1.8, alpha=0.85,
                       label=f"{cft.upper()} $C_{{null}}$")
    ax.set_title(title, fontsize=13)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=10)
    ax.set_ylabel("% satisfied", fontsize=11)
    ax.yaxis.set_major_formatter(mtick.PercentFormatter())
    ax.set_ylim(0, 112)
    ax.grid(axis="y", linestyle="--", alpha=0.4)

handles, labels_leg = ax_req.get_legend_handles_labels()
fig1.legend(handles, labels_leg, fontsize=9, ncol=len(handles),
            loc="lower center", bbox_to_anchor=(0.5, -0.04))

fig1.suptitle(f"{cft_label}: $C_{{OAP}}$, $\\gamma=0$ ({freeze_str})", fontsize=14)
out1 = os.path.join(ROOT, f"plot_{freeze_tag}{cft_tag}.png")
fig1.savefig(out1, dpi=150, bbox_inches="tight")
print(f"Plot saved to: {out1}")

# --- Figure 2: per-CFT group averages (2 subplots per CFT: req + con) ---
if n_groups > 0:
    group_colors = ["#5C6BC0", "#EF5350"]
    group_dims   = list(GROUPS.keys())
    xg = np.arange(len(group_dims))
    w  = 0.35

    fig2 = plt.figure(figsize=(max(8, len(group_dims) * 2 + 4), n_cfts * 4))
    gs2  = fig2.add_gridspec(n_cfts, 2, hspace=0.5, wspace=0.35)

    for ri, cft in enumerate(active_cfts):
        for ci, (per_cft_pcts, metric) in enumerate([
            (per_cft_req, "Requirements"),
            (per_cft_con, "Constraints"),
        ]):
            ax = fig2.add_subplot(gs2[ri, ci])
            for gi, dim in enumerate(group_dims):
                opts   = GROUPS[dim]
                keys   = list(opts.keys())
                vals_a = [per_cft_pcts[cft][i] for i in opts[keys[0]]]
                vals_b = [per_cft_pcts[cft][i] for i in opts[keys[1]]]
                mean_a, std_a = np.mean(vals_a), np.std(vals_a)
                mean_b, std_b = np.mean(vals_b), np.std(vals_b)
                ax.bar(xg[gi] - w/2, mean_a, w, color=group_colors[0], edgecolor="white")
                ax.bar(xg[gi] + w/2, mean_b, w, color=group_colors[1], edgecolor="white")
                ax.text(xg[gi] - w/2, mean_a + 1, f"{keys[0]}\n{mean_a:.1f}%\n±{std_a:.1f}%",
                        ha="center", va="bottom", fontsize=7.5)
                ax.text(xg[gi] + w/2, mean_b + 1, f"{keys[1]}\n{mean_b:.1f}%\n±{std_b:.1f}%",
                        ha="center", va="bottom", fontsize=7.5)
            nv = null_scores[cft][ci]
            if nv is not None:
                ax.axhline(nv, color=CFT_COLORS[ri % len(CFT_COLORS)],
                           linestyle="--", linewidth=1.8, alpha=0.85,
                           label=f"$C_{{null}}$")
            ax.set_title(f"{cft.upper()} {metric}", fontsize=11)
            ax.set_xticks(xg)
            ax.set_xticklabels(group_dims, fontsize=10)
            ax.set_ylabel("% satisfied", fontsize=10)
            ax.yaxis.set_major_formatter(mtick.PercentFormatter())
            ax.set_ylim(0, 125)
            ax.grid(axis="y", linestyle="--", alpha=0.4)
            ax.legend(fontsize=8, loc="upper left",
                      bbox_to_anchor=(1.01, 1.0), borderaxespad=0)

    fig2.suptitle(f"Group Averages $C_{{OAP}}$, $\\gamma=0$ ({freeze_str})", fontsize=13)
    out2 = os.path.join(ROOT, f"plot_avg_{freeze_tag}{cft_tag}.png")
    fig2.savefig(out2, dpi=150, bbox_inches="tight")
    print(f"Plot saved to: {out2}")

plt.show()
