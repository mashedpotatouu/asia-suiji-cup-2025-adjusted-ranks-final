import os
import re
import pandas as pd
import numpy as np
import requests
from tqdm import tqdm
from dotenv import load_dotenv
ROOT_DIR = "" # Set this to your tournaments root directory
load_dotenv()

IGNORED_USER_IDS = [
    "15806492", "16629204",
]

OSU_API_KEY = os.getenv("OSU_API_KEY")
STAGE_NAMES = [
    'Grand Finals', 'Finals', 'Semifinals', 'Quarterfinals',  "Play-off 1", "Play-off 2", "Playoffs",
    'Round of 16', 'Round of 32',  'Round of 64', 'Qualifiers', "Group Stage"
]
POW = 30

def extract_id(cell, kind="map"):
    if pd.isna(cell):
        return None
    s = str(cell).strip()
    if s.isdigit():
        return s
    try:
        if float(s).is_integer():
            return str(int(float(s)))
    except Exception:
        pass
    if kind == "map":
        m = re.search(r'#mania/(\d+)', s)
        if m:
            return m.group(1)
        m2 = re.search(r'/(\d+)$', s)
        if m2:
            return m2.group(1)
    elif kind == "match":
        m = re.search(r'/matches/(\d+)', s)
        if m:
            return m.group(1)
    return None

def load_match_links(stage, TOURNEY_DIR):
    path = os.path.join(TOURNEY_DIR, f"{stage}_matches.csv")
    if not os.path.exists(path):
        return []
    df = pd.read_csv(path)
    links = df.iloc[:,0].dropna().tolist()
    match_ids = []
    for cell in links:
        mid = extract_id(cell, kind="match")
        if mid:
            match_ids.append(mid)
    return match_ids

def get_match_scores(match_id):
    url = f"https://osu.ppy.sh/api/get_match?k={OSU_API_KEY}&mp={match_id}"
    try:
        resp = requests.get(url, timeout=20)
        data = resp.json()
        if not isinstance(data, dict):
            print(f"Non-dict response for match {match_id}: {data}")
            return []
        if "games" not in data:
            print(f"No 'games' in match {match_id} response: {data}")
            return []
        scores = []
        for g in data["games"]:
            map_id = g.get("beatmap_id", None)
            game_scores = g.get("scores", [])
            if not game_scores:
                print(f"Game {g.get('game_id')} in match {match_id} has no scores.")
            for s in game_scores:
                scores.append({
                    "user_id": s["user_id"],
                    "map_id": map_id,
                    "score": int(s["score"]),
                    "match_id": match_id
                })
        return scores
    except Exception as e:
        print(f"Failed to fetch match {match_id}: {e}")
    return []

def get_username(user_id, username_cache):
    if user_id in username_cache:
        return username_cache[user_id]
    url = f"https://osu.ppy.sh/api/get_user?k={OSU_API_KEY}&u={user_id}"
    try:
        resp = requests.get(url, timeout=10)
        data = resp.json()
        if isinstance(data, list) and data and "username" in data[0]:
            username = data[0]["username"]
        else:
            username = "Banned or Unavailable"
    except Exception as e:
        print(f"Failed to fetch username for {user_id}: {e}")
        username = "Banned or Unavailable"
    username_cache[user_id] = username
    return username

def is_tournament_processed(TOURNEY_DIR):
    for stage in STAGE_NAMES:
        leaderboard_path = os.path.join(TOURNEY_DIR, f"{stage}_leaderboard.csv")
        if os.path.exists(leaderboard_path):
            return True
    return False

def process_tournament(TOURNEY_DIR):
    username_cache = {}
    print(f"\n\n========== Processing {TOURNEY_DIR} ==========")
    for stage in STAGE_NAMES:
        match_ids = load_match_links(stage, TOURNEY_DIR)
        if not match_ids:
            continue

        all_scores = []
        for match_id in tqdm(match_ids):
            scores = get_match_scores(match_id)
            all_scores.extend(scores)

        if not all_scores:
            continue

        scores_df = pd.DataFrame(all_scores)
        scores_df = scores_df[scores_df["score"] >= 500000]
        scores_df = scores_df[~scores_df["user_id"].astype(str).isin([str(uid) for uid in IGNORED_USER_IDS])]
        if scores_df.empty:
            continue

        mappool_path = os.path.join(TOURNEY_DIR, f"{stage}_maps.csv")
        if not os.path.exists(mappool_path):
            continue
        mappool_df = pd.read_csv(mappool_path)

        mappool_ids = set()
        for cell in mappool_df.iloc[:,0].dropna():
            mapid = extract_id(cell, kind="map")
            if mapid:
                mappool_ids.add(mapid)

        if not mappool_ids:
            print(f"No beatmap IDs could be extracted from {stage}_maps.csv, skipping stage.")
            continue

        scores_df = scores_df[scores_df["map_id"].astype(str).isin(mappool_ids)]

        scores_df_path = os.path.join(TOURNEY_DIR, f"{stage}_scores.csv")
        scores_df.to_csv(scores_df_path, index=False)

        if scores_df.empty:
            continue

        medians = scores_df.groupby("map_id")["score"].median()
        player_pscores = {}
        player_maps_played = {}
        player_total_possible_maps = {}

        for player in scores_df["user_id"].unique():
            player_df = scores_df[scores_df["user_id"] == player]
            n_maps_played = len(player_df)
            matches_played = player_df["match_id"].unique()
            maps_in_matches = scores_df[scores_df["match_id"].isin(matches_played)][["match_id", "map_id"]].drop_duplicates()["map_id"]
            n_possible_map_plays = len(maps_in_matches)
            player_maps_played[player] = n_maps_played
            player_total_possible_maps[player] = n_possible_map_plays

            ratio_terms = []
            for _, row in player_df.iterrows():
                s = row["score"]
                m = medians[row["map_id"]]
                ratio = (s / m) ** POW if m > 0 else 0
                ratio_terms.append(ratio)
            if not ratio_terms:
                continue
            part1 = np.mean(ratio_terms)

            N_js = []
            for match_id in matches_played:
                match_df = scores_df[scores_df["match_id"] == match_id]
                plays_per_player = match_df.groupby("user_id")["map_id"].count()
                mean_plays = plays_per_player.mean()
                N_js.append(mean_plays)
            if N_js:
                normalization = (n_maps_played / sum(N_js)) ** (1/3)
            else:
                normalization = 1

            pscore = part1 * normalization
            player_pscores[player] = pscore

        out_list = []
        for pid, score in player_pscores.items():
            name = get_username(pid, username_cache)
            maps_played = f"{player_maps_played[pid]}/{player_total_possible_maps[pid]}"
            out_list.append({
                "Player ID": pid,
                "Player Name": name,
                "pScore": score,
                "Maps Played": maps_played
            })
        out_df = pd.DataFrame(out_list)
        out_df = out_df.sort_values("pScore", ascending=False)
        out_path = os.path.join(TOURNEY_DIR, f"{stage}_leaderboard.csv")
        out_df.to_csv(out_path, index=False)
        print(f"Leaderboard saved to {out_path}")

if __name__ == "__main__":
    for folder in os.listdir(ROOT_DIR):
        path = os.path.join(ROOT_DIR, folder)
        if not os.path.isdir(path):
            continue
        if folder == "manual_work":
            continue
        if is_tournament_processed(path):
            print(f"Skipping {folder} as it has already been processed.")
            continue
        process_tournament(path)
        print(f"Finished processing {folder}")
    print("All tournaments processed.")
