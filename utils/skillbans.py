import pandas as pd
import numpy as np

from dataclasses import dataclass
from scipy.stats import norm

from .elo import elo

@dataclass
class SkillbansResult:
    threshold: float
    skillbanned: pd.DataFrame

def winning_chances_to_elo(winning_chances):
    players = winning_chances.index
    indices = range(len(players))
    winning_chances.index = indices
    winning_chances.columns = indices
    data = pd.melt(winning_chances, ignore_index=False).dropna(how='any').reset_index().values
    data = data[data[:, 0] < data[:, 1]]
    x0 = np.random.normal(0, 0.01, len(winning_chances))
    x = elo(data, x0)
    df = pd.DataFrame(x, index=players)
    return df.reset_index().rename({0: 'elo'})

def get_skillbans_threshold(elo_rank, target_rank, z):
    elo_samples = elo_rank[elo_rank['rank'] >= target_rank]['elo']
    mean = elo_samples.mean()
    std = elo_samples.std()
    return mean + std * z

def skillbans(elo, actual_rank, target_rank=1000, top_rank=500, top_elo_threshold=0.025):
    z = norm.ppf(1-top_elo_threshold)
    elo_rank = actual_rank.merge(elo).sort_values(by='pp', ascending=False)
    elo_rank['rank'] = range(1, elo_rank.shape[0] + 1)
    threshold = get_skillbans_threshold(elo_rank, target_rank, z)
    return SkillbansResult(
        threshold=threshold,
        skillbanned=elo_rank[(elo_rank['elo'] > threshold) & (elo_rank['rank'] >= top_rank)]
    )

__all__ = ['skillbans']
