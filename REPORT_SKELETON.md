# Networks Project Report Skeleton
## Dataset: BACRIM 2020 Mexican Cartel Network (Prieto-Curiel & Campedelli, 2023)

## 1. Introduction
### 1.1 Context and Motivation
- Introduce organized crime as a relational system where alliances and rivalries shape power, coordination, and conflict.
- Present BACRIM 2020 as a signed network dataset with positive and negative ties among Mexican cartels.
- Explain why network science is a suitable framework: it captures structure beyond individual actors.

### 1.2 Research Questions
- RQ1: What are the key structural properties of the cartel alliance network?
- RQ2: Is the observed alliance network compatible with a random process, or does it show structured organization?
- RQ3: Which currently disconnected cartel pairs are most likely to form future alliances based on network topology?

### 1.3 Contributions of This Report
- Signed network construction from raw BACRIM files.
- Empirical comparison to two null models (ER and BA).
- Topological link prediction using Jaccard and Adamic-Adar metrics.

## 2. Methods
### 2.1 Data and Preprocessing
- Files used:
  - `BACRIM2020_Nodes.csv`
  - `BACRIM2020_Alliances.csv`
  - `BACRIM2020_Rivals.csv`
- Build one signed undirected master graph:
  - Alliance edge weight = +1, type = `alliance`
  - Rivalry edge weight = -1, type = `rivalry`
- Build alliance-only subgraph for predictive tasks.
- Mention duplicate handling and undirected edge canonicalization.

### 2.2 Topic 1: Foundations of Networks
- Metrics on alliance graph:
  - Number of nodes `N`
  - Number of edges `E`
  - Density
  - Diameter
- Centrality:
  - Degree centrality to detect highly connected cartels.
  - Betweenness centrality to detect brokerage/intermediation roles.
- Visualization:
  - Fruchterman-Reingold force-directed layout on signed master graph.
  - Green edges = alliances, red edges = rivalries.

### 2.3 Topic 2: Random Graph Models
- Generate two null graphs with same `N` and `E` as empirical alliance graph:
  - Erdos-Renyi (ER)
  - Barabasi-Albert (BA)
- Compare across:
  - Global clustering coefficient `C`
  - Average path length `L`
- Degree distribution analysis:
  - Plot empirical `P(k)` on log-log axes.
  - Assess whether heavy-tailed behavior is consistent with scale-free intuition.

### 2.4 Topic 3: Link Prediction (Machine Learning with Network Data)
- Candidate links: all currently non-adjacent pairs in alliance graph.
- Similarity scores:
  - Jaccard coefficient
  - Adamic-Adar index
- Ranking rule:
  - Sort descending by Jaccard, then Adamic-Adar.
- Output:
  - Top 10 most likely future alliance links.

## 3. Results
### 3.1 Descriptive Structure of the Alliance Network
- Use `outputs/basic_stats_alliance_network.csv`.
- Report exact values for `N`, `E`, density, and diameter.
- Interpret what these values imply (fragmentation vs cohesion).

### 3.2 Central Actors
- Use:
  - `outputs/top5_degree_centrality.csv`
  - `outputs/top5_betweenness_centrality.csv`
- Discuss overlap/non-overlap between top degree and top betweenness nodes.
- Explain strategic interpretation:
  - High-degree actors: many allies.
  - High-betweenness actors: brokers/bridges controlling indirect connectivity.

### 3.3 Signed Network Visualization
- Insert figure: `outputs/signed_network_fruchterman_reingold.png`.
- Describe visible clusters, bridge actors, and concentration of rivalry ties.
- Connect visual evidence with centrality rankings.

### 3.4 Null Model Comparison (ER vs BA vs Real)
- Use `outputs/random_graph_model_comparison.csv`.
- Present table with `C` and `L` for all three networks.
- Interpretation template:
  - If real `C` >> ER `C`, alliances are more locally clustered than random.
  - If real `L` is closer to BA than ER, discuss possible hub-driven organization.
  - If real network departs from both, argue for domain-specific mechanisms.

### 3.5 Degree Distribution Evidence
- Insert figure: `outputs/degree_distribution_loglog.png`.
- Comment on linearity/non-linearity in log-log space.
- State whether evidence is suggestive (not definitive proof) of power-law behavior.

### 3.6 Predicted Future Alliances
- Use `outputs/top10_predicted_future_alliances.csv`.
- Report top 10 pairings with both scores.
- Interpret why highest-ranked pairs are plausible:
  - Shared neighborhood overlap (Jaccard)
  - Shared rare/common neighbors weighted by informativeness (Adamic-Adar).

## 4. Conclusion
### 4.1 Answers to Research Questions
- Summarize findings for RQ1, RQ2, and RQ3 in 3 short paragraphs.

### 4.2 Substantive Interpretation
- Explain what the network structure suggests about coordination, brokerage, and conflict dynamics in cartel ecosystems.

### 4.3 Limitations
- Static snapshot (2020) rather than longitudinal dynamics.
- Topological prediction only (no geography, economics, or enforcement covariates).
- Potential data incompleteness or reporting bias.

### 4.4 Future Work
- Temporal network analysis over multiple years.
- Signed-link prediction models that incorporate rivalry directly.
- ERGM/SBM/community-detection extensions.

## 5. Reproducibility Appendix
- Script: `bacrim_network_analysis.R`
- Main output folder: `outputs/`
- Suggested run command:
  - `Rscript bacrim_network_analysis.R`
- If data are outside project root:
  - `BACRIM_DATA_DIR=/path/to/csvs BACRIM_OUTPUT_DIR=outputs Rscript bacrim_network_analysis.R`
