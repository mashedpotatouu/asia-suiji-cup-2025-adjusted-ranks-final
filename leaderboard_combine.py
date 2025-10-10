import pandas as pd

# Load both leaderboard files
rank_adjusted_df = pd.read_csv('leaderboard_rank_adjusted.csv')
tournament_adjusted_df = pd.read_csv('leaderboard_tournament_adjusted.csv')

rank_adjusted_df = rank_adjusted_df.rename(columns={'player_id': 'user_id'})
tournament_adjusted_df = tournament_adjusted_df.rename(columns={'player_id': 'user_id'})

rank_adjusted_df = rank_adjusted_df[['user_id', 'username', 'final_rank']]
tournament_adjusted_df = tournament_adjusted_df[['user_id', 'username', 'final_rank']]

rank_adjusted_df['source'] = 'rank_adjusted'
tournament_adjusted_df['source'] = 'tournament_adjusted'
concat_df = pd.concat([tournament_adjusted_df, rank_adjusted_df], ignore_index=True)

final_df = concat_df.drop_duplicates(subset=['user_id'], keep='first')
final_df_sorted = final_df.sort_values('final_rank')
final_df_sorted = final_df_sorted[['user_id', 'username', 'final_rank']]
final_df_sorted.to_csv('leaderboard_adjusted_what.csv', index=False)
