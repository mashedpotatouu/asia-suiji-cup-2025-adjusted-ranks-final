import pandas as pd

rank_adjusted_df = pd.read_csv('results/leaderboard_rank_adjusted.csv')
tournament_adjusted_df = pd.read_csv('results/leaderboard_tournament_adjusted.csv')

rank_adjusted_df = rank_adjusted_df.rename(columns={'player_id': 'user_id'})
tournament_adjusted_df = tournament_adjusted_df.rename(columns={'player_id': 'user_id'})

rank_adjusted_df = rank_adjusted_df[['user_id', 'username', 'final_rank']]
tournament_adjusted_df = tournament_adjusted_df[['user_id', 'username', 'final_rank']]

rank_adjusted_df['source'] = 'rank_adjusted'
tournament_adjusted_df['source'] = 'tournament_adjusted'
concat_df = pd.concat([tournament_adjusted_df, rank_adjusted_df], ignore_index=True)

final_df = concat_df.drop_duplicates(subset=['user_id'], keep='first')

def adjust_rank_for_tiebreak(df):
    df = df.copy()
    mask = df['source'] == 'rank_adjusted'
    df.loc[mask, 'final_rank'] = df.loc[mask, 'final_rank'] + 0.5
    return df

final_df_tiebreak = adjust_rank_for_tiebreak(concat_df)
final_df_sorted = final_df_tiebreak.sort_values(by=['final_rank'])
final_df_sorted = final_df_sorted[['user_id', 'username', 'final_rank', 'source']]
final_df_sorted.to_csv('results/leaderboard_adjusted.csv', index=False)
