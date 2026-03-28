from .data_processor import export_osu_to_parquet
from .calc_pp_4k import calculate_pp_4k
from .constants import SCORE_QUERY, BEATMAP_QUERY

def export_data():
    export_osu_to_parquet(SCORE_QUERY, 'dataset/scores.parquet')
    export_osu_to_parquet(BEATMAP_QUERY, 'dataset/beatmaps.parquet')
    calculate_pp_4k().to_parquet('dataset/pp_4k.parquet')

__all__ = ['export_data']
