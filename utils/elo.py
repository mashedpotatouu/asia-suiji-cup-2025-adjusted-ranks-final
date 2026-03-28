import numpy as np
import time
from .constants import elo_constant

def grad(xi, xj, pij):
    p_hat = 1.0 / (1.0 + np.exp((xj - xi) * elo_constant))
    return pij - p_hat

def elo(data, x0, gamma=0.9995, eps=1e-2, max_epochs=100, debug=True):
    n = len(x0)
    x = x0.astype('float64').copy()
    n_games = np.zeros(n, dtype=np.int64)
    mult = np.ones(n, dtype='float64')

    start_time = time.time()
    total_iters = 0

    for epoch in range(max_epochs):
        np.random.shuffle(data)
        delta_sum = 0.0

        for k, (i, j, pij) in enumerate(data, 1):  # k = match counter
            i = int(i); j = int(j)
            df = grad(x[i], x[j], pij)
            x[i] += df * mult[i]
            x[j] -= df * mult[j]

            n_games[i] += 1; n_games[j] += 1
            mult[i] *= gamma; mult[j] *= gamma
            delta_sum += abs(df)

            total_iters += 1

            # Debug every 10000000 updates (tune this number as needed)
            if debug and total_iters % 10000000 == 0:
                elapsed = time.time() - start_time
                ips = total_iters / elapsed
                avg_df = delta_sum / k
                print(f"[DEBUG] Epoch {epoch+1}/{max_epochs}, "
                      f"Iter {total_iters}, "
                      f"AvgΔ {avg_df:.4e}, "
                      f"{ips:.1f} it/s, "
                      f"Elapsed {elapsed:.1f}s")

        if delta_sum / len(data) < eps:
            if debug:
                print(f"[DEBUG] Early stop at epoch {epoch+1}, "
                      f"avg update {delta_sum/len(data):.4e}")
            break

    return x
