# utils/winning_chance.py
import numpy as np
import pandas as pd

def process_winning_chance(
    dataset: pd.DataFrame,
    beatmaps: pd.DataFrame,
    bm_block: int = 64,       # beatmaps per block
    u_block: int = 1024,       # users per block (tune to your RAM; 256–1024)
    min_plays_per_user: int = 0,  # set >0 to prune very sparse users
    dtype_acc = np.float32,   # use float32 to cut memory/bandwidth
):
    """
    Compute pairwise winning chance matrix in blocks to avoid allocating (B, U, U).

    Returns: DataFrame (U x U) with values in [0,1], diag=0.5, antisymmetric.
    """

    # ---- Pivot to B x U score matrix (max per beatmap/user) ----
    pivot = dataset.pivot_table(index='beatmap_id', columns='user_id',
                                values='score', aggfunc='max')

    # Optional: prune users with few plays to reduce U
    if min_plays_per_user > 0:
        plays = pivot.notna().sum(axis=0)
        keep_users = plays[plays >= min_plays_per_user].index
        pivot = pivot[keep_users]

    users = pivot.columns.to_numpy()
    S = pivot.to_numpy(dtype=np.float32)   # (B, U)
    P = ~np.isnan(S)                       # played mask (B, U)
    B, U = S.shape

    # ---- Align weights to pivot’s beatmaps ----
    bm = beatmaps.set_index('beatmap_id').reindex(pivot.index)
    rc = bm['RC'].to_numpy(dtype=np.float32)
    ln = bm['LN'].to_numpy(dtype=np.float32)
    denom = rc + ln
    with np.errstate(divide='ignore', invalid='ignore'):
        w_rc_full = np.where(denom > 0, rc / denom, 0.0).astype(np.float32)
        w_ln_full = np.where(denom > 0, ln / denom, 0.0).astype(np.float32)

    # ---- Accumulators (U x U) ----
    num_rc = np.zeros((U, U), dtype=dtype_acc)
    den_rc = np.zeros((U, U), dtype=dtype_acc)
    num_ln = np.zeros((U, U), dtype=dtype_acc)
    den_ln = np.zeros((U, U), dtype=dtype_acc)

    # Pre-convert NaNs to -inf once to simplify comparisons
    Z_full = np.nan_to_num(S, nan=-np.inf)

    # ---- Blocked computation over beatmaps and users (upper triangle only) ----
    for b0 in range(0, B, bm_block):
        b1 = min(b0 + bm_block, B)
        Zb = Z_full[b0:b1]      # (b, U)
        Pb = P[b0:b1]           # (b, U)
        wrc = w_rc_full[b0:b1].reshape(-1, 1, 1)  # (b,1,1)
        wln = w_ln_full[b0:b1].reshape(-1, 1, 1)  # (b,1,1)

        for i0 in range(0, U, u_block):
            i1 = min(i0 + u_block, U)
            A  = Zb[:, i0:i1]     # (b, ui)
            Pa = Pb[:, i0:i1]     # (b, ui)

            # j-block starts at i0 to do upper triangle; we'll mirror later
            for j0 in range(i0, U, u_block):
                j1 = min(j0 + u_block, U)
                Bv = Zb[:, j0:j1]   # (b, uj)
                Pb2 = Pb[:, j0:j1]  # (b, uj)

                # Valid pair (both played)
                V = (Pa[:, :, None] & Pb2[:, None, :])           # (b, ui, uj)

                # Pairwise compare for this block
                greater = (A[:, :, None] >  Bv[:, None, :])
                equal   = (A[:, :, None] == Bv[:, None, :])
                # cast to float and mask invalid pairs
                C = (greater.astype(dtype_acc) + 0.5 * equal.astype(dtype_acc)) * V.astype(dtype_acc)

                # Weighted accumulation
                num_rc[i0:i1, j0:j1] += np.sum(C * wrc, axis=0)   # (ui, uj)
                den_rc[i0:i1, j0:j1] += np.sum(V.astype(dtype_acc) * wrc, axis=0)
                num_ln[i0:i1, j0:j1] += np.sum(C * wln, axis=0)
                den_ln[i0:i1, j0:j1] += np.sum(V.astype(dtype_acc) * wln, axis=0)

    # Mirror lower triangle from upper (excluding diagonal)
    iu, ju = np.triu_indices(U, k=1)
    # Compute means only where denominator > 0
    with np.errstate(invalid='ignore', divide='ignore'):
        m_rc = num_rc / den_rc
        m_ln = num_ln / den_ln
        M = np.nanmean(np.stack([m_rc, m_ln], axis=0), axis=0).astype(np.float32)

    # Diagonal = 0.5
    np.fill_diagonal(M, 0.5)

    # Enforce antisymmetry M[j,i] = 1 - M[i,j] for i<j
    M[(ju, iu)] = 1.0 - M[(iu, ju)]

    # If any entries never had a valid comparison (den=0 for both directions), set to 0.5
    nan_mask = ~np.isfinite(M)
    M[nan_mask] = 0.5

    return pd.DataFrame(M, index=users, columns=users)
