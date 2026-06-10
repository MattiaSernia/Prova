import os
import re
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick

# ── configurazione ────────────────────────────────────────────────────────────

BASE = os.path.dirname(os.path.abspath(__file__))

TOTAL_REQ = 23
TOTAL_CON = 19

# (label, lista di (chunk_dim, path_validation_file))
CONFIGS = [
    ("$C_{O}^{J}(M_1)$", [
        (0,   os.path.join(BASE, "C_{O}/JSON/kg_0/single_validation_kg.txt")),
        (10,  os.path.join(BASE, "C_{O}/JSON/kg_10/single_validation_kg.txt")),
        (30,  os.path.join(BASE, "C_{O}/JSON/kg_30/single_validation_kg.txt")),
        (50,  os.path.join(BASE, "C_{O}/JSON/kg_50/single_validation_kg.txt")),
        (100, os.path.join(BASE, "C_{O}/JSON/kg_100/single_validation_kg.txt")),
    ]),
    ("$C_{OA}^{J}(M_1)$", [
        (0,   os.path.join(BASE, "C_{OA}/JSON/kg_agents_0/single_validation_kgagents.txt")),
        (10,  os.path.join(BASE, "C_{OA}/JSON/kg_agents_10/single_validation_kgagents.txt")),
        (30,  os.path.join(BASE, "C_{OA}/JSON/kg_agents_30/single_validation_kgagents.txt")),
        (50,  os.path.join(BASE, "C_{OA}/JSON/kg_agents_50/single_validation_kgagents.txt")),
        (100, os.path.join(BASE, "C_{OA}/JSON/kg_agents_100/single_validation_kgagents.txt")),
    ]),
    ("$C_{OAP}^{J}(M_1)$", [
        (0,   os.path.join(BASE, "C_{OAP}/JSON/kg_triplet_0/single_validation_kgagents_tri.txt")),
        (10,  os.path.join(BASE, "C_{OAP}/JSON/kg_triplet_10/single_validation_kgagents_tri.txt")),
        (30,  os.path.join(BASE, "C_{OAP}/JSON/kg_triplet_30/single_validation_kgagents_tri.txt")),
        (50,  os.path.join(BASE, "C_{OAP}/JSON/kg_triplet_50/single_validation_kgagents_tri.txt")),
        (100, os.path.join(BASE, "C_{OAP}/JSON/kg_triplet_100/single_validation_kgagents_tri.txt")),
    ]),
    ("$C_{\\emptyset}$", [
        (0,   os.path.join(BASE, "C_null/C_null_0/single_validation_nokg.txt")),
        (10,  os.path.join(BASE, "C_null/C_null_10/single_validation_nokg.txt")),
        (30,  os.path.join(BASE, "C_null/C_null_30/single_validation_nokg.txt")),
        (50,  os.path.join(BASE, "C_null/C_null_50/single_validation_nokg.txt")),
        (100, os.path.join(BASE, "C_null/C_null_100/single_validation_nokg.txt")),
    ]),
]

# ── parsing ───────────────────────────────────────────────────────────────────

def parse_validation(path):
    """Restituisce (n_req, n_con) soddisfatti."""
    if not os.path.exists(path):
        return None, None
    with open(path, encoding="utf-8") as f:
        content = f.read()
    req = len(re.findall(r'^REQ-\d+', content, re.MULTILINE))
    con = len(re.findall(r'^CON-\d+', content, re.MULTILINE))
    return req, con

# ── raccolta dati ─────────────────────────────────────────────────────────────

data = {}
for label, entries in CONFIGS:
    xs, req_pcts, con_pcts = [], [], []
    for chunk_dim, path in entries:
        req, con = parse_validation(path)
        if req is None:
            continue
        xs.append(chunk_dim)
        req_pcts.append(req / TOTAL_REQ * 100)
        con_pcts.append(con / TOTAL_CON * 100)
    data[label] = (xs, req_pcts, con_pcts)

# ── grafico ───────────────────────────────────────────────────────────────────

MARKERS = ["o", "s", "^", "D", "v"]
COLORS  = ["#2196F3", "#4CAF50", "#FF5722", "#9C27B0", "#FF9800"]

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 10), sharey=False)

for i, (label, (xs, req_pcts, con_pcts)) in enumerate(data.items()):
    kw = dict(marker=MARKERS[i], color=COLORS[i], linewidth=2, markersize=7)
    ax1.plot(xs, req_pcts, label=label, **kw)
    ax2.plot(xs, con_pcts, label=label, **kw)

for ax, title, total in [
    (ax1, f"Satisfied Requirements (tot. {TOTAL_REQ})", TOTAL_REQ),
    (ax2, f"Satisfied Constraints (tot. {TOTAL_CON})", TOTAL_CON),
]:
    ax.set_title(title, fontsize=13)
    ax.set_xlabel("$\gamma$", fontsize=11)
    ax.set_ylabel("% satisfied", fontsize=11)
    ax.set_xticks([0, 10, 30, 50, 100])
    ax.yaxis.set_major_formatter(mtick.PercentFormatter())
    ax.set_ylim(0, 105)
    ax.grid(axis="y", linestyle="--", alpha=0.5)
    ax.legend(fontsize=9)

fig.suptitle("Impact of Chunk Dimension on Validation per Configuration", fontsize=14, y=1.02)
plt.tight_layout()

out = os.path.join(BASE, "chunk_dimension_comparison.png")
plt.savefig(out, dpi=150, bbox_inches="tight")
print(f"Plot saved to: {out}")
plt.show()
