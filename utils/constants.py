import numpy as np

PP4k_QUERY = """
SELECT user_id, MAX(pp) as pp FROM osu_scores_mania_high WHERE beatmap_id IN (
    SELECT beatmap_id FROM osu_beatmaps WHERE playmode = 3 AND diff_size = 4
) GROUP BY user_id, beatmap_id ORDER BY user_id ASC, pp DESC
"""

SCORE_QUERY = """
SELECT user_id, beatmap_id, MAX(score) as score FROM osu_scores_mania_high WHERE beatmap_id IN (
    SELECT beatmap_id FROM osu_beatmaps WHERE playmode = 3 AND difficultyrating >= 4 AND diff_size = 4 AND diff_overall >= 5
) AND date >= "2020-01-01" AND enabled_mods in (0, 8, 32, 1024, 16384, 1048576, 1073741824) GROUP BY user_id, beatmap_id
"""

BEATMAP_QUERY = """
SELECT beatmap_id, countNormal as RC, countSlider + countSpinner as LN FROM osu_beatmaps WHERE playmode = 3 AND difficultyrating >= 4 AND diff_size = 4 AND diff_overall >= 5
"""

USERS_QUERY = """
select user_id, username from sample_users
"""

elo_constant = np.log(10) / 400
