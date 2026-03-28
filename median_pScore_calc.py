# code has been cleaned up from the original version for better readability (before there was a lot of commented code and debug codes in a notebook file and its messy)

import os
import re
import numpy as np
import pandas as pd
from IPython.display import display

ROOT_DIR = "./tournament_raw_data"


TOURNAMENT_TIERS = {
    "4 Digit osumania World Cup 3": "B",
    "4 Digit osumania World Cup 4": "B",
    "4 Digit osumania World Cup 2024": "B",
    "osumania 4K World Cup 2021": "S",
    "osumania 4K World Cup 2022": "S",
    "osumania 4K World Cup 2023": "S",
    "osumania 4K World Cup 2024": "S",
    "osumania 4K World Cup 2025": "S",
    "osumania 4K Chinese National Cup 2022": "A",
    "osumania 4K Chinese National Cup 2023": "A",
    "osumania 4K Chinese National Cup 2024": "A",
    "osumania 4K Indonesia Cup 2022": "B",
    "osumania Malaysia Tournament 4": "B",
    "osumania Malaysia Tournament 3": "B",
    "osumania LN Tournament 3": "S",
    "GB Cup 2023 Autumn": "A",
    "GB Cup 2024 Spring": "S",
    "Jack House Cup 2024": "A",
    "Jack House Cup 2025": "A",
    "Meow Mania": "S",
    "Speed of Light 2 Lucha Libre Edition": "S",
    "Speed of Light 3": "S",
    "Springtime Osumania Free-for-all Tournament 5": "S",
    "Springtime Osumania Free-for-all Tournament 6": "S",
    "Touhou Project Mania Cup 3rd": "A",
    "Touhou Project Mania Cup 4th": "S",
    "China LAN 2025": "A",
    "Gulano Cup #4": "C",
    "osu!mania Malaysia Tournament 2": "B",
    "Korean Extraterrestrials Tournament 2": "A",
    "Mania Key Clash Cup 2024": "B",
    "GB Cup 2025 Spring": "S",
    "Gulano Cup #5": "B",
    "Mania Collegiate League Summer 2022": "A",
    "Solo Score Rush": "A",
    "The Broken Matrix": "A",
    "Asia Suiji Cup Rhythmus Aquarum": "A",
    "Vietnam National Mania Championship 2022": "B",
    "Vietnamese National Mania Championship 2024": "B",
    "4-Digit 4K South Korean Summer Tournament": "C",
    "4K Korean Mania Tournament 2": "A",
    "4K Korean Mania Tournament": "A",
    "Anti-Meta-Madness": "A",
    "Anti-Meta-Madness 2 Summer Showdown": "A",
    "International Rhythm League Mania 2023": "A",
    "Japanese Mania Championship 2 まだ見ぬ新星を探して": "B",
    "Mania Collegiate League Spring 2023": "A",
    "Mania Collegiate League Spring 2024": "A",
    "Vietnamese Rewind Mania Championship": "C",
    "osu! Philippines Nationals 2024": "B",
    "osu!mania 4K Pid Term Thailand Tournament": "B",
    "osu!mania LN Tournament 4": "S",
    "Vietnamese National Mania Championship 4K 2025": "B",
    "Soundwave Mania 2": "B",
    "Middle East Mania 4k Tournament 2": "B",
    "Vietnam National Mania Championship 2023": "B",
}

TOURNAMENT_YEAR = {
    "4 Digit osumania World Cup 3": 2021,
    "Springtime Osumania Free-for-all Tournament 5": 2021,
    "Speed of Light 2 Lucha Libre Edition": 2021,
    "osumania 4K World Cup 2021": 2021,
    "osumania 4K Chinese National Cup 2021": 2021,
    "osumania Malaysia Tournament": 2021,
    "osu! Philippines Nationals 2021": 2021,
    "osu!mania Thailand Pro League 2021": 2021,
    "Vietnam National Mania Championship 2021": 2021,
    "osumania 4K Chinese National Cup 2022": 2022,
    "osumania 4K Indonesia Cup 2022": 2022,
    "Korean Extraterrestrials Tournament": 2022,
    "osu!mania Malaysia Tournament 2": 2022,
    "osu! Philippines Nationals 2022": 2022,
    "Vietnam National Mania Championship 2022": 2022,
    "Middle East 4k osu!mania Tournament": 2022,
    "GB Cup 2023 Autumn": 2023,
    "GB Cup 2024 Spring": 2024,
    "Touhou Project Mania Cup 3rd": 2023,
    "Touhou Project Mania Cup 4th": 2025,
    "Meow Mania": 2024,
    "Speed of Light 3": 2023,
    "Springtime Osumania Free-for-all Tournament 6": 2022,
    "osumania LN Tournament 3": 2022,
    "Jack House Cup 2024": 2024,
    "Jack House Cup 2025": 2025,
    "China LAN 2025": 2025,
    "Gulano Cup #4": 2024,
    "osumania Malaysia Tournament 3": 2023,
    "osumania Malaysia Tournament 4": 2024,
    "Korean Extraterrestrials Tournament 2": 2025,
    "Mania Key Clash Cup 2024": 2024,
    "GB Cup 2025 Spring": 2025,
    "Gulano Cup #5": 2025,
    "Mania Collegiate League Summer 2022": 2022,
    "Solo Score Rush": 2025,
    "The Broken Matrix": 2022,
    "Asia Suiji Cup Rhythmus Aquarum": 2024,
    "Vietnamese National Mania Championship 2024": 2024,
    "4-Digit 4K South Korean Summer Tournament": 2024,
    "4K Korean Mania Tournament 2": 2024,
    "4K Korean Mania Tournament": 2023,
    "Anti-Meta-Madness": 2023,
    "Anti-Meta-Madness 2 Summer Showdown": 2025,
    "International Rhythm League Mania 2023": 2023,
    "Japanese Mania Championship 2 まだ見ぬ新星を探して": 2024,
    "Mania Collegiate League Spring 2023": 2023,
    "Mania Collegiate League Spring 2024": 2024,
    "Vietnamese Rewind Mania Championship": 2024,
    "osu! Philippines Nationals 2024": 2024,
    "osu!mania 4K Pid Term Thailand Tournament": 2024,
    "osu!mania LN Tournament 4": 2025,
    "Vietnamese National Mania Championship 4K 2025": 2025,
    "Soundwave Mania 2": 2025,
    "Middle East Mania 4k Tournament 2": 2023,
    "Vietnam National Mania Championship 2023": 2023,
    "osumania 4K World Cup 2022": 2022,
    "osumania 4K World Cup 2023": 2023,
    "osumania 4K World Cup 2024": 2024,
    "osumania 4K World Cup 2025": 2025,
    "4 Digit osumania World Cup 4": 2022,
    "4 Digit osumania World Cup 2024": 2024,
}

TOURNAMENT_INFO = {
    name: {"tier": tier, "year": TOURNAMENT_YEAR.get(name)}
    for name, tier in TOURNAMENT_TIERS.items()
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
