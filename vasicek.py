import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


def simulate_vasicek_paths(
    r0: float = 0.04,
    a: float = 0.30,
    b: float = 0.045,
    sigma: float = 0.01,
    years: int = 10,
    steps_per_year: int = 252,
    n_paths: int = 1000,
    seed: int = 42,
) -> pd.DataFrame:
    """
    Simulate interest rate paths using the Vasicek model:
        dr_t = a(b - r_t)dt + sigma dW_t
    """

    rng = np.random.default_rng(seed)

    dt = 1 / steps_per_year
    n_steps = years * steps_per_year

    rates = np.zeros((n_steps + 1, n_paths))
    rates[0, :] = r0

    for t in range(1, n_steps + 1):
        z = rng.standard_normal(n_paths)

        rates[t, :] = (
            rates[t - 1, :]
            + a * (b - rates[t - 1, :]) * dt
            + sigma * np.sqrt(dt) * z
        )

    time_index = np.linspace(0, years, n_steps + 1)

    return pd.DataFrame(
        rates,
        index=time_index,
        columns=[f"path_{i + 1}" for i in range(n_paths)]
    )


paths = simulate_vasicek_paths()

print(paths.head())
print(paths.shape)

plt.figure(figsize=(12, 6))

# Plot only first 100 paths so chart is readable
plt.plot(paths.index, paths.iloc[:, :100], linewidth=0.5, alpha=0.4)

plt.xlabel("Years")
plt.ylabel("Interest Rate")
plt.title("Simulated Vasicek Interest Rate Paths")
plt.show()

mean_path = paths.mean(axis=1)
p5 = paths.quantile(0.05, axis=1)
p50 = paths.quantile(0.50, axis=1)
p95 = paths.quantile(0.95, axis=1)

plt.figure(figsize=(12, 6))

plt.plot(paths.index, mean_path, label="Mean")
plt.plot(paths.index, p5, label="5th percentile")
plt.plot(paths.index, p50, label="Median")
plt.plot(paths.index, p95, label="95th percentile")

plt.xlabel("Years")
plt.ylabel("Interest Rate")
plt.title("Vasicek Scenario Distribution")
plt.legend()
plt.show()

