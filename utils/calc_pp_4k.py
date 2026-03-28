import pandas as pd
from .constants import PP4k_QUERY
from .data_processor import read_query

def calculate_pp_4k():
    pp_raw = read_query(PP4k_QUERY).dropna(how='any')
    pp_processed = []
    prev_userid = 0
    total_pp = 0
    multipiler = 1
    for user_id, pp in zip(pp_raw['user_id'], pp_raw['pp']):
        if prev_userid != user_id:
            if prev_userid == 0:
                prev_userid = user_id
            else:
                pp_processed.append({
                    'user_id': prev_userid,
                    'pp': total_pp
                })
                prev_userid = user_id
                total_pp = 0
                multipiler = 1
        total_pp += pp * multipiler
        multipiler *= 0.95
    pp_processed.append({
        'user_id': prev_userid,
        'pp': total_pp
    })
    return pd.DataFrame(pp_processed)

__all__ = ['calculate_pp_4k']
