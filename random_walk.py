import numpy as np
import pandas as pd

# Brownian motion with drift
#
# r(t + dt) = r(t) + μdt + σ√dt·Z, where Z ~ N(0, 1)
#
# μ  : annual drift
# σ  : annual volatility
# dt : time step (1 / steps_per_year)
# Z  : standard normal shock

def simulate_random_walk_paths(
    r0: float = 0.04,
    mu: float = 0.0005,
    sigma: float = 0.01,
    years: int = 10,
    steps_per_year: int = 252,
    n_paths: int = 1000,
    seed: int = 42,
) -> pd.DataFrame:
    """
    Simulate interest rate paths using Brownian motion with drift.

    Returns
    -------
    pd.DataFrame
        Simulated paths indexed by year.
    """

    rng = np.random.default_rng(seed)

    dt = 1 / steps_per_year
    n_steps = years * steps_per_year

    rates = np.empty((n_steps + 1, n_paths))
    rates[0] = r0

    for t in range(1, n_steps + 1):
        Z = rng.normal(size=n_paths)
        rates[t] = rates[t - 1] + mu * dt + sigma * np.sqrt(dt) * Z

    index = pd.Index(
        np.linspace(0, years, n_steps + 1),
        name="year",
    )

    columns = [f"path_{i + 1}" for i in range(n_paths)]

    return pd.DataFrame(rates, index=index, columns=columns)

if __name__ == "__main__":
    paths = simulate_random_walk_paths()
    print(paths.head())
    print(paths.tail())
