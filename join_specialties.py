"""
Join BACRIM2020_Nodes.csv with Cartel_Specialties.csv

Sources for specialty data:
- DEA National Drug Threat Assessment 2024: https://www.dea.gov/sites/default/files/2025-02/508_5.23.2024%20NDTA-updated.pdf
- DEA National Drug Threat Assessment 2025: https://www.dea.gov/sites/default/files/2025-07/2025NationalDrugThreatAssessment.pdf
- CRS Report R41576 "Mexico: Organized Crime and Drug Trafficking Organizations": https://crsreports.congress.gov/product/details?prodcode=R41576
- InSight Crime cartel profiles: https://insightcrime.org/mexico-organized-crime-news/
- Coscia & Rios (2012) municipality-level cartel data: https://www.michelecoscia.com/?page_id=1032
"""

import pandas as pd

# Load datasets
nodes = pd.read_csv("BACRIM2020_Nodes.csv")
specialties = pd.read_csv("Cartel_Specialties.csv")

# Join on Group name
joined = nodes.merge(specialties, on="Group", how="left")

# Fill NaN for any unmatched groups
joined["Type"] = joined["Type"].fillna("Undocumented")
joined["Primary_Specialty"] = joined["Primary_Specialty"].fillna("Undocumented")
joined["Activities"] = joined["Activities"].fillna("")
joined["Primary_Drugs"] = joined["Primary_Drugs"].fillna("")
joined["Source"] = joined["Source"].fillna("")

# Save joined dataset
joined.to_csv("BACRIM2020_Nodes_With_Specialties.csv", index=False)

# Print summary statistics
print("=" * 60)
print("BACRIM 2020 - Nodes with Specialties (Joined Dataset)")
print("=" * 60)
print(f"\nTotal nodes: {len(joined)}")
print(f"Documented:  {(joined['Primary_Specialty'] != 'Undocumented').sum()}")
print(f"Undocumented: {(joined['Primary_Specialty'] == 'Undocumented').sum()}")

print(f"\n--- Type Distribution ---")
print(joined["Type"].value_counts().to_string())

print(f"\n--- Primary Specialty Distribution ---")
print(joined["Primary_Specialty"].value_counts().to_string())

# Explode activities to count individual ones
documented = joined[joined["Activities"] != ""]
all_activities = documented["Activities"].str.split(";").explode()
print(f"\n--- Activity Frequency (across documented groups) ---")
print(all_activities.value_counts().to_string())

# Explode drugs
has_drugs = joined[joined["Primary_Drugs"] != ""]
all_drugs = has_drugs["Primary_Drugs"].str.split(";").explode()
print(f"\n--- Drug Frequency (across documented groups) ---")
print(all_drugs.value_counts().to_string())

print(f"\n--- Sample of joined data ---")
print(joined[["Node", "ShortName", "State", "Type", "Primary_Specialty", "Activities"]].head(25).to_string(index=False))

print(f"\nOutput saved to: BACRIM2020_Nodes_With_Specialties.csv")
