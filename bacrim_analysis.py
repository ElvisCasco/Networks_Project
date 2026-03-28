"""
BACRIM 2020 Mexican Cartel Network Analysis
Standalone script extracted from BACRIM_Report.qmd
"""

import pandas as pd
import numpy as np
import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from collections import Counter
from itertools import combinations
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
import os
import gc
import warnings
warnings.filterwarnings('ignore')

os.makedirs("outputs", exist_ok=True)

# =============================================================================
# 1. Load data
# =============================================================================

nodes_df = pd.read_csv("BACRIM2020_Nodes.csv")
alliances_df = pd.read_csv("BACRIM2020_Alliances.csv")
rivals_df = pd.read_csv("BACRIM2020_Rivals.csv")
nodes_specialty_df = pd.read_csv("BACRIM2020_Nodes_With_Specialties.csv")
trends_df = pd.read_csv("Trends2012_2021.csv")

print(f"Nodes: {len(nodes_df)}, Alliance edges: {len(alliances_df)}, "
      f"Rivalry edges: {len(rivals_df)}")

# =============================================================================
# 2. Build graphs
# =============================================================================

node_labels = dict(zip(nodes_df["Node"], nodes_df["ShortName"]))
node_type = dict(zip(nodes_specialty_df["Node"], nodes_specialty_df["Type"]))
node_specialty = dict(zip(nodes_specialty_df["Node"],
                          nodes_specialty_df["Primary_Specialty"]))
node_state = dict(zip(nodes_specialty_df["Node"], nodes_specialty_df["State"]))
node_drugs = dict(zip(nodes_specialty_df["Node"],
                       nodes_specialty_df["Primary_Drugs"].fillna("")))

# Deduplicate edges (each appears twice in raw data)
def deduplicate_edges(df):
    edges, seen = [], set()
    for _, row in df.iterrows():
        key = (min(row["Node"], row["RNode"]), max(row["Node"], row["RNode"]))
        if key not in seen:
            seen.add(key)
            edges.append({"Node": row["Node"], "RNode": row["RNode"],
                          "weight": row["weight"]})
    return pd.DataFrame(edges)

alliances_dedup = deduplicate_edges(alliances_df)
rivals_dedup = deduplicate_edges(rivals_df)

# Signed master graph (alliances + rivalries)
G_signed = nx.Graph()
for _, row in nodes_specialty_df.iterrows():
    G_signed.add_node(row["Node"], label=row["ShortName"],
                      group=row["Group"], state=row["State"],
                      org_type=row.get("Type", "Unknown"),
                      specialty=row.get("Primary_Specialty", "Unknown"),
                      drugs=row.get("Primary_Drugs", ""))

for _, row in alliances_dedup.iterrows():
    G_signed.add_edge(row["Node"], row["RNode"],
                      weight=1, edge_type="alliance", strength=row["weight"])
for _, row in rivals_dedup.iterrows():
    G_signed.add_edge(row["Node"], row["RNode"],
                      weight=-1, edge_type="rivalry", strength=row["weight"])

# Alliance-only subgraph (remove isolates)
G_alliance = nx.Graph()
for _, row in nodes_specialty_df.iterrows():
    G_alliance.add_node(row["Node"], label=row["ShortName"],
                        group=row["Group"], state=row["State"],
                        org_type=row.get("Type", "Unknown"),
                        specialty=row.get("Primary_Specialty", "Unknown"),
                        drugs=row.get("Primary_Drugs", ""))
for _, row in alliances_dedup.iterrows():
    G_alliance.add_edge(row["Node"], row["RNode"], weight=row["weight"])

isolates_alliance = list(nx.isolates(G_alliance))
G_alliance_connected = G_alliance.copy()
G_alliance_connected.remove_nodes_from(isolates_alliance)

print(f"Signed graph: {G_signed.number_of_nodes()} nodes, "
      f"{G_signed.number_of_edges()} edges")
print(f"Alliance graph (non-isolates): {G_alliance_connected.number_of_nodes()} nodes, "
      f"{G_alliance_connected.number_of_edges()} edges")

# =============================================================================
# 3. Crime trends plot
# =============================================================================

fig, ax1 = plt.subplots(figsize=(10, 6))
ax1.plot(trends_df["YEAR"], trends_df["homicide"], "o-", color="crimson",
         linewidth=2, markersize=7, label="Homicides")
ax1.plot(trends_df["YEAR"], trends_df["missings"], "s-", color="darkorange",
         linewidth=2, markersize=7, label="Missing Persons")
ax1.set_xlabel("Year", fontsize=12)
ax1.set_ylabel("Count (Homicides / Missing)", fontsize=12, color="crimson")
ax1.tick_params(axis="y", labelcolor="crimson")

ax2 = ax1.twinx()
ax2.plot(trends_df["YEAR"], trends_df["arrests"], "^-", color="steelblue",
         linewidth=2, markersize=7, label="Arrests")
ax2.set_ylabel("Count (Arrests)", fontsize=12, color="steelblue")
ax2.tick_params(axis="y", labelcolor="steelblue")

ax1.axvline(x=2020, color="gray", linestyle="--", alpha=0.7, linewidth=1.5)
ax1.annotate("BACRIM 2020\nSnapshot",
             xy=(2020, trends_df[trends_df["YEAR"]==2020]["homicide"].values[0]),
             xytext=(2018, 38000), fontsize=9, fontweight="bold",
             arrowprops=dict(arrowstyle="->", color="gray"), color="gray")
lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper left", fontsize=10)
ax1.set_title("Mexican Crime Trends (2012–2021)", fontsize=14, fontweight="bold")
ax1.grid(True, alpha=0.3)
ax1.set_xticks(trends_df["YEAR"])
plt.tight_layout()
plt.savefig("outputs/crime_trends_2012_2021.png", dpi=200, bbox_inches="tight")
plt.close()

# =============================================================================
# 4. Organizational profiles
# =============================================================================

fig, axes = plt.subplots(1, 3, figsize=(18, 6))

type_counts = nodes_specialty_df["Type"].value_counts()
colors_type = ["#2c3e50", "#e74c3c", "#3498db", "#f39c12", "#2ecc71",
               "#9b59b6", "#1abc9c"]
ax1 = axes[0]
bars1 = ax1.barh(type_counts.index, type_counts.values,
                 color=colors_type[:len(type_counts)])
ax1.set_xlabel("Count", fontsize=11)
ax1.set_title("Organization Type", fontsize=13, fontweight="bold")
for bar, val in zip(bars1, type_counts.values):
    ax1.text(bar.get_width() + 0.5, bar.get_y() + bar.get_height()/2,
             str(val), va="center", fontsize=10, fontweight="bold")
ax1.invert_yaxis()

spec_counts = nodes_specialty_df["Primary_Specialty"].value_counts()
ax2 = axes[1]
bars2 = ax2.barh(spec_counts.index, spec_counts.values,
                 color=["#e74c3c", "#95a5a6", "#3498db", "#f39c12",
                        "#2ecc71", "#9b59b6"][:len(spec_counts)])
ax2.set_xlabel("Count", fontsize=11)
ax2.set_title("Primary Criminal Specialty", fontsize=13, fontweight="bold")
for bar, val in zip(bars2, spec_counts.values):
    ax2.text(bar.get_width() + 0.5, bar.get_y() + bar.get_height()/2,
             str(val), va="center", fontsize=10, fontweight="bold")
ax2.invert_yaxis()

has_drugs = nodes_specialty_df[nodes_specialty_df["Primary_Drugs"].notna() &
                                (nodes_specialty_df["Primary_Drugs"] != "")]
all_drugs = has_drugs["Primary_Drugs"].str.split(";").explode().str.strip()
drug_counts = all_drugs.value_counts()
ax3 = axes[2]
bars3 = ax3.barh(drug_counts.index, drug_counts.values,
                 color=["#e74c3c", "#3498db", "#f39c12", "#2ecc71",
                        "#9b59b6"][:len(drug_counts)])
ax3.set_xlabel("Number of Organizations", fontsize=11)
ax3.set_title("Drug Portfolio (organizations handling each)",
              fontsize=13, fontweight="bold")
for bar, val in zip(bars3, drug_counts.values):
    ax3.text(bar.get_width() + 0.5, bar.get_y() + bar.get_height()/2,
             str(val), va="center", fontsize=10, fontweight="bold")
ax3.invert_yaxis()

plt.suptitle("Organizational Composition of BACRIM 2020",
             fontsize=15, fontweight="bold", y=1.02)
plt.tight_layout()
plt.savefig("outputs/organizational_profiles.png", dpi=200, bbox_inches="tight")
plt.close()

# =============================================================================
# 5. Basic network statistics
# =============================================================================

N = G_alliance_connected.number_of_nodes()
E = G_alliance_connected.number_of_edges()
density = nx.density(G_alliance_connected)
components = list(nx.connected_components(G_alliance_connected))
largest_cc = max(components, key=len)
G_lcc = G_alliance_connected.subgraph(largest_cc).copy()
diameter = nx.diameter(G_lcc)
avg_path_length = nx.average_shortest_path_length(G_lcc)
clustering = nx.transitivity(G_alliance_connected)

stats_df = pd.DataFrame({
    "Metric": ["Nodes (N)", "Edges (E)", "Density",
               "Global Clustering Coefficient (C)",
               "Diameter (LCC)", "Avg Path Length (LCC)",
               "Connected Components", "Largest Component Size"],
    "Value": [N, E, round(density, 4), round(clustering, 4),
              diameter, round(avg_path_length, 4),
              len(components), len(largest_cc)]
})
stats_df.to_csv("outputs/basic_stats_alliance_network.csv", index=False)
print("\n=== Basic Statistics ===")
print(stats_df.to_string(index=False))

# =============================================================================
# 6. Centrality analysis
# =============================================================================

deg_cent = nx.degree_centrality(G_alliance_connected)
btw_cent = nx.betweenness_centrality(G_alliance_connected)

deg_df = pd.DataFrame([
    {"Node": n, "ShortName": node_labels.get(n, n),
     "Type": node_type.get(n, "Unknown"),
     "Specialty": node_specialty.get(n, "Unknown"),
     "Degree_Centrality": round(v, 4)}
    for n, v in deg_cent.items()
]).sort_values("Degree_Centrality", ascending=False)
deg_df.head(10).to_csv("outputs/top10_degree_centrality.csv", index=False)

btw_df = pd.DataFrame([
    {"Node": n, "ShortName": node_labels.get(n, n),
     "Type": node_type.get(n, "Unknown"),
     "Specialty": node_specialty.get(n, "Unknown"),
     "Betweenness_Centrality": round(v, 4)}
    for n, v in btw_cent.items()
]).sort_values("Betweenness_Centrality", ascending=False)
btw_df.head(10).to_csv("outputs/top10_betweenness_centrality.csv", index=False)

print("\n=== Top 5 Degree Centrality ===")
print(deg_df.head(5).to_string(index=False))
print("\n=== Top 5 Betweenness Centrality ===")
print(btw_df.head(5).to_string(index=False))

# =============================================================================
# 7. Centrality by organization type (boxplots)
# =============================================================================

centrality_df = pd.DataFrame({
    "Node": list(deg_cent.keys()),
    "Degree_Centrality": list(deg_cent.values()),
    "Betweenness_Centrality": [btw_cent[n] for n in deg_cent.keys()],
    "Type": [node_type.get(n, "Unknown") for n in deg_cent.keys()]
})
type_order = centrality_df.groupby("Type")["Degree_Centrality"].median()\
    .sort_values(ascending=False).index.tolist()

fig, axes = plt.subplots(1, 2, figsize=(16, 6))
colors_box = ["#e74c3c", "#3498db", "#2ecc71", "#f39c12", "#9b59b6",
              "#1abc9c", "#95a5a6"]

for ax, metric, title in [
    (axes[0], "Degree_Centrality", "Degree Centrality by Organization Type"),
    (axes[1], "Betweenness_Centrality", "Betweenness Centrality by Organization Type")
]:
    data = [centrality_df[centrality_df["Type"] == t][metric].values
            for t in type_order]
    bp = ax.boxplot(data, labels=type_order, patch_artist=True, vert=True)
    for patch, color in zip(bp["boxes"], colors_box[:len(bp["boxes"])]):
        patch.set_facecolor(color)
        patch.set_alpha(0.6)
    ax.set_ylabel(metric.replace("_", " "), fontsize=12)
    ax.set_title(title, fontsize=13, fontweight="bold")
    ax.tick_params(axis="x", rotation=30)
    ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig("outputs/centrality_by_type.png", dpi=200, bbox_inches="tight")
plt.close()

# =============================================================================
# 8. Geographic distribution
# =============================================================================

state_counts = nodes_specialty_df["State"].value_counts()
fig, axes = plt.subplots(1, 2, figsize=(16, 6))

top_states = state_counts.head(15)
axes[0].barh(top_states.index[::-1], top_states.values[::-1],
             color="steelblue", alpha=0.8)
axes[0].set_xlabel("Number of Organizations", fontsize=11)
axes[0].set_title("Organizations per State (Top 15)", fontsize=13, fontweight="bold")
axes[0].grid(True, alpha=0.3, axis="x")

# Same-state vs cross-state alliances
same_state = sum(1 for u, v in G_alliance_connected.edges()
                 if node_state.get(u, "") == node_state.get(v, ""))
cross_state = G_alliance_connected.number_of_edges() - same_state

bars = axes[1].bar(["Same State\nAlliances", "Cross-State\nAlliances"],
                   [same_state, cross_state], color=["#3498db", "#e74c3c"],
                   alpha=0.8, width=0.5)
total = same_state + cross_state
for bar, val in zip(bars, [same_state, cross_state]):
    axes[1].text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
                 f"{val} ({100*val/total:.1f}%)", ha="center", fontsize=11,
                 fontweight="bold")
axes[1].set_ylabel("Number of Alliance Edges", fontsize=11)
axes[1].set_title("Same-State vs Cross-State Alliances",
                  fontsize=13, fontweight="bold")
axes[1].grid(True, alpha=0.3, axis="y")

plt.tight_layout()
plt.savefig("outputs/geographic_distribution.png", dpi=200, bbox_inches="tight")
plt.close()

# =============================================================================
# 9. Signed network visualization
# =============================================================================

G_signed_viz = G_signed.copy()
G_signed_viz.remove_nodes_from(list(nx.isolates(G_signed_viz)))
pos = nx.spring_layout(G_signed_viz, k=0.5, iterations=80, seed=42)

alliance_edges = [(u, v) for u, v, d in G_signed_viz.edges(data=True)
                  if d.get("edge_type") == "alliance"]
rivalry_edges = [(u, v) for u, v, d in G_signed_viz.edges(data=True)
                 if d.get("edge_type") == "rivalry"]

degrees = dict(G_signed_viz.degree())
node_sizes = [max(degrees[n] * 40, 80) for n in G_signed_viz.nodes()]

type_color_map = {
    "National Cartel": "#e74c3c", "Regional Cartel": "#f39c12",
    "Local": "#3498db", "Cell": "#2ecc71",
    "Toll-Collector": "#9b59b6", "Undocumented": "#95a5a6",
}
node_colors = [type_color_map.get(node_type.get(n, "Undocumented"), "#95a5a6")
               for n in G_signed_viz.nodes()]

# Labels for top-degree nodes only
degree_threshold = sorted(degrees.values(), reverse=True)[min(15, len(degrees)-1)]
labels = {n: node_labels.get(n, n) for n in G_signed_viz.nodes()
          if degrees[n] >= degree_threshold}

fig, ax = plt.subplots(1, 1, figsize=(14, 10))
nx.draw_networkx_edges(G_signed_viz, pos, edgelist=alliance_edges,
                       edge_color="green", alpha=0.4, width=0.8, ax=ax)
nx.draw_networkx_edges(G_signed_viz, pos, edgelist=rivalry_edges,
                       edge_color="red", alpha=0.3, width=0.6,
                       style="dashed", ax=ax)
nx.draw_networkx_nodes(G_signed_viz, pos, node_size=node_sizes,
                       node_color=node_colors, alpha=0.7,
                       edgecolors="k", linewidths=0.5, ax=ax)
nx.draw_networkx_labels(G_signed_viz, pos, labels=labels,
                        font_size=7, font_weight="bold", ax=ax)

legend_patches = [mpatches.Patch(color=c, alpha=0.7, label=t)
                  for t, c in type_color_map.items()]
legend_patches.append(mpatches.Patch(color="green", alpha=0.5, label="Alliance Edge"))
legend_patches.append(mpatches.Patch(color="red", alpha=0.4, label="Rivalry Edge"))
ax.legend(handles=legend_patches, loc="upper left", fontsize=9, ncol=2)
ax.set_title("BACRIM 2020: Signed Cartel Network (colored by organization type)",
             fontsize=14, fontweight="bold")
ax.axis("off")
plt.tight_layout()
plt.savefig("outputs/signed_network_by_type.png", dpi=200, bbox_inches="tight")
plt.close()

# =============================================================================
# 10. Null models: ER and BA comparison
# =============================================================================

N_emp = G_alliance_connected.number_of_nodes()
E_emp = G_alliance_connected.number_of_edges()

p_er = (2 * E_emp) / (N_emp * (N_emp - 1))
G_er = nx.erdos_renyi_graph(N_emp, p_er, seed=42)

m_ba = max(1, round(E_emp / N_emp))
G_ba = nx.barabasi_albert_graph(N_emp, m_ba, seed=42)

def graph_metrics(G, name):
    C = nx.transitivity(G)
    comps = list(nx.connected_components(G))
    lcc = max(comps, key=len)
    G_lcc = G.subgraph(lcc).copy()
    L = nx.average_shortest_path_length(G_lcc)
    return {"Network": name, "Nodes": G.number_of_nodes(),
            "Edges": G.number_of_edges(), "Clustering_C": round(C, 4),
            "Avg_Path_Length_L": round(L, 4), "LCC_Size": len(lcc)}

comparison_df = pd.DataFrame([
    graph_metrics(G_alliance_connected, "Real (Alliance)"),
    graph_metrics(G_er, "Erdős–Rényi"),
    graph_metrics(G_ba, "Barabási–Albert"),
])
comparison_df.to_csv("outputs/random_graph_model_comparison.csv", index=False)
print("\n=== Null Model Comparison ===")
print(comparison_df.to_string(index=False))

# =============================================================================
# 11. Degree distribution (log-log)
# =============================================================================

def degree_distribution(G):
    degrees = [d for _, d in G.degree()]
    counts = Counter(degrees)
    total = sum(counts.values())
    ks = sorted(counts.keys())
    return ks, [counts[k] / total for k in ks]

fig, ax = plt.subplots(1, 1, figsize=(9, 6))
for G_plot, label, color, marker in [
    (G_alliance_connected, "Real (Alliance)", "steelblue", "o"),
    (G_er, "Erdős–Rényi", "orange", "s"),
    (G_ba, "Barabási–Albert", "green", "^"),
]:
    ks, probs = degree_distribution(G_plot)
    ax.scatter(ks, probs, label=label, color=color, marker=marker,
               s=50, alpha=0.7, edgecolors="k", linewidths=0.5)
ax.set_xscale("log"); ax.set_yscale("log")
ax.set_xlabel("Degree k", fontsize=12)
ax.set_ylabel("P(k)", fontsize=12)
ax.set_title("Degree Distribution (Log-Log)", fontsize=14, fontweight="bold")
ax.legend(fontsize=11)
ax.grid(True, alpha=0.3, which="both")
plt.tight_layout()
plt.savefig("outputs/degree_distribution_loglog.png", dpi=200, bbox_inches="tight")
plt.close()

# Small-world coefficient
C_real = nx.transitivity(G_alliance_connected)
C_er = nx.transitivity(G_er)
lcc_real = max(nx.connected_components(G_alliance_connected), key=len)
L_real = nx.average_shortest_path_length(
    G_alliance_connected.subgraph(lcc_real).copy())
lcc_er = max(nx.connected_components(G_er), key=len)
L_er = nx.average_shortest_path_length(G_er.subgraph(lcc_er).copy())

if C_er > 0 and L_er > 0:
    sigma = (C_real / C_er) / (L_real / L_er)
    print(f"\nSmall-world σ = {sigma:.2f}")
else:
    print("\nCannot compute σ (ER clustering is 0)")

# =============================================================================
# 12. Link prediction: Jaccard and Adamic-Adar
# =============================================================================

non_edges = list(nx.non_edges(G_alliance_connected))

jaccard_scores = {(u, v): s for u, v, s in
                  nx.jaccard_coefficient(G_alliance_connected, non_edges)}
adamic_scores = {(u, v): s for u, v, s in
                 nx.adamic_adar_index(G_alliance_connected, non_edges)}

pred_df = pd.DataFrame([{
    "Node_A": u, "Name_A": node_labels.get(u, u),
    "Type_A": node_type.get(u, "Unknown"),
    "Node_B": v, "Name_B": node_labels.get(v, v),
    "Type_B": node_type.get(v, "Unknown"),
    "Jaccard": round(jaccard_scores.get((u, v), 0), 4),
    "Adamic_Adar": round(adamic_scores.get((u, v), 0), 4),
} for u, v in non_edges])

pred_df = pred_df.sort_values(["Jaccard", "Adamic_Adar"],
                               ascending=[False, False])
top15 = pred_df.head(15).reset_index(drop=True)
top15.index += 1
top15.to_csv("outputs/top15_predicted_future_alliances.csv", index=True,
             index_label="Rank")

print("\n=== Top 10 Predicted Future Alliances ===")
print(top15.head(10)[["Name_A", "Type_A", "Name_B", "Type_B", "Jaccard"]]\
      .to_string(index=True))

# Link prediction score distributions
nonzero_jaccard = pred_df[pred_df["Jaccard"] > 0]["Jaccard"]
nonzero_adamic = pred_df[pred_df["Adamic_Adar"] > 0]["Adamic_Adar"]

fig, axes = plt.subplots(1, 2, figsize=(14, 5))
axes[0].hist(nonzero_jaccard, bins=30, color="steelblue", alpha=0.7,
             edgecolor="black")
axes[0].axvline(x=top15["Jaccard"].min(), color="red", linestyle="--",
                linewidth=2, label=f"Top-15 threshold: {top15['Jaccard'].min():.3f}")
axes[0].set_xlabel("Jaccard Coefficient"); axes[0].set_ylabel("Frequency")
axes[0].set_title("Jaccard Score Distribution (non-zero)", fontweight="bold")
axes[0].legend()
axes[0].grid(True, alpha=0.3)

axes[1].hist(nonzero_adamic, bins=30, color="darkorange", alpha=0.7,
             edgecolor="black")
axes[1].axvline(x=top15["Adamic_Adar"].min(), color="red", linestyle="--",
                linewidth=2,
                label=f"Top-15 threshold: {top15['Adamic_Adar'].min():.3f}")
axes[1].set_xlabel("Adamic-Adar Index"); axes[1].set_ylabel("Frequency")
axes[1].set_title("Adamic-Adar Score Distribution (non-zero)", fontweight="bold")
axes[1].legend()
axes[1].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig("outputs/link_prediction_distributions.png", dpi=200,
            bbox_inches="tight")
plt.close()

# =============================================================================
# 13. Dyadic logistic regression
# =============================================================================

# Rivalry subgraph (for SharedRivals feature)
G_rivalry = nx.Graph()
for u, v, d in G_signed.edges(data=True):
    if d.get("edge_type") == "rivalry":
        if u in G_alliance_connected and v in G_alliance_connected:
            G_rivalry.add_edge(u, v)

nodes_list = sorted(G_alliance_connected.nodes())
all_pairs = [(u, v) for i, u in enumerate(nodes_list) for v in nodes_list[i+1:]]


def compute_dyadic_features(u, v, G_all, G_riv, G_sign):
    """Compute 6 dyadic features for a node pair."""
    nu = set(G_all.neighbors(u)) if G_all.has_node(u) else set()
    nv = set(G_all.neighbors(v)) if G_all.has_node(v) else set()
    shared_allies = len(nu & nv)

    ru = set(G_riv.neighbors(u)) if G_riv.has_node(u) else set()
    rv = set(G_riv.neighbors(v)) if G_riv.has_node(v) else set()
    shared_rivals = len(ru & rv)

    su = node_specialty.get(u, "Undocumented")
    sv = node_specialty.get(v, "Undocumented")
    complementarity = int(su != sv and su != "Undocumented"
                          and sv != "Undocumented")

    same_state = int(node_state.get(u, "") == node_state.get(v, "")
                     and node_state.get(u, "") != "")

    balance = 0
    sn_u = set(G_sign.neighbors(u)) if G_sign.has_node(u) else set()
    sn_v = set(G_sign.neighbors(v)) if G_sign.has_node(v) else set()
    for w in sn_u & sn_v:
        wt_uw = G_sign[u][w].get("weight", 0)
        wt_vw = G_sign[v][w].get("weight", 0)
        balance += 1 if wt_uw * wt_vw > 0 else -1

    du = G_all.degree(u) if G_all.has_node(u) else 0
    dv = G_all.degree(v) if G_all.has_node(v) else 0
    deg_product = du * dv

    return [shared_allies, shared_rivals, complementarity,
            same_state, balance, deg_product]


feature_names = ["SharedAllies", "SharedRivals", "Complementarity",
                 "SameState", "BalanceScore", "DegreeProduct"]

X_rows = []
y_labels = []
for u, v in all_pairs:
    X_rows.append(compute_dyadic_features(u, v, G_alliance_connected,
                                           G_rivalry, G_signed))
    y_labels.append(1 if G_alliance_connected.has_edge(u, v) else 0)
X = np.array(X_rows)
y = np.array(y_labels)

print(f"\nDyads: {len(y):,}  |  Positive: {y.sum()} ({100*y.mean():.1f}%)")

# Fit full model for coefficient interpretation
lr_full = LogisticRegression(class_weight='balanced', max_iter=1000,
                              solver='lbfgs', random_state=42)
lr_full.fit(X, y)

coef_df = pd.DataFrame({
    "Feature": feature_names,
    "Coefficient": np.round(lr_full.coef_[0], 4),
    "Odds_Ratio": np.round(np.exp(lr_full.coef_[0]), 4)
}).sort_values("Coefficient", ascending=False)
coef_df.to_csv("outputs/logistic_coefficients.csv", index=False)
print("\n=== Logistic Coefficients ===")
print(coef_df.to_string(index=False))

# =============================================================================
# 14. Cross-validation: 4 models compared
# =============================================================================

edges_list = list(G_alliance_connected.edges())
non_edge_set = set(all_pairs) - set((min(u, v), max(u, v))
                                     for u, v in G_alliance_connected.edges())
non_edge_list = list(non_edge_set)

np.random.seed(42)
edge_indices = np.random.permutation(len(edges_list))
fold_size = len(edges_list) // 5

auc_results = {"Jaccard": [], "Adamic_Adar": [],
               "Logistic_Topo": [], "Logistic_Full": []}

for fold in range(5):
    test_idx = edge_indices[fold * fold_size : (fold + 1) * fold_size]
    train_idx = np.setdiff1d(edge_indices, test_idx)
    test_edges = [edges_list[i] for i in test_idx]

    G_train = G_alliance_connected.copy()
    G_train.remove_edges_from(test_edges)

    neg_sample_idx = np.random.choice(len(non_edge_list),
                                       size=len(test_edges), replace=False)
    neg_test_pairs = [non_edge_list[i] for i in neg_sample_idx]
    test_pairs = test_edges + neg_test_pairs
    test_y = np.array([1] * len(test_edges) + [0] * len(neg_test_pairs))

    # Jaccard / Adamic-Adar on training graph
    jacc_scores, aa_scores = [], []
    for u, v in test_pairs:
        if G_train.has_node(u) and G_train.has_node(v):
            cn = set(G_train.neighbors(u)) & set(G_train.neighbors(v))
            union = set(G_train.neighbors(u)) | set(G_train.neighbors(v))
            jacc_scores.append(len(cn) / len(union) if union else 0)
            aa_scores.append(sum(1 / np.log(G_train.degree(w))
                                 for w in cn if G_train.degree(w) > 1))
        else:
            jacc_scores.append(0)
            aa_scores.append(0)

    if len(set(test_y)) > 1:
        auc_results["Jaccard"].append(roc_auc_score(test_y, jacc_scores))
        auc_results["Adamic_Adar"].append(roc_auc_score(test_y, aa_scores))

    # Logistic models on training graph features
    X_train_fold, y_train_fold = [], []
    for u, v in all_pairs:
        X_train_fold.append(compute_dyadic_features(u, v, G_train,
                                                     G_rivalry, G_signed))
        y_train_fold.append(1 if G_train.has_edge(u, v) else 0)
    X_train_fold = np.array(X_train_fold)
    y_train_fold = np.array(y_train_fold)

    # Topology-only: SharedAllies + DegreeProduct
    lr_topo = LogisticRegression(class_weight='balanced', max_iter=1000,
                                  solver='lbfgs', random_state=42)
    lr_topo.fit(X_train_fold[:, [0, 5]], y_train_fold)

    lr_cv = LogisticRegression(class_weight='balanced', max_iter=1000,
                                solver='lbfgs', random_state=42)
    lr_cv.fit(X_train_fold, y_train_fold)

    X_test = np.array([compute_dyadic_features(u, v, G_train, G_rivalry, G_signed)
                       for u, v in test_pairs])

    if len(set(test_y)) > 1:
        auc_results["Logistic_Topo"].append(
            roc_auc_score(test_y, lr_topo.predict_proba(X_test[:, [0, 5]])[:, 1]))
        auc_results["Logistic_Full"].append(
            roc_auc_score(test_y, lr_cv.predict_proba(X_test)[:, 1]))

auc_df = pd.DataFrame({
    "Model": list(auc_results.keys()),
    "Mean_AUC": [round(np.mean(v), 4) for v in auc_results.values()],
    "Std_AUC": [round(np.std(v), 4) for v in auc_results.values()]
})
auc_df.to_csv("outputs/model_comparison_auc.csv", index=False)
print("\n=== 5-Fold CV AUC ===")
print(auc_df.to_string(index=False))

# =============================================================================
# 15. Network resilience: single CJNG removal
# =============================================================================

target_node = "N10025"  # CJNG

def comprehensive_metrics(G, name):
    n = G.number_of_nodes()
    e = G.number_of_edges()
    C = nx.transitivity(G)
    comps = list(nx.connected_components(G))
    lcc = max(comps, key=len)
    G_lcc = G.subgraph(lcc).copy()
    diam = nx.diameter(G_lcc) if len(lcc) > 1 else 0
    avg_pl = nx.average_shortest_path_length(G_lcc) if len(lcc) > 1 else 0
    return {"Network": name, "Nodes": n, "Edges": e,
            "Density": round(nx.density(G), 4),
            "Clustering_C": round(C, 4), "Components": len(comps),
            "LCC_Size": len(lcc), "Diameter_LCC": diam,
            "Avg_Path_Length_LCC": round(avg_pl, 4)}

pre_metrics = comprehensive_metrics(G_alliance_connected, "Before Removal")

G_post_removal = G_alliance_connected.copy()
G_post_removal.remove_node(target_node)
new_isolates = list(nx.isolates(G_post_removal))
G_post_removal.remove_nodes_from(new_isolates)

post_metrics = comprehensive_metrics(G_post_removal, "After Removal (CJNG)")

delta = {"Network": "Δ Change"}
for k in pre_metrics:
    if k != "Network":
        delta[k] = round(post_metrics[k] - pre_metrics[k], 4)

comparison = pd.DataFrame([pre_metrics, post_metrics, delta])
comparison.to_csv("outputs/node_removal_impact_cjng.csv", index=False)
print(f"\n=== CJNG Removal Impact ===")
print(f"Nodes lost: {pre_metrics['Nodes'] - post_metrics['Nodes']} "
      f"(incl. {len(new_isolates)} new isolates)")
print(f"LCC: {pre_metrics['LCC_Size']} → {post_metrics['LCC_Size']}")

# =============================================================================
# 16. Before/after visualization
# =============================================================================

fig, axes = plt.subplots(1, 2, figsize=(18, 8))
pos_orig = nx.spring_layout(G_alliance_connected, k=0.6, iterations=80, seed=42)

cjng_neighbors = set(G_alliance_connected.neighbors(target_node))

# Before
ax1 = axes[0]
deg_before = dict(G_alliance_connected.degree())
sizes_before = [max(deg_before[n] * 50, 80) for n in G_alliance_connected.nodes()]
colors_before = ["red" if n == target_node else
                 "orange" if n in cjng_neighbors else "steelblue"
                 for n in G_alliance_connected.nodes()]
nx.draw_networkx_edges(G_alliance_connected, pos_orig, alpha=0.3, width=0.8, ax=ax1)
nx.draw_networkx_nodes(G_alliance_connected, pos_orig, node_size=sizes_before,
                       node_color=colors_before, alpha=0.7,
                       edgecolors="k", linewidths=0.5, ax=ax1)
deg_thresh = sorted(deg_before.values(), reverse=True)[min(10, len(deg_before)-1)]
labels_before = {n: node_labels.get(n, n) for n in G_alliance_connected.nodes()
                 if deg_before[n] >= deg_thresh or n == target_node}
nx.draw_networkx_labels(G_alliance_connected, pos_orig, labels=labels_before,
                        font_size=7, font_weight="bold", ax=ax1)
ax1.legend(handles=[
    mpatches.Patch(color="red", label=f"Target: {node_labels[target_node]}"),
    mpatches.Patch(color="orange", label="Direct allies"),
    mpatches.Patch(color="steelblue", label="Other nodes")
], loc="upper left", fontsize=9)
ax1.set_title("BEFORE Removal", fontsize=13, fontweight="bold")
ax1.axis("off")

# After
ax2 = axes[1]
pos_after = {n: pos_orig[n] for n in G_post_removal.nodes() if n in pos_orig}
deg_after = dict(G_post_removal.degree())
sizes_after = [max(deg_after[n] * 50, 80) for n in G_post_removal.nodes()]
colors_after = ["orange" if n in cjng_neighbors else "steelblue"
                for n in G_post_removal.nodes()]
nx.draw_networkx_edges(G_post_removal, pos_after, alpha=0.3, width=0.8, ax=ax2)
nx.draw_networkx_nodes(G_post_removal, pos_after, node_size=sizes_after,
                       node_color=colors_after, alpha=0.7,
                       edgecolors="k", linewidths=0.5, ax=ax2)
if deg_after:
    deg_thresh2 = sorted(deg_after.values(), reverse=True)[min(10, len(deg_after)-1)]
    labels_after = {n: node_labels.get(n, n) for n in G_post_removal.nodes()
                    if deg_after[n] >= deg_thresh2 or n in cjng_neighbors}
    nx.draw_networkx_labels(G_post_removal, pos_after, labels=labels_after,
                            font_size=7, font_weight="bold", ax=ax2)
ax2.legend(handles=[
    mpatches.Patch(color="orange", label="Former CJNG allies"),
    mpatches.Patch(color="steelblue", label="Other nodes")
], loc="upper left", fontsize=9)
ax2.set_title(f"AFTER Removal of {node_labels[target_node]}",
              fontsize=13, fontweight="bold")
ax2.axis("off")

plt.suptitle(f"Targeted Node Removal: {node_labels[target_node]} (CJNG)",
             fontsize=15, fontweight="bold", y=1.02)
plt.tight_layout()
plt.savefig("outputs/node_removal_before_after.png", dpi=200, bbox_inches="tight")
plt.close()

# =============================================================================
# 17. Sequential targeted attack (top-5 hubs)
# =============================================================================

G_attack = G_alliance_connected.copy()
attack_log = []

comps_0 = list(nx.connected_components(G_attack))
attack_log.append({"Step": 0, "Removed": "(none)", "Removed_Type": "",
                   "Nodes_Left": G_attack.number_of_nodes(),
                   "Edges_Left": G_attack.number_of_edges(),
                   "Components": len(comps_0),
                   "LCC_Size": len(max(comps_0, key=len))})

for step in range(1, 6):
    deg = dict(G_attack.degree())
    if not deg:
        break
    top_node = max(deg, key=deg.get)
    top_label = node_labels.get(top_node, top_node)
    G_attack.remove_node(top_node)
    G_attack.remove_nodes_from(list(nx.isolates(G_attack)))

    comps = list(nx.connected_components(G_attack))
    lcc = max(comps, key=len) if comps else set()
    attack_log.append({"Step": step,
                       "Removed": f"{top_label} (deg={deg[top_node]})",
                       "Removed_Type": node_type.get(top_node, "Unknown"),
                       "Nodes_Left": G_attack.number_of_nodes(),
                       "Edges_Left": G_attack.number_of_edges(),
                       "Components": len(comps), "LCC_Size": len(lcc)})

attack_df = pd.DataFrame(attack_log)
attack_df.to_csv("outputs/sequential_attack_log.csv", index=False)

fig, axes = plt.subplots(1, 2, figsize=(16, 6))

axes[0].plot(attack_df["Step"], attack_df["LCC_Size"], "o-",
             color="crimson", linewidth=2, markersize=8)
axes[0].fill_between(attack_df["Step"], attack_df["LCC_Size"],
                     alpha=0.15, color="crimson")
for _, row in attack_df.iterrows():
    if row["Step"] > 0:
        axes[0].annotate(row["Removed"].split(" (")[0],
                         xy=(row["Step"], row["LCC_Size"]),
                         textcoords="offset points", xytext=(0, 12),
                         fontsize=8, fontweight="bold", ha="center",
                         color="darkred")
axes[0].set_xlabel("Removal Step"); axes[0].set_ylabel("LCC Size")
axes[0].set_title("LCC Shrinkage Under Sequential Hub Removal", fontweight="bold")
axes[0].set_xticks(attack_df["Step"])
axes[0].grid(True, alpha=0.3)

axes[1].plot(attack_df["Step"], attack_df["Components"], "s-",
             color="steelblue", linewidth=2, markersize=8)
axes[1].fill_between(attack_df["Step"], attack_df["Components"],
                     alpha=0.15, color="steelblue")
for _, row in attack_df.iterrows():
    if row["Step"] > 0:
        axes[1].annotate(row["Removed"].split(" (")[0],
                         xy=(row["Step"], row["Components"]),
                         textcoords="offset points", xytext=(0, 12),
                         fontsize=8, fontweight="bold", ha="center",
                         color="darkblue")
axes[1].set_xlabel("Removal Step"); axes[1].set_ylabel("Components")
axes[1].set_title("Network Fragmentation (Component Count)", fontweight="bold")
axes[1].set_xticks(attack_df["Step"])
axes[1].grid(True, alpha=0.3)

plt.suptitle("Network Fragmentation: Sequential Hub Removal",
             fontsize=15, fontweight="bold", y=1.02)
plt.tight_layout()
plt.savefig("outputs/sequential_attack_lcc.png", dpi=200, bbox_inches="tight")
plt.close()

# =============================================================================
# 18. Post-disruption rewiring predictions
# =============================================================================

G_post = G_alliance_connected.copy()
G_post.remove_node("N10025")
G_post.remove_nodes_from([n for n in G_post.nodes() if G_post.degree(n) == 0])

post_nodes = sorted(G_post.nodes())
post_non_edges = [(u, v) for i, u in enumerate(post_nodes)
                  for v in post_nodes[i+1:] if not G_post.has_edge(u, v)]

X_post = np.array([compute_dyadic_features(u, v, G_post, G_rivalry, G_signed)
                   for u, v in post_non_edges])
probs_post = lr_full.predict_proba(X_post)[:, 1]

rewiring_df = pd.DataFrame({
    "Node_A": [p[0] for p in post_non_edges],
    "Name_A": [node_labels.get(p[0], p[0]) for p in post_non_edges],
    "Type_A": [node_type.get(p[0], "Unknown") for p in post_non_edges],
    "Node_B": [p[1] for p in post_non_edges],
    "Name_B": [node_labels.get(p[1], p[1]) for p in post_non_edges],
    "Type_B": [node_type.get(p[1], "Unknown") for p in post_non_edges],
    "Prob": np.round(probs_post, 4)
}).sort_values("Prob", ascending=False)

top20_rewiring = rewiring_df.head(20).reset_index(drop=True)
top20_rewiring.index += 1
top20_rewiring.to_csv("outputs/top20_post_disruption_rewiring.csv", index=False)

# Rewiring visualization
fig, ax = plt.subplots(figsize=(14, 10))
pos_post = nx.spring_layout(G_post, k=0.6, iterations=80, seed=42)
nx.draw_networkx_edges(G_post, pos_post, alpha=0.3, width=0.8, ax=ax)

top10_pairs = list(zip(top20_rewiring.head(10)["Node_A"],
                       top20_rewiring.head(10)["Node_B"]))
valid_pred_edges = [(u, v) for u, v in top10_pairs
                    if u in pos_post and v in pos_post]
nx.draw_networkx_edges(G_post, pos_post, edgelist=valid_pred_edges,
                       edge_color="green", style="dashed", width=2,
                       alpha=0.8, ax=ax)

cjng_neighbor_nodes = set(G_alliance_connected.neighbors("N10025"))
colors_post, sizes_post = [], []
for n in G_post.nodes():
    if n == "N10013":
        colors_post.append("red"); sizes_post.append(300)
    elif n in cjng_neighbor_nodes:
        colors_post.append("orange"); sizes_post.append(150)
    else:
        colors_post.append("steelblue"); sizes_post.append(100)

nx.draw_networkx_nodes(G_post, pos_post, node_size=sizes_post,
                       node_color=colors_post, alpha=0.7,
                       edgecolors="k", linewidths=0.5, ax=ax)

label_nodes = set()
for u, v in valid_pred_edges:
    label_nodes.update([u, v])
label_nodes.add("N10013")
labels_post = {n: node_labels.get(n, n) for n in label_nodes if n in pos_post}
nx.draw_networkx_labels(G_post, pos_post, labels=labels_post,
                        font_size=7, font_weight="bold", ax=ax)

ax.legend(handles=[
    mpatches.Patch(color="red", label="Sinaloa"),
    mpatches.Patch(color="orange", label="Former CJNG ally"),
    mpatches.Patch(color="steelblue", label="Other"),
    mpatches.Patch(color="green", alpha=0.8, label="Predicted new alliance"),
], loc="upper left", fontsize=9)
ax.set_title("Post-CJNG Network with Predicted Rewiring",
             fontsize=14, fontweight="bold")
ax.axis("off")
plt.tight_layout()
plt.savefig("outputs/post_disruption_rewiring.png", dpi=200, bbox_inches="tight")
plt.close()

# =============================================================================
# 19. Optimal targeting under rewiring (k=1, exhaustive)
# =============================================================================

plt.close('all')
gc.collect()


def rewire_and_measure(G_orig, removal_set, lr_model, G_riv, G_sign, alpha):
    """Remove nodes, rewire via logistic model, return post-rewiring LCC size."""
    surviving = set(G_orig.nodes()) - removal_set
    G_rem = G_orig.subgraph(surviving).copy()
    iso = [n for n in G_rem.nodes() if G_rem.degree(n) == 0]
    G_rem.remove_nodes_from(iso)

    if G_rem.number_of_nodes() == 0:
        return 0

    e_lost = G_orig.number_of_edges() - G_rem.number_of_edges()
    n_new_edges = max(1, int(alpha * e_lost))

    rem_nodes = sorted(G_rem.nodes())
    edge_set = set(G_rem.edges())
    non_edges = [(u, v) for i, u in enumerate(rem_nodes)
                 for v in rem_nodes[i+1:]
                 if (u, v) not in edge_set and (v, u) not in edge_set]

    if not non_edges:
        comps = list(nx.connected_components(G_rem))
        return max(len(c) for c in comps) if comps else 0

    # Precompute neighbor sets
    all_nb = {n: set(G_rem.neighbors(n)) for n in rem_nodes}
    riv_nb = {n: set(G_riv.neighbors(n)) if G_riv.has_node(n) else set()
              for n in rem_nodes}
    sign_nb = {n: set(G_sign.neighbors(n)) if G_sign.has_node(n) else set()
               for n in rem_nodes}

    rows = []
    for u, v in non_edges:
        shared_allies = len(all_nb[u] & all_nb[v])
        shared_rivals = len(riv_nb[u] & riv_nb[v])
        su = node_specialty.get(u, "Undocumented")
        sv = node_specialty.get(v, "Undocumented")
        comp = int(su != sv and su != "Undocumented" and sv != "Undocumented")
        same_st = int(node_state.get(u, "") == node_state.get(v, "")
                      and node_state.get(u, "") != "")
        balance = 0
        for w in sign_nb[u] & sign_nb[v]:
            balance += 1 if G_sign[u][w].get("weight", 0) * \
                            G_sign[v][w].get("weight", 0) > 0 else -1
        deg_prod = G_rem.degree(u) * G_rem.degree(v)
        rows.append([shared_allies, shared_rivals, comp, same_st,
                     balance, deg_prod])

    probs = lr_model.predict_proba(np.array(rows))[:, 1]
    top_idx = np.argsort(probs)[::-1][:n_new_edges]
    for idx in top_idx:
        G_rem.add_edge(*non_edges[idx])

    comps = list(nx.connected_components(G_rem))
    return max(len(c) for c in comps) if comps else 0


# Precompute centrality rankings
deg_ranking = sorted(G_alliance_connected.nodes(),
                     key=lambda n: G_alliance_connected.degree(n), reverse=True)
btw_ranking = sorted(btw_cent.keys(), key=lambda n: btw_cent[n], reverse=True)

alphas = [0.25, 0.50, 0.75]
results_all = []

print("\n=== Optimal Targeting (k=1) ===")
candidates = list(combinations(nodes_list, 1))
print(f"Evaluating {len(candidates)} candidates...")

for alpha in alphas:
    best_lcc, best_set = float('inf'), None
    for s_set in candidates:
        lcc = rewire_and_measure(G_alliance_connected, set(s_set),
                                 lr_full, G_rivalry, G_signed, alpha)
        if lcc < best_lcc:
            best_lcc = lcc
            best_set = s_set

    deg_lcc = rewire_and_measure(G_alliance_connected, set(deg_ranking[:1]),
                                  lr_full, G_rivalry, G_signed, alpha)
    btw_lcc = rewire_and_measure(G_alliance_connected, set(btw_ranking[:1]),
                                  lr_full, G_rivalry, G_signed, alpha)

    np.random.seed(42)
    rand_lccs = [rewire_and_measure(
        G_alliance_connected,
        {nodes_list[np.random.choice(len(nodes_list))]},
        lr_full, G_rivalry, G_signed, alpha) for _ in range(20)]
    rand_mean = np.mean(rand_lccs)

    opt_names = [node_labels.get(n, n) for n in best_set]
    print(f"  α={alpha}: Optimal={opt_names} LCC={best_lcc}  "
          f"Degree={deg_lcc}  Between={btw_lcc}  Random={rand_mean:.1f}")

    for strat, targets, lcc_val in [
        ("Optimal", "; ".join(opt_names), best_lcc),
        ("Degree", "; ".join(node_labels.get(n, n) for n in deg_ranking[:1]), deg_lcc),
        ("Betweenness", "; ".join(node_labels.get(n, n) for n in btw_ranking[:1]), btw_lcc),
        ("Random (mean)", "(20 samples)", round(rand_mean, 1)),
    ]:
        results_all.append({"k": 1, "alpha": alpha, "Strategy": strat,
                            "Targets": targets, "Post_Rewiring_LCC": lcc_val})

opt_df = pd.DataFrame(results_all)
opt_df.to_csv("outputs/optimal_targeting_results.csv", index=False)

# Grouped bar chart
fig, ax = plt.subplots(figsize=(12, 6))
strategies = ["Optimal", "Degree", "Betweenness", "Random (mean)"]
colors = {"Optimal": "#2ecc71", "Degree": "#e74c3c",
          "Betweenness": "#3498db", "Random (mean)": "#95a5a6"}
x = np.arange(len(alphas))
width = 0.18

for j, strat in enumerate(strategies):
    vals = [opt_df[(opt_df["alpha"] == a) & (opt_df["Strategy"] == strat)]
            ["Post_Rewiring_LCC"].values[0] for a in alphas]
    bars = ax.bar(x + j * width, vals, width, label=strat,
                  color=colors[strat], alpha=0.85, edgecolor="black",
                  linewidth=0.5)
    for bar, v in zip(bars, vals):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                str(int(v)), ha="center", fontsize=9, fontweight="bold")

ax.set_xlabel("Rewiring Capacity (α)", fontsize=12)
ax.set_ylabel("Post-Rewiring LCC Size", fontsize=12)
ax.set_title("Single-Node Removal (k=1): Which Target Minimizes "
             "Post-Rewiring Connectivity?", fontsize=13, fontweight="bold")
ax.set_xticks(x + 1.5 * width)
ax.set_xticklabels([f"α = {a}" for a in alphas], fontsize=11)
ax.legend(fontsize=10)
ax.grid(True, alpha=0.3, axis="y")
plt.tight_layout()
plt.savefig("outputs/optimal_targeting_comparison.png", dpi=200,
            bbox_inches="tight")
plt.close()

print("\nDone. All outputs saved to outputs/")
