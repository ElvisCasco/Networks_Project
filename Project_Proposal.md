# Project Proposal: Latent Pathways and Post-Disruption Reorganization in Mexican Cartel Networks

**Course:** Networks I: Concepts and Algorithms  
**Dataset:** BACRIM 2020 — Mexican Cartel Signed Network (Prieto-Curiel & Campedelli, 2023)

---

## 1. Research Question and Motivation

Research on organized crime disruption typically assumes that removing central actors weakens criminal organizations by fragmenting their visible alliance structure. However, empirical evidence from Mexico suggests otherwise: Calderón et al. (2015) show that kingpin removals triggered violence spikes and organizational reconfiguration rather than lasting collapse, while Duijn, Kashirin & Sloot (2014) demonstrate more broadly that criminal network disruption is often "relatively ineffective" because the network reorganizes around remaining structure. These findings imply that cartel networks contain latent relational pathways — indirect coordination channels, shared enemies, territorial proximity, and brokerage alternatives — that become strategically activated when central actors are removed.

Morselli (2009) establishes that criminal organizations are structured around brokerage and structural holes, and Lindelauf, Borm & Hamers (2009) provide theoretical foundations for why such networks are only partially observable due to deliberate secrecy. The question, therefore, is not only *whether* targeted disruption fragments a cartel network, but *whether the pre-existing latent structure conditions how the network is likely to reorganize afterward*.

Using the BACRIM2020 dataset (Prieto-Curiel & Campedelli, 2023), this project models inter-cartel relations as a signed cross-sectional network (alliances = positive ties, rivalries = negative ties) and asks:

The hypothesis we want to test is: Pre-existing latent relational pathways in the cartel network condition the likely form of post-disruption reorganization after the removal of structurally central actors.

This has direct policy relevance: if disruption inadvertently activates dormant alliances — especially through "enemy-of-my-enemy" dynamics rooted in structural balance theory (Cartwright & Harary, 1956) — then kingpin strategies may produce reorganized coalitions rather than lasting fragmentation. Understanding latent structure before intervention enables smarter targeting.

## 2. Data

The BACRIM2020 dataset (Prieto-Curiel & Campedelli, 2023) contains 100+ criminal organizations active in Mexico, with weighted alliance and rivalry edges coded from open-source intelligence collected by CentroGeo, GeoInt, and DataLab (via national/local newspapers and narco blogs; source: [ppdata.politicadedrogas.org](https://ppdata.politicadedrogas.org/)). Three CSV files provide nodes (group name, state), alliances, and rivalries, each with edge weights reflecting the number of Mexican states where the relationship holds. This naturally yields a signed, weighted, undirected network suitable for structural analysis. Qualitative context on individual cartels (CJNG, Sinaloa, etc.) and their territorial dynamics will be drawn from InSight Crime profiles to support substantive interpretation of structural findings.

## 3. Methodology

The analysis proceeds in six steps, each building on the previous:

**Step 1 — Signed Network Construction.** Build two network layers (alliance and rivalry) on the same node set. Analyze them separately and jointly as a signed structure, since a highly connected group in the alliance layer plays a substantively different role than one connected through rivalries.

**Step 2 — Identification of Structurally Central Actors.** Compute degree, betweenness, and eigenvector centrality, plus brokerage / structural-hole indicators, following the comparative framework of Bright et al. (2015). Focus on actors in central brokerage positions — those connecting otherwise weakly linked factions — since their removal is theoretically most likely to expose dormant coordination alternatives (Morselli, 2009; Everton, 2012).

**Step 3 — Latent Pathway Inference (Pre-Disruption).** Before any node is removed, approximate latent relational pathways between currently non-adjacent dyads using:

- Jaccard similarity in alliance neighborhoods (Liben-Nowell & Kleinberg, 2007)
- Jaccard similarity in rivalry neighborhoods
- Adamic-Adar overlap in alliance and rivalry neighborhoods (Adamic & Adar, 2003)
- Community co-membership (Doreian & Mrvar, 2009) and short indirect path length

Particular weight is given to **shared rivals** ("enemy of my enemy"), since in criminal contexts mutual enemies create strong incentives for coordination even without visible alliance ties (Everton, 2012; Dorff, Gallop & Minhas, 2020). Adamic-Adar is especially suited here: shared low-degree rivals are more informative than common high-degree enemies shared by many actors. The general link-prediction framework follows Lü & Zhou (2011). These indicators serve as proxies for *latent relational opportunity*, not direct evidence of hidden ties.

**Step 4 — Node Removal Simulation.** Simulate the removal of the most central actors (identified in Step 2) and measure the resulting impact on fragmentation, component structure, bridge loss, alliance cohesion, community dislocation, and signed triad balance. This follows the error-and-attack tolerance framework of Albert, Jeong & Barabási (2000) and the comparative dismantling analysis of Wandelt et al. (2018), adapted to a signed-network setting. This approximates the structural effect of targeted kingpin interventions.

**Step 5 — Counterfactual Post-Removal Reconstruction.** After removing key actors, reconstruct a plausible post-disruption network by adding new ties only where they are supported by strong pre-removal latent scores (from Step 3). For signed tie prediction, the approach draws on Leskovec, Huttenlocher & Kleinberg (2010), who demonstrate that structural features can predict both positive and negative links. Rank all eligible non-adjacent dyads by their composite latent score and add top-scoring ties (or apply a threshold rule). Analyze whether plausible recombination reduces fragmentation, restores brokerage, or generates new coalitional blocs.

**Step 6 — Validation via Internal Link Prediction.** Validate the latent score function by randomly withholding a subset of observed ties, recalculating scores from the remaining structure, and checking whether withheld ties receive systematically higher predicted scores than unrelated dyads. Evaluate using AUC, precision-at-k, recall of held-out ties, and average rank of withheld ties. This does not prove hidden edges exist, but demonstrates the score captures meaningful relational structure.

## 4. Expected Contributions

1. A **theory-driven framework** connecting cartel resilience to latent structural opportunity, going beyond simple fragmentation analysis.
2. A **signed-network methodology** that treats alliances and rivalries as substantively distinct layers, including rivalry-based similarity as a predictor of future coordination.
3. A **counterfactual reconstruction procedure** that identifies plausible directions of post-disruption reorganization from cross-sectional data — appropriate given the hidden nature of cartel networks.
4. An **internal validation protocol** that benchmarks the latent score against held-out observed ties, providing indirect but rigorous evidence for the approach.

## 5. Anticipated Challenges and Mitigation

| Challenge | Mitigation Strategy |
|---|---|
| **Cross-sectional data (no temporal variation):** Cannot observe actual post-disruption dynamics. | Frame results as *counterfactual plausibility*, not causal claims. The reconstructed network represents the most structurally supported direction of reorganization, not a prediction of realized outcomes. |
| **Partial observability:** The dataset captures only reported ties; latent edges are unobserved by definition. | Use the link-prediction validation (Step 6) to show the score recovers artificially hidden edges, establishing it as a credible proxy for latent relational opportunity. |
| **Threshold sensitivity in reconstruction:** Results may depend on how many ties are added post-removal. | Conduct sensitivity analysis across multiple thresholds and report how the key findings (fragmentation recovery, new coalition formation) vary. |
| **Signed network complexity:** Standard centrality and similarity metrics are designed for unsigned networks. | Compute alliance- and rivalry-specific versions of each metric separately, then combine them in a principled composite score. Leverage signed triad balance theory to validate structural coherence. |
| **Small network size:** With ~100 nodes, statistical power for link prediction may be limited. | Report rank-based metrics (AUC, average rank) that are robust at smaller scales, and use repeated random splits to stabilize estimates. |

## 6. Tools and Implementation

The project will be implemented in **Python** using `networkx` for graph construction and analysis, `numpy`/`pandas` for data manipulation, and `matplotlib`/`seaborn` for visualization. The final report will be rendered via **Quarto** (`.qmd`). All code and outputs will be reproducible from the repository.

## 7. Application to Recent Events

A natural question is whether this dataset allows simulating the removal of specific cartel leaders — for instance, Joaquín "El Chapo" Guzmán (extradited 2017) or Ismael "El Mayo" Zambada (arrested 2024). The answer is: not directly, but the dataset supports an analytically stronger alternative.

BACRIM2020 models 150 organizational factions, not individual people. There is no node for "El Chapo" or "El Mayo" as persons. However, the dataset captures the sub-organizational factional structure that is shaped by - and ultimately more consequential than - individual leadership. The Sinaloa Cartel ecosystem alone is represented by multiple faction nodes:

| Node | Faction | Real-world leadership association |
|---|---|---|
| N10013 | Cártel de Sinaloa | Umbrella organization |
| N10138 | MZ | Mayo Zambada's faction |
| N10091 | Los Chapitos | El Chapo's sons (Ovidio, Iván, Alfredo) |
| N10097 | Los Dámasos | Dámaso López faction |
| N10058 | Gente Nueva | Sinaloa's armed wing |
| N10113 | Los Ninis | Chapitos' enforcement arm |
| N10083 | Los Ántrax | Sinaloa-aligned hitmen |
| N10122 | Los Rusos | R. Caro Quintero-linked splinter |

Crucially, the data also encodes intra-Sinaloa rivalries — Chapitos vs. Dámasos (weight 3), Chapitos vs. Rusos (weight 2), even Sinaloa vs. Chapitos (weight 1) — as well as cross-cartel defections such as the Dámasos–CJNG alliance (weight 1). These fracture lines mirror the real post-2017 fragmentation of the Sinaloa Cartel after El Chapo's removal.

This means the project frames disruption at the faction level: removing an organizational node (e.g., N10013/Sinaloa, N10138/MZ, or N10091/Chapitos) and analyzing how the surrounding alliance-rivalry structure reconfigures. This is more structurally grounded than modeling individual arrest, because what matters for network reorganization is not the loss of one person but the collapse of the coordination structure a faction provides. The latent pathway methodology can then ask whether the pre-existing structure predicted precisely the kind of reconfiguration that was historically observed — for example, whether shared-rival scores would have flagged the Dámasos–CJNG alignment as a plausible post-disruption outcome before it materialized. The Sinaloa intra-factional data thus provides a natural empirical anchor for the project, since the post-2017 fragmentation of the Sinaloa Cartel is one of the best-documented cases of post-disruption reorganization in the Mexican drug war.

The recent reported death of Nemesio Oseguera Cervantes, "El Mencho," leader of CJNG, provides a second - and arguably even more consequential - empirical anchor for the project. In the BACRIM2020 dataset, CJNG (N10025) is the single most connected node in the entire network, with 28 alliance ties and 29 rivalry ties spanning virtually every major and minor faction in Mexico. Its sub-organizational ecosystem includes:

| Node | Faction | Role in CJNG structure |
|---|---|---|
| N10025 | CJNG | Core organization (El Mencho's command) |
| N10096 | Los Cuinis | Financial arm (Mencho's wife's family, the Valencia-González clan) |
| N10060 | Grupo Élite del CJNG | Armed enforcement wing |
| N10035 | CJNG Comando la Mancha | Regional sub-cell (Baja California) |

The dataset reveals several features that make the CJNG disruption scenario analytically rich:

**1. Massive brokerage role.** CJNG bridges alliances with 28 distinct factions — from Fuerza Anti-Unión Tepito (w=5) and ACME (w=3) down to smaller regional cells. Removing N10025 would sever more alliance connections than any other single-node removal, making it the strongest test case for whether latent pathways can predict post-disruption reconfiguration.

**2. Ambivalent ties.** Several groups maintain *simultaneous* alliance and rivalry ties with CJNG — notably Cártel de Tláhuac (alliance w=3, rivalry w=3), La Unión Tepito (alliance w=3, rivalry w=3), and Guerreros Unidos (alliance w=2, rivalry w=1). These ambivalent relationships are structurally unstable and likely the first to shift after CJNG's collapse. The signed-network framework is specifically designed to capture this kind of tension.

**3. Dense rivalry neighborhood.** CJNG's major rivals include La Nueva Familia Michoacana (w=13), Cártel de Sinaloa (w=7), Cártel del Noreste (w=6), and Cárteles Unidos (w=6). These groups share a common enemy in CJNG. The "enemy-of-my-enemy" logic central to the latent pathway methodology predicts that these rivals may *not* cooperate after CJNG's fall — because their mutual hostility toward CJNG was one of the few structural factors aligning them. Removing the shared enemy could expose their own latent rivalries and trigger a new multi-front reconfiguration.

**4. Los Cuinis dependency.** Los Cuinis (N10096) is connected to CJNG with the highest alliance weight in the dataset (w=6, across 6 states), reflecting the family-based financial integration of El Mencho's organization. After his death, the key structural question is whether Los Cuinis can sustain independent alliances or whether its connections depended entirely on the CJNG umbrella — a question the latent score function can address by checking whether Los Cuinis shares enough indirect structural overlap with other factions to maintain connectivity.

**5. Real-time validation opportunity.** Because El Mencho's death is recent, the reorganization that follows provides an observable outcome against which the project's counterfactual predictions can be qualitatively assessed. If the latent pathway scores identify certain factions as likely post-disruption alliance candidates, subsequent reporting from sources like InSight Crime can serve as an informal check on whether the predicted structural logic materializes.

## 8. Key References

1. Adamic, L.A. & Adar, E. (2003). Friends and neighbors on the Web. *Social Networks*, 25(3), 211–230.
2. Albert, R., Jeong, H. & Barabási, A.-L. (2000). Error and attack tolerance of complex networks. *Nature*, 406, 378–382.
3. Bright, D., Greenhill, C., Reynolds, M., Ritter, A. & Morselli, C. (2015). The use of actor-level attributes and centrality measures to identify key actors. *Journal of Contemporary Criminal Justice*, 31(3), 262–280.
4. Calderón, G., Robles, G., Díaz-Cayeros, A. & Magaloni, B. (2015). The beheading of criminal organizations and the dynamics of violence in Mexico. *Journal of Conflict Resolution*, 59(8), 1455–1485.
5. Cartwright, D. & Harary, F. (1956). Structural balance: A generalization of Heider's theory. *Psychological Review*, 63(5), 277–293.
6. Doreian, P. & Mrvar, A. (2009). Partitioning signed social networks. *Social Networks*, 31(1), 1–11.
7. Dorff, C., Gallop, M. & Minhas, S. (2020). Networks of violence: Predicting conflict in Nigeria. *Journal of Politics*, 82(2), 476–493.
8. Duijn, P.A.C., Kashirin, V. & Sloot, P.M.A. (2014). The relative ineffectiveness of criminal network disruption. *Scientific Reports*, 4, 4238.
9. Everton, S.F. (2012). *Disrupting Dark Networks*. Cambridge University Press.
10. Leskovec, J., Huttenlocher, D. & Kleinberg, J. (2010). Predicting positive and negative links in online social networks. *Proceedings of WWW 2010*, 641–650.
11. Liben-Nowell, D. & Kleinberg, J. (2007). The link-prediction problem for social networks. *JASIST*, 58(7), 1019–1031.
12. Lindelauf, R., Borm, P. & Hamers, H. (2009). The influence of secrecy on the communication structure of covert networks. *Social Networks*, 31(2), 126–137.
13. Lü, L. & Zhou, T. (2011). Link prediction in complex networks: A survey. *Physica A*, 390(6), 1150–1170.
14. Morselli, C. (2009). *Inside Criminal Networks*. Springer.
15. Prieto-Curiel, R. & Campedelli, G.M. (2023). Mexican cartels form a network of alliances and rivalries. Working paper / dataset.
16. Wandelt, S., Sun, X., Feng, D., Zanin, M. & Havlin, S. (2018). A comparative analysis of approaches to network-dismantling. *Scientific Reports*, 8, 13513.

---

*This proposal outlines a feasible, self-contained project that applies core course tools — centrality analysis, random graph comparison, community structure, and link prediction — to a substantively motivated research question grounded in the criminal networks literature and with real-world policy implications.*
