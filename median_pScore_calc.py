# code has been cleaned up from the original version for better readability (before there was a lot of commented code and debug codes in a notebook file and its messy)

import os
import re
import numpy as np
import pandas as pd
from IPython.display import display

ROOT_DIR = "."
TOURNAMENT_INFO = {
    "4 Digit osumania World Cup 3": {"tier": "B", "year": 2021},
}
TIER_WEIGHTS = {"S": 1.1, "A": 0.85, "B": 0.7, "C": 0.55}

def normalize_name(name):
    name = name.lower()
    name = re.sub(r'[^a-z0-9 ]', '', name)
    name = re.sub(r'\s+', '_', name)
    return name

_normalized_info = {normalize_name(k): v for k, v in TOURNAMENT_INFO.items()}

def get_info_from_folder(folder_name):
    norm = normalize_name(folder_name)
    info = _normalized_info.get(norm, None)
    if info is None:
        return {"tier": "C", "year": None}
    return {"tier": info.get("tier", "C"), "year": info.get("year", None)}

def get_decay_weight(year, base_year=2023, decay_per_year=0.3, min_weight=0.5):
    if year is None or year > base_year:
        return 1.0
    decay = np.exp(-decay_per_year * (base_year - year))
    return max(decay, min_weight)

def weighted_mean(group):
    return np.average(group["pScore"], weights=group["Weight"])

def iqr_mean(series):
    q1 = series.quantile(0.25)
    q3 = series.quantile(0.75)
    iqr_values = series[(series >= q1) & (series <= q3)]
    if not iqr_values.empty:
        return iqr_values.mean()
    else:
        return np.nan

all_pscores = []

for folder in os.listdir(ROOT_DIR):
    folder_path = os.path.join(ROOT_DIR, folder)
    if not os.path.isdir(folder_path) or folder == "manual_work":
        continue
    info = get_info_from_folder(folder)
    tier = info["tier"]
    year = info["year"]
    weight = TIER_WEIGHTS.get(tier, 1.0)
    decay_weight = get_decay_weight(year)
    print(f"Processing folder: {folder} (Tier: {tier}, Weight: {weight}, Year: {year}, DecayWeight: {decay_weight})")
    for file in os.listdir(folder_path):
        if file.endswith("_leaderboard.csv"):
            csv_path = os.path.join(folder_path, file)
            df = pd.read_csv(csv_path)
            required = {"Player ID", "Player Name", "pScore", "Maps Played"}
            if not required.issubset(df.columns):
                print(f"Skipping {csv_path} due to missing columns: {required - set(df.columns)}")
                continue
            df["Maps Played Num"] = df["Maps Played"].astype(str).str.extract(r"^(\d+)")
            df["Maps Played Num"] = pd.to_numeric(df["Maps Played Num"], errors="coerce").fillna(0).astype(int)
            df["Tier"] = tier
            df["Weight"] = weight
            df["Tournament"] = folder
            df["Year"] = year
            df["DecayWeight"] = decay_weight
            df["weighted_pScore"] = df["pScore"] * df["Weight"]
            df["final_weighted_pScore"] = df["weighted_pScore"] * df["DecayWeight"]
            all_pscores.append(df[["Player ID", "Player Name", "pScore", "weighted_pScore", "final_weighted_pScore", "Maps Played Num", "Tier", "Weight", "Tournament", "Year", "DecayWeight"]])

if all_pscores:
    combined = pd.concat(all_pscores, ignore_index=True)
    display(combined)
    combined = combined.copy()
    multi_name_ids = (
        combined.groupby('Player ID')['Player Name']
        .nunique()
        .pipe(lambda s: s[s > 1])
    )
    canonical_name = {}
    changes = []
    for pid, rows in combined.groupby('Player ID'):
        yr = rows['Year'].fillna(-np.inf)
        max_year = yr.max()
        cand = rows.loc[yr == max_year, 'Player Name']
        if cand.empty:
            name = rows['Player Name'].iloc[-1]
        else:
            modes = cand.mode()
            name = modes.iloc[-1] if not modes.empty else cand.iloc[-1]
        canonical_name[pid] = name
        if pid in multi_name_ids.index:
            orig_names = sorted(rows['Player Name'].unique())
            if len(orig_names) > 1 or name not in orig_names:
                changes.append((pid, orig_names, name, None if max_year == -np.inf else int(max_year)))
    combined['Player Name (original)'] = combined['Player Name']
    combined['Player Name'] = combined['Player ID'].map(canonical_name)
    if changes:
        print("Merged names to latest-year canonical name for these IDs:")
        for pid, names, chosen, yr in changes:
            print(f"  ID {pid}: {names}  ->  '{chosen}' (year {yr})")
    else:
        print("No IDs with multiple names found.")
    summary = (
        combined.groupby(["Player ID", "Player Name"], as_index=False)
        .agg(
            median_pScore=("final_weighted_pScore", "median"),
            total_maps_played=("Maps Played Num", "sum"),
            num_appearances=("pScore", "count")
        )
    )
    summary = summary.rename(columns={"Player ID": "user_id"})
    def logistic_activation(x, k=0.6, x0=4, L=1.0):
        return L / (1 + np.exp(-k * (x - x0)))
    def reward_boost(n, base=1.0, reward=1.10, threshold=20):
        if n > threshold:
            return reward
        return base
    summary["adjusted_median_pScore"] = summary.apply(
        lambda row: (
            row["median_pScore"] * logistic_activation(row["num_appearances"])
        ),
        axis=1
    )
    summary = summary.sort_values("adjusted_median_pScore", ascending=False)
    summary.to_csv("combined_player_weighted_stats.csv", index=False)
    print("Combined leaderboard with tournament weighting and decay saved as combined_player_weighted_stats.csv")
else:
    print("No leaderboard files found.")
